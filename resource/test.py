from flask_restful import Resource 

# 깃 액션을 테스트해봅니다
class GitActionTestResource(Resource):
    def get(self) :
        return {"result" : "success"}, 200