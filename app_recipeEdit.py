from flask import Flask 
from flask_restful import Api
from flask_jwt_extended import JWTManager
from config import Config
from resource.alcohol import AlcoholListResource, AlcoholRequestResource, AlcoholResource
from resource.creating import CreatingAlcoholList, CreatingIngredientList, CreatingRecipe, CreatingRecipeIngredient, CreatingSearchAlcohol, CreatingSearchIngredient
from resource.creating_copy import CreatingRecipeEdit, CreatingRecipeEditMaster, CreatingRecipeIngredientEdit
from resource.game import RekognitionEmotionResource, DiceResource
from resource.recipe import RecipeAllListResource, RecipeHonorListResource, RecipeLikeListResource, RecipeLikeSearchResource, RecipeMasterListResource, RecipeMasterallListResource, RecipeMyListResource, RecipeResource, RecipeUserListResource
from resource.user import UserLoginResource, UserLogoutResource, UserRegisterResource, UserResource, jwt_blocklist, UserDetailResource



app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
jwt = JWTManager(app)

# 로그아웃된 토큰으로 요청하는 경우 처리하는 코드작성.
@jwt.token_in_blocklist_loader # 토큰이 만료되었는지 확인하는 함수를 등록한다.
def check_if_token_is_revoked(jwt_header, jwt_payload): # 토큰이 만료되었는지 확인하는 함수
    jti = jwt_payload['jti'] # jti는 JWT 토큰의 고유 식별자
    return jti in jwt_blocklist 

# 회원가입, 로그인, 로그아웃, 신규회원취향 , 내정보 엔드포인트
api.add_resource(UserRegisterResource, '/user/register') 
api.add_resource(UserLoginResource, '/user/login')
api.add_resource(UserLogoutResource, '/user/logout')
api.add_resource(UserResource, '/user/preference')
api.add_resource(UserDetailResource, '/user/detail') 

# 경로와 리소스(API코드)를 연결한다.
api.add_resource(AlcoholRequestResource, '/alcohol/request')
api.add_resource(AlcoholListResource, '/alcohol')
api.add_resource(AlcoholResource, '/alcohol/<int:alcohol_id>')
api.add_resource(RekognitionEmotionResource, '/emotion')
api.add_resource(DiceResource, '/game/dice/<int:penaltyType_id>')


# 레시피 (주인장추천, 명예 주인장, 즐겨찾기) 엔드포인트
api.add_resource(RecipeMasterListResource, '/recipe/master')
api.add_resource(RecipeHonorListResource, '/recipe/honor')
api.add_resource(RecipeLikeListResource, '/recipe/favorite')
api.add_resource(RecipeLikeSearchResource, '/recipe/favorite/search')

# 레시피 주인장전체목록,유저전체목록,주인장+유저전체목록, 내가만든전체목록,세부레시피조회
api.add_resource(RecipeMasterallListResource,'/recipe/Masterall')
api.add_resource(RecipeUserListResource,'/recipe/user')
api.add_resource(RecipeMyListResource,'/recipe/me')
api.add_resource(RecipeAllListResource,'/recipe/all')
api.add_resource(RecipeResource, '/recipe/user/<int:recipe_id>')


# 레시피 작성
api.add_resource(CreatingRecipe, '/creating/recipe')
api.add_resource(CreatingRecipeIngredient, '/creating/ingredient')
# 레시피 재료 목록
api.add_resource(CreatingAlcoholList, '/creating/list/alcohol')
api.add_resource(CreatingIngredientList, '/creating/list/ingredient')
# 레시피 재료 검색
api.add_resource(CreatingSearchAlcohol, '/creating/search/alcohol')
api.add_resource(CreatingSearchIngredient, '/creating/search/ingredient')


# 레시피 수정 삭제모음
api.add_resource(CreatingRecipeEdit,'/creating/recipe/edit/<int:recipe_id>')
api.add_resource(CreatingRecipeIngredientEdit,'/creating/ingredient/edit/<int:recipe_id>')
api.add_resource(CreatingRecipeEditMaster,'/creating/recipe/edit/master/<int:recipe_id>')



if __name__ == '__main__': 
    app.debug = True
    app.run() # debug=True 는 개발할때만 사용해야함 # 배포할때는 False로 바꿔야함 
    # debug=True 는 코드를 수정하면, 서버를 재시작하지 않아도, 자동으로 코드가 반영됨
    # 디버그 모드를 사용하려면 set FLASK_ENV=development 를 cmd에 입력해야함