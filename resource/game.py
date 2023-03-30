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
import pandas as pd


## 오락실 페이지 ##


# 건배사 (룰베이스챗봇)
class CheersResource(Resource):
    @jwt_required()
    def post(self) :
        type = request.args.get('type')
        data = request.get_json()

        try :
            connection = get_connection()

            query = '''select *
                    from cheersMent
                    where type = '''+ type +''';'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, )


            result_list = cursor.fetchall()

            cursor.close()
            connection.close()

            chatbot_data = pd.DataFrame(result_list)
            # print(chatbot_data)

            # 이게 잘 된 버전
            chatbot_data = chatbot_data.fillna(" ")
            # rule의 데이터를 split 하여 list형태로 변환 후, index값과 함께 dictionary 형태로 저장 
            chat_dic = {} 
            row = 0 
            for rule in chatbot_data['rule']: 
                chat_dic[row] = rule.split('|')
                row += 1 

            chat = data['ment']

            # result_df = pd.DataFrame(columns=[['title', 'first', 'last']])
            cheers_list = []


            for k, v in chat_dic.items():
                chat_flag = False
                for word in v:
                    if word in chat:
                        chat_flag = True
                        
                    else:
                        chat_flag = False
                    break
                
                if chat_flag:

                    cheers_list.append(chatbot_data[chatbot_data.index == k])


            random_num = random.randint(0, len(cheers_list)-1)

            cheers_list[random_num].to_dict()


            key = list(cheers_list[random_num].to_dict()['title'].keys())[0]

            cheers_dict = {"title" :cheers_list[random_num].to_dict()['title'].get(key) , 
               "first" :cheers_list[random_num].to_dict()['first'].get(key),
               "last" :cheers_list[random_num].to_dict()['last'].get(key)}
      
            print(cheers_dict)

            return {"result" : "success" ,
                "item" : cheers_dict}, 200
        

            
        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500
        
        except ValueError as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : "다른 단어 또는 문장을 입력해주세요"}, 500
                

# 지금 내 얼굴은 (레코그니션얼굴인식)
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
                                    'face/'+ file.filename,
                                    ExtraArgs = {'ACL':'public-read', 'ContentType' : file.content_type } )
        
        except Exception as e:
            return {'error' : str(e)}, 500

        # 3. S3에 저장된 사진을 detect_faces 한다
        #    (AWS Rekognition 이용)
        client = boto3.client('rekognition',
                    'ap-northeast-2',
                    aws_access_key_id=Config.ACCESS_KEY,
                    aws_secret_access_key = Config.SECRET_ACCESS)

        response = client.detect_faces(Image={'S3Object':{'Bucket':Config.BUCKET_NAME, 'Name': 'face/' + file.filename}}, Attributes=['ALL'])

        # print(response)

        for faceDetail in response['FaceDetails']:
            emotion = faceDetail['Emotions'][0]['Type']
            
            # return { "result" : emotion }


        try :
            connection = get_connection()
            query = '''select a.id as alcoholId, a.name, a.imgUrl, ea.emotionId, e.name as emotion, ea.content
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

            random_num = random.randint(0, len(emotion_result)-1)

            return { "result" : emotion_result[random_num] }



        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        
        # return { "result" : "success" ,
        #         "alcohol" : emotion_result[random_num] }, 200


# 명령 상자 (랜덤) - 주사위게임
# subjectType_id === >  1 : 본인만, 2: 본인제외 , 3: 전체랜덤
# penaltyType_id === >  1 : 벌칙,  2  : 벌주, 3: 전체랜덤
class DiceResource(Resource):
    @jwt_required()
    def get(self, subjectType_id, penaltyType_id) :

        try :
            connection = get_connection()
        
            # 본인만
            if subjectType_id ==1 :

                query = '''select *
                        from diceSubject
                        where subject = "내가";'''
                
                cursor = connection.cursor(dictionary=True)


                cursor.execute(query, )

                subject_list = cursor.fetchall()
                subject_list = subject_list[0]['subject']

                if penaltyType_id == 1 or penaltyType_id == 2 :

                    query = '''select * from dicePenalty
                            where penaltyType = ''' + str(penaltyType_id) +''';'''
                                        
                    # record = (penaltyType, )
                    cursor = connection.cursor(dictionary= True)
                    cursor.execute(query, )

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

                action_list = action_list[random.randint( 1, len(action_list) -1 )]['action']
                    

            
            # 본인 제외
            if subjectType_id == 2 :

                query = '''select *
                        from diceSubject
                        where subject not in ("내가");'''
                cursor = connection.cursor(dictionary=True)

                cursor.execute(query, )

                subject_list = cursor.fetchall()

                subject_list = subject_list[random.randint( 1, len(subject_list) -1 )]['subject']

                if penaltyType_id == 1 or penaltyType_id == 2 :

                    query = '''select * from dicePenalty
                            where penaltyType = ''' + str(penaltyType_id) +''';'''
                                        
                    # record = (penaltyType, )
                    cursor = connection.cursor(dictionary= True)
                    cursor.execute(query, )

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

                action_list = action_list[random.randint( 1, len(action_list) -1 )]['action']
                    

            # 전체랜덤
            if subjectType_id == 3:

                query = '''select *
                        from diceSubject;'''

                # record = (user_id, )

                cursor = connection.cursor(dictionary=True)

                cursor.execute(query, )

                subject_list = cursor.fetchall()

                subject_list = subject_list[random.randint( 1, len(subject_list) -1 )]['subject']
                if penaltyType_id == 1 or penaltyType_id == 2 :

                    query = '''select * from dicePenalty
                            where penaltyType = ''' + str(penaltyType_id) +''';'''
                                        
                    # record = (penaltyType, )
                    cursor = connection.cursor(dictionary= True)
                    cursor.execute(query, )

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

                action_list = action_list[random.randint( 1, len(action_list) -1 )]['action']
                
            
            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        return {"result" : "success",
                "subject": subject_list,
                "action" : action_list},200


# 심심이 - gpt3를 이용한
# class GPT3CHATBOTRESOURCE(Resource):
#     @jwt_required()
#     def post(self) :
#         data = request.get_json()
        
#         try:

#             openai.api_key = Config.OPENAI_SECRET_KEY
#             response = openai.Completion.create(
#             model="text-davinci-003",
#             prompt=data['question'],
#             temperature=0.9,
#             max_tokens=300,
#             top_p=1,
#             frequency_penalty=0,
#             presence_penalty=0.6
#             )

#             generated_text = response.choices[0].text
#             print(generated_text)


            
#         except Error as e :
#             print(e)
#             return {'error' : str(e)}, 500
        
#         except ValueError as e :
#             print(e)
#             return {'error' : "다른 단어 또는 문장을 입력해주세요"}, 500
                
#         return {"result" : "success",
#                 "answer": generated_text},200







