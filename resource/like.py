from flask import request 
from flask_restful import Resource 
from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity

# 레시피 좋아요 누르기
class LikeRecipeResource(Resource):
    @jwt_required()
    def post(self, recipe_id) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''insert into likeRecipe (userId, recipeId)
                    values (%s, %s);'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (user_id, recipe_id ))

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        return {"result" : "success"}, 200
    
    # 레시피 좋아요 취소
    @jwt_required()
    def delete(self, recipe_id) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''delete from likeRecipe
                    where userId = %s and recipeId = %s;'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (user_id, recipe_id ))

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        return {"result" : "success"}, 200
    
# 술도감 좋아요 누르기
class LikeAlcoholResource(Resource):
    @jwt_required()
    def post(self, alcohol_id) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''insert into likeAlcohol (userId, alcoholId)
                    values (%s, %s);'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (user_id, alcohol_id ))

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        return {"result" : "success"}, 200
    
    # 술도감 좋아요 취소
    @jwt_required()
    def delete(self, alcohol_id) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''delete from likeAlcohol
                    where userId = %s and alcoholId = %s;'''

            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, (user_id, alcohol_id ))

            connection.commit()

            cursor.close()
            connection.close()

        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        return {"result" : "success"}, 200

