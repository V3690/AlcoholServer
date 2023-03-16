from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
import boto3
from mysql_connection import get_connection
from config import Config


## 레시피 작성 페이지 ##


# 레시피 작성 - 기본 등록
class CreatingRecipe(Resource):
    @jwt_required()
    def post(self) :

        # 사진과 내용을 올리면 db에 저장
        # 1. 클라이언트로부터 데이터 받아온다.
        # form-data
        # title : text
        # engTitle : text
        # intro : text
        # percent : text
        # content : text
        # img : file

        user_id = get_jwt_identity()

        # userId, title, engTitle, intro, percent, imgUrl, content
        
        title = request.form['title']
        engTitle = request.form['engTitle']
        intro = request.form['intro']
        percent = request.form['percent']
        content = request.form['content']
        file = request.files['img']

        # 필수 항목 체크
        if (title == "") or (percent == "") or (content == "")  :
            return {'error' : '<한글 이름, 도수, 레시피, 사진은 필수입니다.'}, 400
        elif file.filename == "":
            return {'error' : '<한글 이름, 도수, 레시피, 사진은 필수입니다.'}, 400

        print(file.content_type)
        
        # 사진만 업로드 가능하도록 하는 코드
        if 'image' not in file.content_type :
            return {'error' : 'image 파일만 업로드 가능합니다.'}, 400

        # 2. 사진을 먼저 S3에 저장한다.
        # 파일명을 유니크하게 만드는 방법
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':', '_') + '.' + file.content_type.split('/')[-1]
        
        # 파일명을, 유니크한 이름으로 변경한다.
        # 클라이언트에서 보낸 파일명을 대체!
        
        file.filename = new_file_name

        # S3 에 파일을 업로드 하면 된다.
        # S3 에 파일 업로드 하는 라이브러리가 필요
        # 따라서, boto3 라이브러리를 이용해서
        # 업로드 한다.

        client = boto3.client('s3', 
                    aws_access_key_id = Config.ACCESS_KEY ,
                    aws_secret_access_key = Config.SECRET_ACCESS )
        
        try :
            
            client.upload_fileobj(file,
                                    Config.BUCKET_NAME,
                                    'recipe/'+ file.filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )

        except Exception as e:
            return {'error' : str(e)}, 500

        # 3. 저장된 사진의 imgUrl 을 만든다.        
        imgUrl = Config.S3_LOCATION + 'recipe/'+ file.filename

        # 4. recipe DB에 저장
        try :
            connection = get_connection()

            query = '''insert into recipe(userId, title, engTitle, intro, percent, imgUrl, content)
                    values
                    (%s, %s, %s, %s, %s, %s, %s);'''

            record = (user_id, title, engTitle, intro, percent, imgUrl, content)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500

        # 5. recipe DB에 저장한 id 불러오기
        try :
            connection = get_connection()

            query = '''select id from recipe
                    where title like %s;'''

            record = (title, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)

            result_id = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500

        return {'result' : 'success',
                'recipe_id' : result_id}, 200

# 레시피 작성 - 술/재료 등록
class CreatingRecipeIngredient(Resource):
    @jwt_required()
    def post(self) :

        data = request.get_json()

        # {
        #     "recipeId": 3,
        #     "alcolholId": "1,2,3,4,5,6"
        #     "ingredientId": "1,2,3,4,5,6"
        # }

        recipe = int(data['recipeId'])
        alcolhols = data['alcoholId'].split(',')
        ingredients = data['ingredientId'].split(',')

        try :
            connection = get_connection()
            cursor = connection.cursor()

        # recipe_alcohol 테이블에 저장
            for alcohol in alcolhols:
                cursor.execute(
                    "INSERT INTO recipeAlcohol (recipeId, alcoholId) VALUES (%s, %s)",
                    (recipe, alcohol)
                )

        # recipe_ingredient 테이블에 저장
            for ingredient in ingredients:
                cursor.execute(
                    "INSERT INTO recipeIngredient (recipeId, ingredientId) VALUES (%s, %s)",
                    (recipe, ingredient)
                )

            connection.commit()
            return {"result": "success"}, 200

        # 오류가 발생한 경우 데이터베이스 트랜잭션에 롤백을 추가
        except Error as e :
            print(e)
            connection.rollback() 
            return {"result": "fail", "error": str(e)}, 500

        # 오류 발생 여부에 관계없이 데이터베이스 커서 및 연결을 닫는 블록
        finally:
            cursor.close()
            connection.close()



