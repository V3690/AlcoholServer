from flask import request 
from flask_restful import Resource 
from mysql_connection import get_connection
from mysql.connector import Error
from flask_jwt_extended import get_jwt, jwt_required, get_jwt_identity


## 메인 페이지 ##


class RecipeMasterListResource(Resource):

    # 유저가 오늘의 실험 페이지를 눌렀을 때, 레시피를 불러오는 api
    # 페이지는 2개의 리사이클러뷰에 보여줄 레시피를 불러온다.
    # 1.recipe 테이블의 id, title, imgUrl 컬럼을 반환할것
    # userId가 반드시 1인 레시피를 랜덤하게 불러온다 (마스터 id = 1)
    # 갯수는 쿼리스트링으로 받는 limit 값으로 한다
    # 불러온 레시피의 id, title, imgUrl을 리턴한다.
    @jwt_required()
    def get(self):
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = "SELECT id, title, imgUrl FROM recipe WHERE userId = 1 ORDER BY RAND() LIMIT " + offset + ", " + limit + ";"
            cursor.execute(query)
            rows = cursor.fetchall()
            return {'result' : 'success', 'items' : rows, 'count' : len(rows)}, 200
    
        except Error as e:
            return {'error' : str(e)}, 500
        finally:
            cursor.close()
            conn.close()

