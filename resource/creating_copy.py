from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
import boto3
from mysql_connection import get_connection
from config import Config

# 내가쓴 레시피 수정 및 삭제
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
                                    Config.S3_BUCKET,
                                    file.filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType':file.content_type} )                 

            except Exception as e :
                return {'error' : str(e)}, 500

            # 데이터 베이스에 업데이트 해준다.
            imgUrl = Config.S3_LOCATION + new_file_name
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

# 마스터계정의 모든 레시피 수정 및 삭제
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
                                        Config.S3_BUCKET,
                                        file.filename,
                                        ExtraArgs = {'ACL':'public-read', 'ContentType':file.content_type} )                 

                except Exception as e :
                    return {'error' : str(e)}, 500

                # 데이터 베이스에 업데이트 해준다.
                imgUrl = Config.S3_LOCATION + new_file_name
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



#내가 쓴 레시피 수정중 부재료 수정
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


