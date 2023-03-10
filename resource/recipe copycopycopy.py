from flask import request 
from flask_restful import Resource 
from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity




# 부재료 목록중 검색
class IngredientSearch(Resource):
    @jwt_required()
    def get(self):
    
        keyword = request.args.get('keyword')
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """select name
                    from ingredient
                    where name like '%""" + keyword + """%'
                    UNION
                    select name from alcohol
                    where name like
                    '%""" + keyword + """%'
                    ; """
            cursor.execute(query)
            result = cursor.fetchall()
            return {"result": result, "count" : len(result)}, 200
        
        except Exception as e:
            print(e)
            return ("errer" + str(e)), 500
        
        finally:
            conn.close()
            cursor.close()
        




#작성중 부재료 목록 가저오기
class recipeIngredient(Resource):
    @jwt_required()
    def get(self):
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        try :
            connection = get_connection()

            query = '''select name from ingredient
                        UNION
                        select name from alcohol
                        limit ''' + offset + ''', '''+ limit + ''';
                    '''

        
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
