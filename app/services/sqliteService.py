from app.database.sqliteserver import get_connection




def fetch_tech_stack():
    """
    tech_stack 테이블에서 데이터를 조회하는 함수.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT category, name FROM technical_element order by name asc;")
   
        results = cursor.fetchall()
        return [{"category": row[0], "name": row[1]} for row in results]
    except Exception as e:
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()


def category_search(search_request):
    """
    tech_stack 테이블에서 데이터를 조회하는 함수.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()

        # 동적 필터링을 위한 SQL 조건 생성
        query = """
        SELECT category, name 
        FROM technical_element 
        WHERE category = ? AND name LIKE ? 
        ORDER BY name ASC;
        """
        params = (
            search_request.category,
            f"%{search_request.keyword}%",  # 키워드를 부분 검색 형태로 적용
        )

        # 쿼리 디버깅용 출력 (SQLite에서는 mogrify 대신 수동 출력)
        print("Executing Query:", query.replace("?", "{}").format(*params))
        
        # SQL 실행
        cursor.execute(query, params)
        print('실행여기2')  # SQL 실행 후 출력
        
        # 결과 가져오기
        results = cursor.fetchall()
        print("Results:", results)  # 디버깅용 출력

        # 결과를 JSON 형태로 변환
        return [{"category": row[0], "name": row[1]} for row in results]
    except Exception as e:
        print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()
