from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
import boto3
from mysql_connection import get_connection
from config import Config

# 주인장에게 술 데이터 요청하는 api
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