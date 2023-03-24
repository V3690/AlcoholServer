from flask import request 
from flask_restful import Resource 
from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import create_access_token, get_jwt, jwt_required, get_jwt_identity
from email_validator import validate_email, EmailNotValidError # 이메일 유효성 검사 라이브러리 
from utils import hash_password, check_password


## 앱 시작 / 유저 정보 관리 ##


# 회원가입
class UserRegisterResource(Resource):
    
    def post(self):
        
        # 클라이언트가 보낸 데이터를 받는다.
        data = request.get_json() 
     
        # data에 email이 있는지 확인한다.
        if "email" in data:
            # 이메일 중복검사
            try:
                connection = get_connection()
                query = """
                    SELECT email FROM users WHERE email = %s;
                    """
                cursor = connection.cursor()
                cursor.execute(query, (data['email'], ))
                record = cursor.fetchone()
                cursor.close()
                connection.close()
                print(record)
                if record:
                    return {'error': '이미 존재하는 이메일입니다.'}, 400
            except Error as e:
                print(e)
                cursor.close()
                connection.close()
                return {'error': str(e) }, 500 # 500은 서버에러를 리턴하는 에러코드
        
        # data에 nickname이 있는지 확인한다.
        if "nickname" in data:
            # 닉네임이 이미 존재하는지 확인한다.
            try:
                connection = get_connection()
                query = """
                    SELECT nickname FROM users WHERE nickname = %s;
                    """
                cursor = connection.cursor()
                cursor.execute(query, (data['nickname'], ))
                record = cursor.fetchone()
                cursor.close()
                connection.close()
                print(record)
                if record:
                    return {'error': '이미 존재하는 닉네임입니다.'}, 400
            except Error as e:
                print(e)
                cursor.close()
                connection.close()
                return {'error': str(e) }, 500 # 500은 서버에러를 리턴하는 에러코드
            

        # email 유효성 검사 
        try:
            validate_email(data['email']) 
        except EmailNotValidError as e:
            return {'error': str(e)}, 400 

        # 비밀번호 유효성 검사
        if len(data['password']) < 4 or len(data['password']) > 12: 
            return {'error': '비밀번호는 4자리 이상, 12자리 이하로 입력해주세요.'}, 400 
        
        hashed_password = hash_password( data['password'] ) 

                # {
                #     "email": "master@naver.com",
                #     "password": "12341234",
                #     "nickname": "마스터"
                #      "accountType" : "recipeApp"
                # }
        try:
            connection = get_connection()

            query = """
                INSERT INTO users ( email, password, nickname,accountType) 
                VALUES (%s, %s, %s,%s);
                """
            
            record = (data['email'],hashed_password, data['nickname'],data['accountType'] )
            
            cursor = connection.cursor() # 커서를 가져온다.
            cursor.execute(query, record) # 쿼리를 실행한다.
            connection.commit() # 커밋한다.
            
            ### DB에 회원가입하여, insert 된 후에
            ### user 테이블의 id 값을 가져오는 코드!
            user_id = cursor.lastrowid # 마지막에 추가된 row의 id를 가져온다.

            cursor.close() # 커서를 닫는다.
            connection.close() # 커넥션을 닫는다.

        except Error as e:
            print(e)
            cursor.close() 
            connection.close()
            return {'error': str(e) }, 500 # 500은 서버에러를 리턴하는 에러코드
       
        # user_id를 바로 클라이언트에게 보내면 안되고,
        # jwt로 암호화 해서, 인증토큰을 보낸다.

        acces_token = create_access_token(identity=user_id ) # identity는 토큰에 담길 내용이다. # 담을게 여러개면 딕셔너리 형태로담는다.  
        # expires_delta는 토큰의 유효기간이다. # timedelta로 지정한다. # timedelta는 datetime에서 가져온다.

        return {'access_token': acces_token}, 200 # 200은 성공했다는 의미의 코드

# 로그인
class UserLoginResource(Resource):
   
    def post(self) :
        # {"email":"zzez@naver.com",
        # "password" : "1234" } # 클라이언트가 보낸 데이터
        
        # 1. 클라이언트가 보낸 데이터를 받는다.
        data = request.get_json()
        
        # 2. DB 로부터 해당 유저의 데이터를 가져온다.
        try :
            connection = get_connection()
            query = """
                select * 
                from users
                where email = %s and accountType = %s;
            """
            record = (data['email'],data['accountType']) 
            
            cursor = connection.cursor(dictionary=True) # dictionary=True를 하면, DB의 컬럼명을 key로 가지는 딕셔너리를 리턴한다.
            cursor.execute(query, record)
            
            result_list = cursor.fetchall() # fetchall은 모든 데이터를 가져온다. # 데이터형식은 리스트안의 딕셔너리이다. 
            
            if len(result_list) == 0 :
                return {'error' : '존재하지 않는 이메일입니다.'}, 400

            cursor.close()
            connection.close()

        except Error as e :
            print(e)
            cursor.close()
            connection.close()
            return {'error' : str(e)}, 500 # 500은 서버에러를 리턴하는 에러코드

        # 3. 비밀번호를 비교한다.
        check = check_password(data['password'], result_list[0]['password']) 

        if check == False :
            return {'error' : '비밀번호가 틀렸습니다.'}, 400

        # 4. id를 jwt 토큰을 만들어서 클라이언트에게 보낸다.
        acces_token = create_access_token(identity=result_list[0]['id'] ) # identity는 토큰에 담길 내용이다. # 담을게 여러개면 딕셔너리 형태로담는다.

        return {'nickname' : result_list[0]['nickname'],'access_token': acces_token}, 200 # 200은 성공했다는 의미의 코드