# 레시피 작성 중 - 술재료 목록
class CreatingAlcoholList(Resource):
    @jwt_required()
    def get(self):
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        try :
            connection = get_connection()

            query = '''select id, name from alcohol
                        limit ''' + offset + ''', '''+ limit + ''';
                    '''
            
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,)

            result_list = cursor.fetchall()

            cursor.close()
            connection.close()
    
        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        # print(result_list)

        return {"result" : "success" ,
                "items" : result_list , 
                "count" : len(result_list)}, 200

# 레시피 작성 중 - 부재료 목록
class CreatingIngredientList(Resource):
    @jwt_required()
    def get(self):
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        try :
            connection = get_connection()

            query = '''select id, name from ingredient
                        limit ''' + offset + ''', '''+ limit + ''';
                    '''
            
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,)

            result_list = cursor.fetchall()

            cursor.close()
            connection.close()
    
        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        # print(result_list)

        return {"result" : "success" ,
                "items" : result_list , 
                "count" : len(result_list)}, 200



# 레시피 작성 중 - 술재료 검색
class CreatingSearchAlcohol(Resource):
    @jwt_required()
    def get(self):
    
        keyword = request.args.get('keyword')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """select id, name
                    from alcohol
                    where name like '%""" + keyword + """%'
                    limit """ + offset + """, """+ limit + """;
                    """
            cursor.execute(query)
            result = cursor.fetchall()
            return {"result": result, "count" : len(result)}, 200
        
        except Exception as e:
            print(e)
            return ("errer" + str(e)), 500
        
        finally:
            conn.close()
            cursor.close()

# 레시피 작성 중 - 부재료 검색
class CreatingSearchIngredient(Resource):
    @jwt_required()
    def get(self):
    
        keyword = request.args.get('keyword')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """select id, name
                    from ingredient
                    where name like '%""" + keyword + """%'
                    limit """ + offset + """, """+ limit + """;
                    """
            cursor.execute(query)
            result = cursor.fetchall()
            return {"result": result, "count" : len(result)}, 200
        
        except Exception as e:
            print(e)
            return ("errer" + str(e)), 500
        
        finally:
            conn.close()
            cursor.close()



# 선택한 술/재료 불러오기 (화면에 나타내기) -- 개발 필요
#
#
#
#



# 본인 레시피 수정, 삭제
class CreatingRecipeEdit(Resource):
    @jwt_required()
    def put(self, recipe_id) :

        # photo(file), content(text)
        
        # 유저 토큰으로부터 user_id 반환
        user_id = get_jwt_identity()

        if 'image' not in request.files:
            # 쿼리 부분을 만든다.
            title = request.form['title']
            engTitle = request.form['engTitle']
            intro = request.form['intro']
            percent = request.form['percent']
            content = request.form['content']

            # S3에 파일 업로드가 필요 없으므로, 디비에 저장한다.
            try :
                # DB에 연결
                connection = get_connection()

                # 쿼리문 만들기
                query = f'''update recipe set 
                        title = %s,
                        engTitle = %s,
                        intro = %s,
                        percent = %s,
                        imgUrl = null,
                        content = %s
                        where userId = {user_id} and id = {recipe_id};'''

                record = (title, engTitle, intro, percent, content)

                # 커서를 가져온다.
                cursor = connection.cursor()

                # 쿼리문을 커서를 이용해서 실행한다.
                cursor.execute(query, record)

                # 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                connection.commit()

                # 자원 해제
                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 500

            try :
                connection = get_connection()

                query = '''select id from recipe
                        where title like %s;'''

                record = (title, )
                cursor = connection.cursor(dictionary= True)
                cursor.execute(query, record)

                result_id = cursor.fetchall()

                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 500

            return {'result' : 'success',
                    'recipe_id' : result_id}, 200

        else :
            # 쿼리 부분을 만든다.
            title = request.form['title']
            engTitle = request.form['engTitle']
            intro = request.form['intro']
            percent = request.form['percent']
            content = request.form['content']
            file = request.files['img']
            # 파일이 있으니까, 파일명을 새로 만들어서
            # S3 에 업로드한다.

            # 2. S3 에 파일 업로드
            # 파일명을 우리가 변경해 준다.
            # 파일명은, 유니크하게 만들어야 한다.
            current_time = datetime.now()
            new_file_name = current_time.isoformat().replace(':', '_') + '.jpg'

            # 유저가 올린 파일의 이름을, 내가 만든 파일명으로 변경
            file.filename = new_file_name

            # S3 에 업로드 하면 된다.
            # AWS 의 라이브러리를 사용해야 한다.
            # 이 파이썬 라이브러리가 boto3 라이브러리다!
            # boto3 라이브러리 설치
            # pip install boto3 

            s3 = boto3.client('s3', 
                        aws_access_key_id = Config.ACCESS_KEY,
                        aws_secret_access_key = Config.SECRET_ACCESS)

            try :
                s3.upload_fileobj(file,
                                    Config.BUCKET_NAME,
                                    'recipe/' + file.filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType':file.content_type} )                 

            except Exception as e :
                return {'error' : str(e)}, 500

            # 데이터 베이스에 업데이트 해준다.
            imgUrl = Config.S3_LOCATION + 'recipe/' + file.filename
            try :
                # DB에 연결
                connection = get_connection()

                # 쿼리문 만들기
                query = f'''update recipe set 
                title = %s,
                engTitle = %s,
                intro = %s,
                percent = %s,
                imgUrl = %s,
                content = %s
                where userId = {user_id} and id = {recipe_id};'''

                record = (title, engTitle, intro, percent, imgUrl, content)

                # 커서를 가져온다.
                cursor = connection.cursor()

                # 쿼리문을 커서를 이용해서 실행한다.
                cursor.execute(query, record)

                # 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                connection.commit()

                # 자원 해제
                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 500

            # 5. recipe DB에 저장한 id 불러오기
            try :
                connection = get_connection()

                query = '''select id from recipe
                        where title like %s;'''

                record = (title, )
                cursor = connection.cursor(dictionary= True)
                cursor.execute(query, record)

                result_id = cursor.fetchall()

                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 500

            return {'result' : 'success',
                    'recipe_id' : result_id}, 200

    @jwt_required()   
    def delete(self,recipe_id):
        user_id = get_jwt_identity()
        try :
            connection = get_connection()
            query = f'''delete from r,ra,ri
                        using recipe r
                        left join recipeAlcohol ra
                        on r.id = ra.recipeId
                        left join recipeIngredient ri
                        on r.id = ri.recipeId
                    where r.id = %s and r.userId = {user_id};'''
            record = (recipe_id,)
            cursor = connection.cursor()
            cursor.execute(query, record)
            connection.commit()
            cursor.close()
            connection.close()
        
        except Error as e:
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)} , 500


        return {'result' : 'success'}, 200

