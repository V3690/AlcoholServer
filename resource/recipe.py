from flask import request 
from flask_restful import Resource 
from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity

class RecipeMasterListResource(Resource):

    # 유저가 오늘의 실험 페이지를 눌렀을 때, 레시피를 불러오는 api
    # 페이지는 2개의 리사이클러뷰에 보여줄 레시피를 불러온다.
    # 1.recipe 테이블의 id, title, imgUrl 컬럼을 반환할것
    # userId가 반드시 1인 레시피를 랜덤하게 불러온다 (마스터 id = 1)
    # 갯수는 쿼리스트링으로 받는 limit 값으로 한다
    # 불러온 레시피의 id, title, imgUrl을 리턴한다.
    @jwt_required()
    def get(self):
        limit = request.args.get('limit')
        print(limit)
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT id, title, imgUrl FROM recipe WHERE userId = 1 ORDER BY RAND() LIMIT " + limit + ";"
            cursor.execute(query)
            rows = cursor.fetchall()
            return {'result' : 'success', 'items' : rows, 'count' : len(rows)}, 200
        except Error as e:
            print(e)
            return {'error' : str(e)}, 500
        finally:
            cursor.close()
            conn.close()


# 명예 레시피 리스트를 불러오는 api
# 최근 2주안의 좋아요를 가장 많이받은 레시피를 불러온다.
# 레시피의 id, imgUrl, likeCount를 반환한다.
# 레시피의 likeCount를 기준으로 내림차순 정렬한다.
# limit은 쿼리스트링으로 받는다.
class RecipeHonorListResource(Resource):
    @jwt_required()
    def get(self):
        limit = request.args.get('limit')
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT r.id, r.imgUrl, COUNT(l.recipeId) AS likeCount
            FROM recipe r LEFT JOIN likeRecipe l 
            ON r.id = l.recipeId 
            WHERE DATE_SUB(CURDATE(), INTERVAL 2 WEEK) <= r.createdAt 
            GROUP BY r.id ORDER BY likeCount DESC 
            LIMIT """ + limit + ";"
            # DATE_SUB(CURDATE(), INTERVAL 2 WEEK) <= r.createdAt GROUP BY r.id ORDER BY likeCount
            # 2. 현재시간에서 2주전보다 크거나 같은 레코드를 조회한다.
            # 3. recipe 테이블의 id를 기준으로 그룹핑한다.
            # 4. likeCount를 기준으로 내림차순 정렬한다.
            cursor.execute(query)
            rows = cursor.fetchall()
            return {'result' : 'success', 'items' : rows, 'count' : len(rows)}, 200
        except Error as e:
            print(e)
            return {'error' : str(e)}, 500
        finally:
            cursor.close()
            conn.close()


# 내가 좋아요한 레시피 리스트를 불러오는 api
class RecipeLikeListResource(Resource):
    # 리스트는 정렬 기준이 여러개있다 
    # 1.(최신순, 인기순)
    # 2.전체레시피, 공식레시피(userId == 1인경우), 창작레시피(userId != 1인경우)
    # 3.도수 약,중,강,?

    # 보여줄 레시피의 id, title, percent 를 반환한다.
    # percent는 레시피의 도수를 나타낸다.

    # 테스트를 위해 jieun_db.recipe 테이블에 percent 컬럼에 1~100까지의 값을 랜덤으로 넣어놓았다.
    # UPDATE recipe SET percent = FLOOR(RAND() * 4) + 1;
    # FLOOR(RAND() * 4) + 1 : 1~4까지의 랜덤한 숫자를 반환한다. +1을 해주는 이유는 0이 나올 수 있기 때문이다.
    # FLOOR() : 소수점 이하를 버린다.
    # RAND() : 0~1 사이의 랜덤한 숫자를 반환한다.
    
    @jwt_required()
    def get(self):
        # 쿼리스트링으로 받은 값들을 변수에 저장한다.
        # sort는 정렬 기준이다.
        # sort = 1 : 최신순
        # sort = 2 : 인기순
        # type은 레시피의 타입이다.
        # type = 1 : 전체 레시피
        # type = 2 : 공식 레시피
        # type = 3 : 창작 레시피
        # strength는 레시피의 도수이다.
        # strength = 1 : 약
        # strength = 2 : 중
        # strength = 3 : 강
        # strength = 4 : ?
        # limit은 불러올 레시피의 갯수이다.
        
        # 경우의 수는 2 * 3 * 4 = 24가지이다.
        # 즉, 24개의 쿼리문을 작성해야한다.
        # TODO : 이를 줄이는 방법은 쿼리스트링으로 받은 값들을 조합하여 쿼리문을 작성하는 것이다. (고민해봐야할듯)
        # 중복되는 값을 객체화 시키고, 
        # 반복되는 작업을 함수로 만들고, 
        # 정렬 알고리즘을 사용하여 쿼리문을 작성하는 방법이 있을것같다

        sort = request.args.get('sort')
        type = request.args.get('type')
        strength = request.args.get('strength')
        limit = request.args.get('limit')
        userId = get_jwt_identity()
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            # 정렬 기준이 최신순인 경우
            if sort == '1':
                # 전체 레시피를 불러올 경우
                if type == '1':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 1 
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 2 
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 3 
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent >= 4 
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                # 공식 레시피를 불러올 경우
                elif type == '2':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 1 AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 2 AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 3 AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 4 AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                # 창작 레시피를 불러올 경우
                elif type == '3':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 1 AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 2 AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 3 AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = 4 AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """ + limit + ";"
            # 정렬 기준이 인기순인 경우
            elif sort == '2':
                # 전체 레시피를 불러올 경우
                if type == '1':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent <= 1
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";" 
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent <= 2
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";" 
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                       SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent <= 3
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";" 
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent <= 4
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";" 
                # 공식 레시피를 불러올 경우
                elif type == '2':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.userId = 1  and r.userId = 1
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 1 AND r.userId = 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 2 AND r.userId = 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 3 AND r.userId = 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 4 AND r.userId = 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                # 창작 레시피를 불러올 경우
                elif type == '3':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.userId <> 1 
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 약인 경우
                    if strength == '1':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 1 AND r.userId <> 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 중인 경우
                    elif strength == '2':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 2 AND r.userId <> 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 강인 경우
                    elif strength == '3':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 3 AND r.userId <> 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"
                    # 도수가 ?인 경우
                    elif strength == '4':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = 4 AND r.userId <> 1  
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """ + limit + ";"

            # 쿼리를 실행하고 결과를 저장
            cursor.execute(query)
            result = cursor.fetchall()
            return {"result": result, "count" : len(result)}

        except Exception as e:
            print(e)
            return ("errer" + str(e))
        
        finally:
            conn.close()
            cursor.close()











