## 로그아웃된 토큰을 저장할 set 만든다.
jwt_blocklist = set() # set은 중복을 허용하지 않는다.

# 로그 아웃
class UserLogoutResource(Resource) :

    # 로그아웃
    @jwt_required() # jwt 토큰이 필요한 리소스이다.
    def post(self) :
        
        jti = get_jwt()['jti'] # jti는 jwt 토큰의 고유한 식별자이다. # get_jwt()는 토큰의 내용을 딕셔너리 형태로 리턴한다.
        
        jwt_blocklist.add(jti) # 로그아웃된 토큰을 저장한다.

        return {'result' : '로그아웃 성공'}, 200

# 회원 추가 정보
class UserResource(Resource) :
    @jwt_required()
    def post(self) :
        # 클라이언트가 보낸 데이터를 받는다.
        data = request.get_json()
        user_id = get_jwt_identity() # 토큰에 담긴 id를 가져온다.
        print(data)
# 주종          # 누구와함께
# id name       # id name
# 1 맥주        # 1 가족
# 2	소주        # 2 친구
# 3	막걸리      # 3 혼자
# 4	와인        # 4 직장
# 5	양주        # 5 지인
# 6	기타        # 6 기타

# 도수     
# percent # tynyint

        # 클라이언트로부터 받은 데이터는 다음과 같다.
        # {
        #     "alcoholType": "1,2,3,4,5,6",
        #     "withs": "1,2,3,4,5,6",
        #     "percent": "50"
        # }
      
        alcohol_types = data['alcoholType'].split(',')
        withs = data['withs'].split(',')
        percent = data['percent']

        try:
            connection = get_connection()
            cursor = connection.cursor()

            for alcohol_type in alcohol_types:
                cursor.execute(
                    "INSERT INTO usersAlcoholType (userId, alcoholTypeId) VALUES (%s, %s)",
                    (user_id, alcohol_type)
                )

            for with_id in withs:
                cursor.execute(
                    "INSERT INTO usersWiths (userId, withsId) VALUES (%s, %s)",
                    (user_id, with_id)
                )

            cursor.execute(
                "UPDATE users SET percent = %s WHERE id = %s",
                (percent, user_id)
            )

            connection.commit()
            return {"result": "success"}, 200

        # 오류가 발생한 경우 데이터베이스 트랜잭션에 롤백을 추가
        except Error as e:
            print(e)
            connection.rollback() 
            return {"result": "fail", "error": str(e)}, 500

        # 오류 발생 여부에 관계없이 데이터베이스 커서 및 연결을 닫는 블록
        finally:
            cursor.close()
            connection.close()



# 닉네임 변경
class UserNicknameResetResource(Resource):
    @jwt_required()
    def put(self) :
        user_id = get_jwt_identity()
        data = request.get_json() 
        if "nickname" in data:
            # 닉네임이 이미 존재하는지 확인한다.
            try:
                connection = get_connection()
                query = """
                    SELECT nickname FROM users WHERE nickname = %s;
                    """
                cursor = connection.cursor()
                cursor.execute(query, (data['nickname'], ))
                record = cursor.fetchone()
                cursor.close()
                connection.close()
                
                if record:
                    return {'error': '이미 존재하는 닉네임입니다.'}, 400
            except Error as e:
                print(e)
                cursor.close()
                connection.close()
                return {'error': str(e) }, 500 # 500은 서버에러를 리턴하는 에러코드
            
            try :
                connection = get_connection()

                query = f'''update users 
                    set nickname = %s
                        where id = {user_id};'''

                record = (data['nickname'],)
                cursor = connection.cursor(dictionary= True)
                cursor.execute(query, record)

                connection.commit()

                cursor.close()
                connection.close()

            except Error as e :
                print(e)
                cursor.close()
                connection.close()
                return {'error' : str(e)}, 500

            return {'result' : 'success',}, 200

# 비밀번호 변경
class UserPasswordResetResource(Resource) :
    @jwt_required()
    def put(self):
        user_id = get_jwt_identity()
        data = request.get_json()

        if len(data['password']) < 4 or len(data['password']) > 12: 
            return {'error': '비밀번호는 4자리 이상, 12자리 이하로 입력해주세요.'}, 400 
        
        hashed_password = hash_password( data['password'] ) 

        try :
            # DB에 연결
            connection = get_connection()

            # 쿼리문 만들기
            query = '''update users
                    set password = %s
                    where id = %s;'''

            record = (hashed_password, user_id )

            # 커서를 가져온다.
            cursor = connection.cursor()

            # 쿼리문을 커서를 이용해서 실행한다
            cursor.execute(query, record)

            # 커넥션을 커밋해줘야한다
            connection.commit()

            # 자원 해제
            cursor.close()
            connection.close()

        except Error as e:
            print(e)
            cursor.close() 
            connection.close()
            return {'error': str(e) }, 500 # 500은 서버에러를 리턴하는 에러코드

        return {'result' : 'success'}, 200 # 200은 성공했다는 의미의 코드

# 탈퇴
class UserDetailResource(Resource) :
    # 유저가 탈퇴하면 호출되는 API
    @jwt_required()
    def delete(self) :

        user_id = get_jwt_identity()
        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "DELETE FROM users WHERE id = %s",
                (user_id,)
            )
            connection.commit()
            
            jti = get_jwt()['jti'] 
        
            jwt_blocklist.add(jti) 

            return {"result": "success"}, 200
        
        except Error as e:
            print(e)
            connection.rollback() 
            return {"result": "fail", "error": str(e)}, 500
        
        finally:
            cursor.close()
            connection.close()

      