# 본인 레시피 재료 수정
class CreatingRecipeIngredientEdit(Resource):
    def put(self, recipe_id):
        data = request.get_json()

        # {
        #     "recipeId": 3,
        #     "alcolholId": "1,2,3,4,5,6"
        #     "ingredientId": "1,2,3,4,5,6"
        # }

        recipe = int(data['recipeId'])
        alcohols = data['alcoholId'].split(',')
        ingredients = data['ingredientId'].split(',')

        try:
            connection = get_connection()
            cursor = connection.cursor()


            cursor.execute(
                f'''delete from recipeAlcohol 
                where recipeId = {recipe_id}'''
            )

            cursor.execute(
                f'''delete from recipeIngredient 
                where recipeId ={recipe_id}'''
            )

  
            for alcohol in alcohols:
                cursor.execute(
                '''insert into recipeAlcohol (recipeId, alcoholId) values (%s, %s)''',
                    (recipe, alcohol)
                )

            for ingredient in ingredients:
                cursor.execute(
                '''insert into recipeIngredient (recipeId, ingredientId) values (%s, %s)''',
                    (recipe, ingredient)
                )

            connection.commit()
            return {"result": "success"}, 200

        except Error as e:
            print(e)
            return {"result": "fail", "error": str(e)}, 500

        finally:
            cursor.close()
            connection.close()

