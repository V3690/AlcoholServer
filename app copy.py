from flask import Flask 
from flask_restful import Api
from flask_jwt_extended import JWTManager
from config import Config
from resource.user import UserLoginResource, UserLogoutResource, UserRegisterResource, UserResource, jwt_blocklist
from resource.alcohol import AlcoholRequestResource, AlcoholListResource, AlcoholResource
from resource.emotion import RekognitionEmotionResource


app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
jwt = JWTManager(app)

# 로그아웃된 토큰으로 요청하는 경우 처리하는 코드작성.
@jwt.token_in_blocklist_loader # 토큰이 만료되었는지 확인하는 함수를 등록한다.
def check_if_token_is_revoked(jwt_header, jwt_payload): # 토큰이 만료되었는지 확인하는 함수
    jti = jwt_payload['jti'] # jti는 JWT 토큰의 고유 식별자
    return jti in jwt_blocklist 

# 회원가입, 로그인, 로그아웃 엔드포인트
api.add_resource(UserRegisterResource, '/user/register') 
api.add_resource(UserLoginResource, '/user/login')
api.add_resource(UserLogoutResource, '/user/logout')
api.add_resource(UserResource, '/user/preference')

# 경로와 리소스(API코드)를 연결한다.
api.add_resource(AlcoholRequestResource, '/alcohol/request')
api.add_resource(AlcoholListResource, '/alcohol')
api.add_resource(AlcoholResource, '/alcohol/<int:alcohol_id>')
api.add_resource(RekognitionEmotionResource, '/emotion')


if __name__ == '__main__': 
    app.debug = True
    app.run() # debug=True 는 개발할때만 사용해야함 # 배포할때는 False로 바꿔야함 
    # debug=True 는 코드를 수정하면, 서버를 재시작하지 않아도, 자동으로 코드가 반영됨
    # 디버그 모드를 사용하려면 set FLASK_ENV=development 를 cmd에 입력해야함