# 명예 레시피 리스트를 불러오는 api
# 최근 2주안의 좋아요를 가장 많이받은 레시피를 불러온다.
# 레시피의 id, imgUrl, likeCount를 반환한다.
# limit은 쿼리스트링으로 받는다.
class RecipeHonorListResource(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            query = """
            SELECT r.id, r.imgUrl, COUNT(l.recipeId) AS likeCount, if(lr.userId is null, 0 , 1) as isLike 
            FROM recipe r LEFT JOIN likeRecipe l 
            ON r.id = l.recipeId 
            LEFT JOIN likeRecipe lr
            ON r.id = lr.recipeId AND lr.userId = """ + str(user_id) + """
            WHERE DATE_SUB(CURDATE(), INTERVAL 2 WEEK) <= r.createdAt 
            GROUP BY r.id ORDER BY likeCount DESC 
            LIMIT """ + offset + ", " + limit + ";"
            # DATE_SUB(CURDATE(), INTERVAL 2 WEEK) <= r.createdAt GROUP BY r.id ORDER BY likeCount
            # 2. 현재시간에서 2주전보다 크거나 같은 레코드를 조회한다.
            # 3. recipe 테이블의 id를 기준으로 그룹핑한다.
            # 4. likeCount를 기준으로 내림차순 정렬한다.
            cursor.execute(query)
            rows = cursor.fetchall()
            return {'result' : 'success', 'items' : rows, 'count' : len(rows)}, 200
        except Error as e:
            return {'error' : str(e)}, 500
        finally:
            cursor.close()
            conn.close()



## 즐겨찾기 페이지 ##


# 즐겨찾기 레시피 리스트 (필터링)
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
        # order = 1 : 최신순
        # order = 2 : 인기순
        # type은 레시피의 타입이다.
        # type = 1 : 전체 레시피
        # type = 2 : 공식 레시피
        # type = 3 : 창작 레시피
        # strength는 레시피의 도수이다.
        # strength = 0 : 전체
        # strength = 1 : 약
        # strength = 2 : 중
        # strength = 3 : 강
        # strength = 4 : ?
        # limit은 불러올 레시피의 갯수이다.
        
        # 경우의 수는 2 * 3 * 5 = 30가지이다.
        # 즉, 24개의 쿼리문을 작성해야한다.
        # TODO : 이를 줄이는 방법은 쿼리스트링으로 받은 값들을 조합하여 쿼리문을 작성하는 것이다. (고민해봐야할듯)
        # 중복되는 값을 객체화 시키고, 
        # 반복되는 작업을 함수로 만들고, 
        # 정렬 알고리즘을 사용하여 쿼리문을 작성하는 방법이 있을것같다

        order = request.args.get('order')
        type = request.args.get('type')
        strength = request.args.get('strength')
        limit = request.args.get('limit')
        offset = request.args.get('offset')
        userId = get_jwt_identity()
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            # 정렬 기준이 최신순인 경우
            if order == '1':
                # 전체 레시피를 불러올 경우
                if type == '1':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """
                        ORDER BY r.createdAt DESC LIMIT """ + offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = """ + strength + """
                        ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
                # 공식 레시피를 불러올 경우
                elif type == '2':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l 
                        ON r.id = l.recipeId 
                        WHERE l.userId = """ + str(userId) + """ AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = """ + strength + """ AND r.userId = 1
                        ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
                # 창작 레시피를 불러올 경우
                elif type == '3':
                    # 전체 도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent
                        FROM recipe r LEFT JOIN likeRecipe l
                        ON r.id = l.recipeId
                        WHERE l.userId = """ + str(userId) + """ AND r.percent = """ + strength + """ AND r.userId != 1
                        ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
            # 정렬 기준이 인기순인 경우
            elif order == '2':
                # 전체 레시피를 불러올 경우
                if type == '1':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 
                        ON r.id = l1.recipeId and l1.userId = """ + str(userId) + """
                        left join likeRecipe l2
                        on r.id = l2.recipeId
                        WHERE l1.userId = """ + str(userId) + """
                        GROUP BY r.id, r.title, r.percent 
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 
                        ON r.id = l1.recipeId and l1.userId = """ + str(userId) + """
                        left join likeRecipe l2
                        on r.id = l2.recipeId
                        WHERE r.percent = """ + strength + """ and l1.userId = """ + str(userId) + """
                        GROUP BY r.id, r.title, r.percent 
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
                # 공식 레시피를 불러올 경우
                elif type == '2':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.userId = 1 and l1.userId = """ + str(userId) + """
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = """ + strength + """ AND r.userId = 1 and l1.userId = """ + str(userId) + """
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
                # 창작 레시피를 불러올 경우
                elif type == '3':
                    # 전체도수를 불러올 경우
                    if strength == '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.userId <> 1  and l1.userId = """ + str(userId) + """
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
                    if strength != '0':
                        query = """
                        SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
                        FROM recipe r 
                        LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(userId) + """
                        LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
                        WHERE r.percent = """ + strength + """ AND r.userId <> 1 and l1.userId = """ + str(userId) + """
                        GROUP BY r.id
                        ORDER BY likeCount DESC LIMIT """+ offset + ", " + limit + ";"
               
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

# 즐겨찾기 레시피 리스트 내에서 검색 (사용자가 입력한 키워드를 포함하는)
class RecipeLikeSearchResource(Resource):
    @jwt_required()
    def get(self):
         # 사용자가 입력한 키워드를 가져온다
        keyword = request.args.get('keyword')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        user_id = get_jwt_identity()
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            # 사용자가 입력한 키워드를 포함하는 레시피를 검색
            query = """
            SELECT r.id, r.title, r.percent, COUNT(l1.recipeId) AS likeCount
            FROM recipe r 
            LEFT JOIN likeRecipe l1 ON r.id = l1.recipeId AND l1.userId = """ + str(user_id) + """
            LEFT JOIN likeRecipe l2 ON r.id = l2.recipeId
            WHERE r.id IN (SELECT recipeId FROM likeRecipe WHERE userId = """ + str(user_id) + """ ) AND r.title LIKE '%""" + keyword + """%'
            GROUP BY r.id
            ORDER BY r.createdAt DESC LIMIT """+ offset + ", " + limit + ";"
            # 쿼리를 실행하고 결과를 저장   
            cursor.execute(query)
            result = cursor.fetchall()
            return {"result": result, "count" : len(result)}, 200
        
        except Exception as e:
            print(e)
            return ("errer" + str(e)), 500
        
        finally:
            conn.close()
            cursor.close()



## 레시피 메뉴 ##


# 레시피 목록 (공식)
class RecipeMasterallListResource(Resource):
    @jwt_required()
    def get(self) :
        # user_id = get_jwt_identity()
        percent = request.args.get('percent')
        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()

            if order == "cnt":
                order = "cnt desc"

            elif order == "createdAt":
                order = "r.createdAt desc"

            elif order == "title":
                order = "r.title asc"            

            if percent == "0":

                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId= 1
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''

            elif percent == "1":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId= 1 and percent = 1
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''
                
            elif percent == "2":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId= 1 and percent = 2
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''

            elif percent == "3":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId= 1 and percent = 3
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''   

            elif percent == "4":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId= 1 and percent = 4
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''                                             

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

# 레시피 목록 (창작)
class RecipeUserListResource(Resource):
    @jwt_required()
    def get(self) :
      



        # user_id = get_jwt_identity()
        percent = request.args.get('percent')
        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()

            if order == "cnt":
                order = "cnt desc"

            elif order == "createdAt":
                order = "r.createdAt desc"

            elif order == "title":
                order = "r.title asc"            

            if percent == "0":

                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId NOT IN(1)
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''
            elif percent == "1":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId NOT IN(1) and percent = 1
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''
                
            elif percent == "2":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId NOT IN(1) and percent = 2
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''

            elif percent == "3":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId NOT IN(1) and percent = 3
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''   

            elif percent == "4":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where r.userId NOT IN(1) and percent = 4
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};''' 

        
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

# 레시피 목록 (공식+창작)
class RecipeAllListResource(Resource):
    @jwt_required()
    def get(self) :
      



        # user_id = get_jwt_identity()
        percent = request.args.get('percent')
        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')

        try :
            connection = get_connection()

            if order == "cnt":
                order = "cnt desc"

            elif order == "createdAt":
                order = "r.createdAt desc"

            elif order == "title":
                order = "r.title asc"            

            if percent == "0":

                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''
            elif percent == "1":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where  percent = 1
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''
                
            elif percent == "2":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where percent = 2
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};'''

            elif percent == "3":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where percent = 3
                        group by r.id
                        order by  {order} ,r.percent desc
                        limit {limit} offset {offset};'''   

            elif percent == "4":
                query = f'''select r.id, r.title, r.percent , count(l.userId) as cnt
                        from recipe r
                        left join likeRecipe l
                        on r.id = l.recipeId
                        where percent = 4
                        group by r.id
                        order by  {order} , r.percent desc
                        limit {limit} offset {offset};''' 

        
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



## 내 레시피 관련
# 내 레시피 전체 리스트
class RecipeMyListAllResource(Resource):
    @jwt_required()
    def get(self) :
      
        user_id = get_jwt_identity()

        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select userId, id as recipeId ,title, percent , createdAt ,updatedAt
                    from recipe
                    where userId = %s
                    order by createdAt desc
                    limit ''' + offset + ''', '''+ limit + ''';'''


            record = (user_id, )
        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()

          

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i + 1

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
    

# 레시피 목록 (본인) - 도수 필터링
class RecipeMyListPercentResource(Resource):
    @jwt_required()
    def get(self) :
      
        user_id = get_jwt_identity()

        order = request.args.get('order')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select userId, id as recipeId ,title, percent , createdAt ,updatedAt
                    from recipe
                    where userId = %s and percent = ''' + order + '''
                    order by createdAt desc
                    limit ''' + offset + ''', '''+ limit + ''';'''


            record = (user_id, )
        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()

          

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i + 1

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
    
# 레시피 키워드로 가져오기 
class RecipeMyListKeywordResource(Resource):
    @jwt_required()
    def get(self) :
      
        user_id = get_jwt_identity()

        keyword = request.args.get('keyword')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        

        try :
            connection = get_connection()

            query = '''select userId,id as recipeId ,title, percent , createdAt ,updatedAt
                    from recipe
                    where userId = %s and title like "%''' +keyword+ '''%"
                    order by updatedAt desc;
                    limit ''' + offset + ''', '''+ limit + ''';'''


            record = (user_id, )
        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,record)

            result_list = cursor.fetchall()

          

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i + 1

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

# 레시피 1개 세부 정보
class RecipeResource(Resource):
    @jwt_required()
    def get(self,recipe_id) :
        user_id = get_jwt_identity()

        try :
            connection = get_connection()

            query = '''SELECT r.title, COUNT(DISTINCT l.userId) AS likeCnt, r.percent, a.alcoholType, u.nickname, r.engTitle, r.intro, r.content, r.imgUrl, GROUP_CONCAT(DISTINCT ig.name SEPARATOR ', ') AS ingredient, r.createdAt, r.updatedAt, r.userId, IF(lr.userId IS NULL, 0, 1) AS isLike
                    FROM recipe r
                    LEFT JOIN likeRecipe l ON r.id = l.recipeId
                    LEFT JOIN recipeAlcohol ra ON r.id = ra.recipeId
                    LEFT JOIN alcohol a ON ra.AlcoholId = a.id
                    LEFT JOIN recipeIngredient ri ON ri.recipeId = r.id
                    LEFT JOIN ingredient ig ON ig.id = ri.ingredientId
                    LEFT JOIN users u ON u.id = r.userId
                    LEFT JOIN likeRecipe lr ON lr.recipeId = r.id AND lr.userId = %s
                    WHERE r.id = %s
                    GROUP BY l.recipeId 
                    ORDER BY likeCnt DESC;;'''

            record = (user_id, recipe_id )
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query, record)
            
            result_list = cursor.fetchall()

            if result_list[0]['title'] is None:
                return {'error': '잘못된 알콜 아이디 입니다.'}, 400        
            
            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i + 1

            cursor.close()
            connection.close()
    
        except Error as e :
            print(e)            
            cursor.close()
            connection.close()
            return {"error" : str(e)}, 500
                
        # print(result_list)
        return { "recipeOne" : result_list[0] }, 200


#레시피 검색(레시피페이지에서)
class RecipeListKeywordResource(Resource):
    @jwt_required()
    def get(self) :
      
    

        keyword = request.args.get('keyword')
        offset = request.args.get('offset')
        limit = request.args.get('limit')
        type = request.args.get('type')

        try :
            connection = get_connection()

            if type == "0":
                type = "=1"
            elif type == "1":
                type = " not in (1)"
            elif type == "2":
                type = " >0"
           
            query = '''select userId,id ,title, percent , createdAt ,updatedAt
                    from recipe
                    where title like "%''' +keyword+ '''%" and userId'''+type+'''
                    order by updatedAt desc
                    limit ''' + offset + ''', '''+ limit + ''';'''


           
        
            cursor = connection.cursor(dictionary= True)
            cursor.execute(query,)

            result_list = cursor.fetchall()

          

            i = 0
            for row in result_list :
                result_list[i]['createdAt'] = row['createdAt'].isoformat()
                result_list[i]['updatedAt'] = row['updatedAt'].isoformat()
                i = i + 1

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






