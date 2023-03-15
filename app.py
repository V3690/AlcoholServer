from flask import Flask 
from flask_restful import Api
from flask_jwt_extended import JWTManager
from config import Config
from resource.alcohol import AlcoholAddResource, AlcoholDeleteResource, AlcoholListResource, AlcoholRequestResource, AlcoholResource, AlcoholUpdateResource
from resource.creating import CreatingAlcoholList, CreatingIngredientList, CreatingRecipe, CreatingRecipeEdit, CreatingRecipeEditMaster, CreatingRecipeIngredient, CreatingRecipeIngredientEdit, CreatingSearchAlcohol, CreatingSearchIngredient
from resource.game import CheersResource, DiceResource, RekognitionEmotionResource
from resource.like  import LikeAlcoholResource, LikeRecipeResource
from resource.recipe import RecipeAllListResource, RecipeHonorListResource, RecipeLikeListResource, RecipeLikeSearchResource, RecipeMasterListResource, RecipeMasterallListResource, RecipeMyListResource, RecipeResource, RecipeUserListResource
from resource.user import jwt_blocklist, UserDetailResource, UserLoginResource, UserLogoutResource, UserNicknameResetResource, UserPasswordResetResource, UserRegisterResource, UserResource



app = Flask(__name__)
api = Api(app)
app.config.from_object(Config)
jwt = JWTManager(app)

# 로그아웃된 토큰으로 요청하는 경우 처리하는 코드작성.
@jwt.token_in_blocklist_loader # 토큰이 만료되었는지 확인하는 함수를 등록한다.
def check_if_token_is_revoked(jwt_header, jwt_payload): # 토큰이 만료되었는지 확인하는 함수
    jti = jwt_payload['jti'] # jti는 JWT 토큰의 고유 식별자
    return jti in jwt_blocklist 



##### 앱 시작 #####

# 회원가입, 로그인, 로그아웃, 회원추가정보
api.add_resource(UserRegisterResource, '/user/register') 
api.add_resource(UserLoginResource, '/user/login')
api.add_resource(UserLogoutResource, '/user/logout')
api.add_resource(UserResource, '/user/preference')


##### 하단바 #####

# 메인 페이지 (추천 공식 레시피, 인기 창작 레시피)
api.add_resource(RecipeMasterListResource, '/recipe/master')
api.add_resource(RecipeHonorListResource, '/recipe/honor')

# 즐겨찾기 (필터링, 검색)
api.add_resource(RecipeLikeListResource, '/recipe/favorite')
api.add_resource(RecipeLikeSearchResource, '/recipe/favorite/search')

# 닉네임변경, 비밀번호변경, 탈퇴
api.add_resource(UserNicknameResetResource,'/user/edit/nickname')
api.add_resource(UserPasswordResetResource,'/user/edit/password')
api.add_resource(UserDetailResource, '/user/detail') 


##### 레시피 메뉴 #####

# 레시피 목록 (공식, 창작, 공식+창작, 본인, 1개 세부 정보)
api.add_resource(RecipeMasterallListResource,'/recipe/Masterall')
api.add_resource(RecipeUserListResource,'/recipe/user')
api.add_resource(RecipeAllListResource,'/recipe/all')
api.add_resource(RecipeMyListResource,'/recipe/me')
api.add_resource(RecipeResource, '/recipe/<int:recipe_id>')

# 레시피 작성, 재료 등록
api.add_resource(CreatingRecipe, '/creating/recipe')
api.add_resource(CreatingRecipeIngredient, '/creating/ingredient')
# 레시피 재료 목록
api.add_resource(CreatingAlcoholList, '/creating/list/alcohol')
api.add_resource(CreatingIngredientList, '/creating/list/ingredient')
# 레시피 재료 검색
api.add_resource(CreatingSearchAlcohol, '/creating/search/alcohol')
api.add_resource(CreatingSearchIngredient, '/creating/search/ingredient')

# 본인 레시피 수정, 삭제
api.add_resource(CreatingRecipeEdit,'/creating/recipe/edit/<int:recipe_id>')
# 본인 레시피 재료 수정
api.add_resource(CreatingRecipeIngredientEdit,'/creating/ingredient/edit/<int:recipe_id>')
# 전체 레시피 수정, 삭제 (관리자 전용)
api.add_resource(CreatingRecipeEditMaster,'/creating/recipe/edit/master/<int:recipe_id>')


##### 술도감 메뉴 #####

# 술 도감 (전체 목록, 1개 세부 정보)
api.add_resource(AlcoholListResource, '/alcohol')
api.add_resource(AlcoholResource, '/alcohol/<int:alcohol_id>')
# 유저의 요청(데이터 수정/추가)
api.add_resource(AlcoholRequestResource, '/alcohol/request')

# 술 추가, 수정, 삭제 (관리자 전용)
api.add_resource(AlcoholAddResource, '/alcohol/add')
api.add_resource(AlcoholUpdateResource, '/alcohol/update/<int:alcohol_id>')
api.add_resource(AlcoholDeleteResource, '/alcohol/delete/<int:alcohol_id>')


##### 오락실 메뉴 #####

api.add_resource(RekognitionEmotionResource, '/game/emotion')
api.add_resource(DiceResource, '/game/dice/<int:subjectType_id>/<int:penaltyType_id>')
api.add_resource(CheersResource, '/game/cheers')

#### 좋아요 #####

#레시피 좋아요
api.add_resource(LikeRecipeResource, '/recipe/<int:recipe_id>/like')
#술도감 좋아요
api.add_resource(LikeAlcoholResource, '/alcohol/<int:alcohol_id>/like')

if __name__ == '__main__': 
    app.debug = True
    app.run() # debug=True 는 개발할때만 사용해야함 # 배포할때는 False로 바꿔야함 
    # debug=True 는 코드를 수정하면, 서버를 재시작하지 않아도, 자동으로 코드가 반영됨
    # 디버그 모드를 사용하려면 set FLASK_ENV=development 를 cmd에 입력해야함
