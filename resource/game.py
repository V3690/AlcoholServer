from flask import request
from flask_restful import Resource
from datetime import datetime
import boto3
from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from flask_jwt_extended import get_jwt_identity
from mysql_connection import get_connection
from config import Config
import random

class RekognitionEmotionResource(Resource) :
    @jwt_required()
    def post(self) :

    # 1. 클라이언트가 보낸 데이터를 받는다.fl
        if 'photo' not in request.files :
            return {'error' : '파일을 업로드 하세요'}, 400

        file = request.files['photo']

    # 2. 사진을 먼저 S3에 저장
        ### 2-1. aws 콘솔로 가서 IAM 유저 만든다.(없으면 만든다)
        ### 2-2. s3 로 가서 이 프로젝트의 버킷을 만든다.
        ### 2-3. config.py 에 적어준다.
        ### 2-4. 파일명을 유니크하게 만든다.

        current_time = datetime.now()
        new_file_name = current_time.isoformat().replace(':','_')+'.jpg'

        file.filename = new_file_name
        
        ### 2-5. S3에 파일 업로드 한다.
        ###      파일 업로드하는 코드는! boto3라이브러리를
        ###      이용해서 업로드한다.
        ###      라이브러리가 설치안되어있으면, pip install boto3 로 설치한다.

        client = boto3.client('s3', 
                    aws_access_key_id = Config.ACCESS_KEY,
                    aws_secret_access_key = Config.SECRET_ACCESS)
        
        try :
            client.upload_fileobj(file,
                                    Config.BUCKET_NAME,
                                    new_file_name,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )
        
        except Exception as e:
            return {'error' : str(e)}, 500

        # 3. S3에 저장된 사진을 detect_faces 한다
        #    (AWS Rekognition 이용)
        client = boto3.client('rekognition',
                    'ap-northeast-2',
                    aws_access_key_id=Config.ACCESS_KEY,
                    aws_secret_access_key = Config.SECRET_ACCESS)

        response = client.detect_faces(Image={'S3Object':{'Bucket':Config.BUCKET_NAME, 'Name':new_file_name}}, Attributes=['ALL'])

        # print(response)

        for faceDetail in response['FaceDetails']:
            emotion = faceDetail['Emotions'][0]['Type']
            
            # return { "result" : emotion }


        try :
            connection = get_connection()
            query = '''select a.id as alcoholId, a.name, ea.emotionId, e.name as emotion, ea.content
                    from alcohol a
                    join emotionAlcohol ea
                    on a.id = ea.alcoholId
                    join emotion e
                    on ea.emotionId = e.id
                    where e.name = %s;'''
            
            record = (emotion, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)

            emotion_result = cursor.fetchall()

        
            cursor.close()
            connection.close()

            random_num = random.randint(0, 3)

            return { "result" : emotion_result[random_num] }



        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        
        # return { "result" : "success" ,
        #         "alcohol" : emotion_result[random_num] }, 200


# 주사위 게임 API
# penaltyType_id : 1 , 벌칙
# penaltyType_id : 2 , 벌주
# penaltyType_id : 1 , 벌칙 + 벌주 중 랜덤으로 하나
class DiceResource(Resource):
    @jwt_required()
    def get(self, penaltyType_id) :
        try :

            if penaltyType_id == 1 or penaltyType_id == 2:


                connection = get_connection()
                query = '''select * from dicePenalty
                        where penaltyType = %s;'''
                                    
                record = (penaltyType_id, )
                cursor = connection.cursor(dictionary= True)
                cursor.execute(query, record)

                action_list = cursor.fetchall()

                if action_list[0]['id'] is None :
                    return{'error' : '잘못된 알콜 아이디 입니다.'}, 400
                
            elif penaltyType_id == 3:
                connection = get_connection()
                query = '''select * from dicePenalty;'''
                                    
                # record = (penaltyType_id, )
                cursor = connection.cursor(dictionary= True)
                cursor.execute(query, )

            #     cursor = connection.cursor(dictionary=True)
            #     cursor.execute(query, 

                action_list = cursor.fetchall()


            query = '''select * from diceSubject;'''
            
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, )

            subject_list = cursor.fetchall()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
        
        # print(subject_list[random.randint( 1, len(subject_list) -1 )]['subject'])
        
        # print("subject_list : " + str(len(subject_list)))
        # print("action_list : " + str(len(action_list)))
        
        return { "result" : "success" ,
                "subject": subject_list[random.randint( 1, len(subject_list) -1 )]['subject'],
                "alcohol" : action_list[random.randint( 1, len(action_list) -1 )]['action']}, 200