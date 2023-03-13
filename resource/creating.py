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
# 레시피 저장
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
        if (title == "") or (percent == "") or (content == "") or (file == "") :
            return {'error' : '<한글 이름, 도수, 레시피, 이미지>는 필수입니다.'}, 400

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

# 레시피-술/재료 저장
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


# 선택한 술/재료 불러오기 (화면에 나타내기)



