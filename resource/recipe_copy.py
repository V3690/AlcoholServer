from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from mysql.connector import Error
from datetime import datetime
from flask_jwt_extended import get_jwt_identity
import boto3
from mysql_connection import get_connection
from config import Config

#주인장레시피 목록 불러오기
class RecipeMasterallListResource(Resource):
    @jwt_required()
    def get(self) :
        # user_id = get_jwt_identity()

        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()

            query = '''select r.id, r.title, r.percent , count(l.userId) as cnt
                    from recipe r
                    left join likeRecipe l
                    on r.id = l.recipeId
                    where r.userId= 1
                    group by r.id
                    order by ''' + order + '''  desc
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


# 유저레시피 목록 불러오기
class RecipeUserListResource(Resource):
    @jwt_required()
    def get(self) :
      

        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select r.id, r.title, r.percent , count(l.userId) as cnt
                    from recipe r
                    left join likeRecipe l
                    on r.id = l.recipeId
                    where r.userId NOT IN(1)
                    group by r.id
                    order by ''' + order + '''  desc
                    limit ''' + offset + ''', '''+ limit + ''';'''

        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,)

            result_list = cursor.fetchall()

          

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
                
        # print(result_list)

        return {"result" : "success" ,
                "items" : result_list , 
                "count" : len(result_list)}, 200


# 전체목록(주인장 + 유저) 불러오기
class RecipeAllListResource(Resource):
    @jwt_required()
    def get(self) :
      

        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select r.id, r.title, r.percent , count(l.userId) as cnt
                    from recipe r
                    left join likeRecipe l
                    on r.id = l.recipeId
                    group by r.id
                    order by ''' + order + '''  desc
                    limit ''' + offset + ''', '''+ limit + ''';'''

        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,)

            result_list = cursor.fetchall()

          

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
                
        # print(result_list)

        return {"result" : "success" ,
                "items" : result_list , 
                "count" : len(result_list)}, 200



#내가 만든 레시피 목록 불러오기
class RecipeMyListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select r.id, r.title, r.percent , r.createdAt 
                    from recipe r
                    left join likeRecipe l
                    on r.id = l.recipeId
                    where r.userId= %s
                    group by r.id
                    order by ''' + order + '''  desc
                    limit ''' + offset + ''', '''+ limit + ''';'''

            record = (user_id, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)

            result_list = cursor.fetchall()

          

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
                
        # print(result_list)

        return {"result" : "success" ,
                "items" : result_list , 
                "count" : len(result_list)}, 200


#레시피 세부 선택
class RecipeResource(Resource):
    @jwt_required()
    def get(self,recipe_id) :
    

        try :
            connection = get_connection()

            query = '''select r.id, r.title, COUNT(l.userId) AS cnt, r.percent, a.alcoholType, r.userId,u.nickname, r.engTitle, r.intro, r.content, GROUP_CONCAT(DISTINCT ig.name SEPARATOR ', ') AS '재료'
                    FROM recipe r
                    LEFT JOIN likeRecipe l ON r.id = l.recipeId
                    LEFT JOIN recipeAlcohol ra ON r.id = ra.recipeId
                    LEFT JOIN alcohol a ON ra.AlcoholId = a.id
                    LEFT JOIN recipeIngredient ri ON ri.recipeId = r.id
                    LEFT JOIN ingredient ig ON ig.id = ri.ingredientId
                    LEFT JOIN users u on r.userId = u.id
                    where r.id = %s
                    group by l.recipeId 
                    order by count(l.userId) desc;'''

            record = (recipe_id, )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)
            
            result_list = cursor.fetchall()



            if result_list[0]['id'] is None:
                return {'error': '잘못된 알콜 아이디 입니다.'}, 400        

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
                
        # print(result_list)
        return { "result" : "success" ,
                "alcohol" : result_list[0] }, 200