# 전체 레시피 수정, 삭제 (관리자 전용)
class CreatingRecipeEditMaster(Resource):
    @jwt_required()
    def put(self, recipe_id) :


        # photo(file), content(text)
        
        # 유저 토큰으로부터 user_id 반환
        user_id = get_jwt_identity()
        if (user_id != 1):
            return {'result' : '당신은 관리자가 아닙니다',}, 200
        else:
            if 'image' not in request.files:
                # 쿼리 부분을 만든다.
                title = request.form['title']
                engTitle = request.form['engTitle']
                intro = request.form['intro']
                percent = request.form['percent']
                content = request.form['content']

                # S3에 파일 업로드가 필요 없으므로, 디비에 저장한다.
                try :
                    # DB에 연결
                    connection = get_connection()

                    # 쿼리문 만들기
                    query = f'''update recipe set 
                            title = %s,
                            engTitle = %s,
                            intro = %s,
                            percent = %s,
                            imgUrl = null,
                            content = %s
                            where id = {recipe_id};'''

                    record = (title, engTitle, intro, percent, content)

                    # 커서를 가져온다.
                    cursor = connection.cursor()

                    # 쿼리문을 커서를 이용해서 실행한다.
                    cursor.execute(query, record)

                    # 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                    connection.commit()

                    # 자원 해제
                    cursor.close()
                    connection.close()

                except Error as e :
                    print(e)
                    cursor.close()
                    connection.close()
                    return {'error' : str(e)}, 500

                try :
                    connection = get_connection()

                    query = '''select id from recipe
                            where title like %s;'''

                    record = (title, )
                    cursor = connection.cursor(dictionary= True)
                    cursor.execute(query, record)

                    result_id = cursor.fetchall()

                    cursor.close()
                    connection.close()

                except Error as e :
                    print(e)
                    cursor.close()
                    connection.close()
                    return {'error' : str(e)}, 500

                return {'result' : 'success',
                        'recipe_id' : result_id}, 200

            else :
                # 쿼리 부분을 만든다.
                title = request.form['title']
                engTitle = request.form['engTitle']
                intro = request.form['intro']
                percent = request.form['percent']
                content = request.form['content']
                file = request.files['img']
                # 파일이 있으니까, 파일명을 새로 만들어서
                # S3 에 업로드한다.

                # 2. S3 에 파일 업로드
                # 파일명을 우리가 변경해 준다.
                # 파일명은, 유니크하게 만들어야 한다.
                current_time = datetime.now()
                new_file_name = current_time.isoformat().replace(':', '_') + '.jpg'

                # 유저가 올린 파일의 이름을, 내가 만든 파일명으로 변경
                file.filename = new_file_name

                # S3 에 업로드 하면 된다.
                # AWS 의 라이브러리를 사용해야 한다.
                # 이 파이썬 라이브러리가 boto3 라이브러리다!
                # boto3 라이브러리 설치
                # pip install boto3 

                s3 = boto3.client('s3', 
                            aws_access_key_id = Config.ACCESS_KEY,
                            aws_secret_access_key = Config.SECRET_ACCESS)

                try :
                    s3.upload_fileobj(file,
                                        Config.BUCKET_NAME,
                                        'recipe/' + file.filename,
                                        ExtraArgs = {'ACL':'public-read', 'ContentType':file.content_type} )                 

                except Exception as e :
                    return {'error' : str(e)}, 500

                # 데이터 베이스에 업데이트 해준다.
                imgUrl = Config.S3_LOCATION + 'recipe/' + file.filename
                try :
                    # DB에 연결
                    connection = get_connection()

                    # 쿼리문 만들기
                    query = f'''update recipe set 
                    title = %s,
                    engTitle = %s,
                    intro = %s,
                    percent = %s,
                    imgUrl = %s,
                    content = %s
                    where id = {recipe_id};'''

                    record = (title, engTitle, intro, percent, imgUrl, content)

                    # 커서를 가져온다.
                    cursor = connection.cursor()

                    # 쿼리문을 커서를 이용해서 실행한다.
                    cursor.execute(query, record)

                    # 커넥션을 커밋해줘야 한다 => 디비에 영구적으로 반영하라는 뜻
                    connection.commit()

                    # 자원 해제
                    cursor.close()
                    connection.close()

                except Error as e :
                    print(e)
                    cursor.close()
                    connection.close()
                    return {'error' : str(e)}, 500

                # 5. recipe DB에 저장한 id 불러오기
                try :
                    connection = get_connection()

                    query = '''select id from recipe
                            where title like %s;'''

                    record = (title, )
                    cursor = connection.cursor(dictionary= True)
                    cursor.execute(query, record)

                    result_id = cursor.fetchall()

                    cursor.close()
                    connection.close()

                except Error as e :
                    print(e)
                    cursor.close()
                    connection.close()
                    return {'error' : str(e)}, 500

                return {'result' : 'success',
                        'recipe_id' : result_id}, 200

    @jwt_required()   
    def delete(self,recipe_id):
        user_id = get_jwt_identity()
        if (user_id != 1):
            return {'result' : '당신은 관리자가 아닙니다',}, 200
        else:
            try :
                connection = get_connection()
                query = f'''delete from r,ra,ri
                            using recipe r
                            left join recipeAlcohol ra
                            on r.id = ra.recipeId
                            left join recipeIngredient ri
                            on r.id = ri.recipeId
                            where r.id = %s ;'''
                record = (recipe_id,)
                cursor = connection.cursor()
                cursor.execute(query, record)
                connection.commit()
                cursor.close()
                connection.close()
            
            except Error as e:
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)} , 500


            return {'result' : 'success'}, 200









