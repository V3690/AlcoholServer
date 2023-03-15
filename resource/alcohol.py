from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
import boto3
from mysql_connection import get_connection
from config import Config


## 술도감 페이지 ##


# 술 도감 (전체 목록)
class AlcoholListResource(Resource):
    @jwt_required()
    def get(self) :
        # user_id = get_jwt_identity()

        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()

            query = '''select a.id, a.name, a.percent, a.alcoholType, a.category, a.produce, a.supply, a.imgUrl, count(l.alcoholId) as cnt
                    from alcohol a
                    left join likeAlcohol l
                    on a.id = l.alcoholId
                    group by a.id
                    order by ''' + order + '''  desc, name asc
                    limit ''' + offset + ''', '''+ limit + ''';'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, )


            result_list = cursor.fetchall()

            # i = 0
            # for row in result_list :
            #     result_list[i]['avg'] = float(row['avg'])
            #     i = i + 1

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

# 술 도감 (1개 세부 정보)
class AlcoholResource(Resource):
    @jwt_required()
    def get(self, alcohol_id) :
        try :

            connection = get_connection()
            query = '''select id, name, percent, alcoholType, category, produce, supply, imgUrl
                    from alcohol
                    where id = %s;'''
                                
            record = (alcohol_id, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

            if result_list[0]['id'] is None :
                return{'error' : '잘못된 알콜 아이디 입니다.'}, 400

            # i = 0
            # for row in result_list :
            #     result_list[i]['createdAt'] = row['createdAt'].isoformat()
            #     result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
            #     i = i + 1

            cursor.close()
            connection.close()


        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        
        return { "result" : "success" ,
                "alcohol" : result_list[0] }, 200
    

# 유저의 요청(데이터 수정/추가)
class AlcoholRequestResource(Resource):
    @jwt_required()
    def post(self) :

        # 사진과 내용을 올리면 db에 저장
        # 1. 클라이언트로부터 데이터 받아온다.
        # form-data
        # photo : file
        # requestTypee : text
        # name : text
        # content : text
        # percent : text
        user_id = get_jwt_identity()

        # userId, requestType, name, content,percent, imgUrl   
        
        # 사진과 내용은 필수 항목 !
        if 'name' not in request.form or 'requestType' not in request.form :
            return {'error' : '데이터를 정확히 보내세요.'}, 400

        requestType = request.form['requestType']
        name = request.form['name']
        content = request.form['content']
        percent = request.form['percent']
        file = request.files['photo']


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
                                    new_file_name,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )

        except Exception as e:
            return {'error' : str(e)}, 500

        # 3. 저장된 사진의 imgUrl 을 만든다.        
        imgUrl = Config.S3_LOCATION + new_file_name

        # 4. DB에 저장한다.
        try :
            connection = get_connection()

            query = '''insert into request(userId, requestType, name, content,percent, imgUrl)
                    values
                    (%s, %s, %s, %s, %s, %s); '''

            record = (user_id, requestType,name,content,percent, imgUrl)
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

        return {'result' : 'success'}, 200
    


# 관리자용 술도감 추가 api [관리자용 페이지에서 추가버튼을 눌렀을시 실행되는 api]
class AlcoholAddResource(Resource):

    @jwt_required()
    def post(self) :
        # 관리자만 추가 가능
        user_id = get_jwt_identity()
        if user_id != 1 :
            return {'error' : '관리자만 추가 가능합니다.'}, 400
        
        # 사진과 내용은 필수 항목 !
        if 'name' not in request.form or 'photo' not in request.files :
            return {'error' : '데이터를 정확히 보내세요.'}, 400
        # 폼데이터로 받는다
        name = request.form['name']
        percent = request.form['percent']
        alcoholType = request.form['alcoholType']
        category = request.form['category']
        produce = request.form['produce']
        supply = request.form['supply']
        file = request.files['photo']
        
        if 'image' not in file.content_type :
            return {'error' : 'image 파일만 업로드 가능합니다.'}, 400
        
        # 2. 사진을 먼저 S3에 저장한다.
        # 파일명을 유니크하게 만드는 방법
        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':', '_') + '.' + file.content_type.split('/')[-1]

        # 파일명을, 유니크한 이름으로 변경한다.
        # 클라이언트에서 보낸 파일명을 대체!
        file.filename = new_file_name

        client = boto3.client('s3', 
                    aws_access_key_id = Config.ACCESS_KEY ,
                    aws_secret_access_key = Config.SECRET_ACCESS )
        
        try:
            
            client.upload_fileobj(file,
                                    Config.BUCKET_NAME,
                                    file.filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )
            
        except Exception as e:
            return {'error' : str(e)}, 500
        
        # 3. 저장된 사진의 imgUrl 을 만든다.        
        imgUrl = Config.S3_LOCATION + file.filename
        
        # 추가할 술도감의 정보를 DB에 추가한다.
        try :
            connection = get_connection()

            query = '''insert into alcohol (name, percent, alcoholType, category, produce, supply, imgUrl)
                    values (%s, %s, %s, %s, %s, %s, %s);'''

            record = (name, percent, alcoholType, category, produce, supply, imgUrl)
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
        
        return {'result' : 'success'}, 200
    
# 관리자용 술도감 수정 api [관리자용 페이지에서 수정완료 버튼을 눌렀을시 실행되는 api]
class AlcoholUpdateResource(Resource):
    @jwt_required()
    def put(self, alcohol_id) :
        # 관리자만 수정 가능
        user_id = get_jwt_identity()
        if user_id != 1 :
            return {'error' : '관리자만 추가 가능합니다.'}, 400
        # print(request.form, request.files)
        # ImmutableMultiDict([('name', '머야'), ('percent', '40'), ('alcoholType', '대체함'), ('category', '칵테일'), ('produce', '마니 '), ('supply', '마니공급 ')])
        # ImmutableMultiDict([('photo', <FileStorage: '고양이를주웠다.png' ('image/png')>)])
        
        # 사진과 내용은 필수 항목 !
        if 'name' not in request.form or 'photo' not in request.files or "imgUrl" not in request.form:
            return {'error' : '데이터를 정확히 보내세요.'}, 400
        
        # 폼데이터로 받는다
        name = request.form['name']
        percent = request.form['percent']
        alcoholType = request.form['alcoholType']
        category = request.form['category']
        produce = request.form['produce']
        supply = request.form['supply']
        file = request.files['photo']
        # 기존에 있던 imgUrl도 받아야 한다. 
        # S3에 기존에 있던 파일을 대체해야하기 때문에
        # 클라이언트에서 imgUrl.split("com/")[1] 작업을 한뒤 보낸것을 받는다. (이것은 이름만 사용하는것)
        imgUrl = request.form['imgUrl']
      
        if 'image' not in file.content_type :
            return {'error' : 'image 파일만 업로드 가능합니다.'}, 400

        client = boto3.client('s3', 
                    aws_access_key_id = Config.ACCESS_KEY ,
                    aws_secret_access_key = Config.SECRET_ACCESS )
        
        try:
            # s3에 있는 기존의 파일을 현재 파일로 대체한다.
            client.upload_fileobj(file, Config.BUCKET_NAME, imgUrl , ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type })

        except Exception as e:
            return {'error' : 's3에 저장할 데이터를 정확히 보내세요.'}, 400
        
        # 수정할 술도감의 정보를 DB에 업데이트 한다.
        try :
            connection = get_connection()

            query = '''update alcohol
                    set name = %s, percent = %s, alcoholType = %s, category = %s, produce = %s, supply = %s
                    where id = %s;'''

            record = (name, percent, alcoholType, category, produce, supply, alcohol_id)
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
        
        return {'result' : 'success'}, 200
    
# 관리자용 술도감 삭제 api [관리자용 페이지에서 삭제버튼을 눌렀을시 실행되는 api]
class AlcoholDeleteResource(Resource):
    
    @jwt_required()
    def delete(self, alcohol_id) :
        # 관리자만 삭제 가능
        user_id = get_jwt_identity()
        if user_id != 1 :
            return {'error' : '관리자만 삭제 가능합니다.'}, 400
        # 삭제할 술도감의 이미지를 s3에서 삭제한다.
        client = boto3.client('s3',
                              aws_access_key_id = Config.ACCESS_KEY,
                              aws_secret_access_key = Config.SECRET_ACCESS
                              )
        
        # 이미지를 삭제하기 위해 imgUrl을 가져온다.
        try :
            connection = get_connection()
            query = '''select imgUrl
                    from alcohol
                    where id = %s;'''
            record = (alcohol_id, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)
            result_list = cursor.fetchall()
            imgUrl = result_list[0]['imgUrl'].split("com/")[1]

            # 삭제할 술도감의 정보를 DB에서 삭제한다.
            query = '''delete from alcohol
                    where id = %s;'''
            cursor = connection.cursor()
            cursor.execute(query, record)

            
            # s3에서 이미지를 삭제한다.
            stat = client.delete_objects(
            Bucket=Config.BUCKET_NAME,
            Delete={
                'Objects': [
                    {
                        'Key': imgUrl
                    }
                ],
            },
            )
    
            connection.commit()
        except Exception as e :
            # 에러가 발생하면 롤백한다.
            connection.rollback()
            print(e)
            return {'error' : str(e)}, 500
        
        finally :
            cursor.close()
            connection.close()
        
        return {'result' : 'success'}, 200
    








