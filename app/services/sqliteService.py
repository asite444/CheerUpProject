from app.database.sqliteserver import get_connection
from app.models.user_input_data import UserInputData 



def fetch_tech_stack():
    """
    tech_stack 테이블에서 데이터를 조회하는 함수.
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()

        query = """
        SELECT category, name FROM technical_element 
        UNION ALL
        select 'job' as category,name FROM duty_element
        ORDER BY name
        """


        cursor.execute(query)
   
        results = cursor.fetchall()
        return [{"category": row[0], "name": row[1]} for row in results]
    except Exception as e:
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()

def is_existing_tech_stack(user_data: UserInputData):
    """
    사용자가 이전에 선택한 기술 스택인지 검색하는 함수(수정예정)
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
        SELECT text FROM customized_analysis
        WHERE job         = ? 
          AND it_language = ? 
          AND framework   = ? 
          AND library     = ? 
          AND tool        = ? 
        """

        # 리스트를 문자열로 변환하여 SQL 바인딩
        params = (
            ','.join(user_data.jobs) if isinstance(user_data.jobs, list) else user_data.jobs,
            ','.join(user_data.languages) if isinstance(user_data.languages, list) else user_data.languages,
            ','.join(user_data.frameworks) if isinstance(user_data.frameworks, list) else user_data.frameworks,
            ','.join(user_data.libraries) if isinstance(user_data.libraries, list) else user_data.libraries,
            ','.join(user_data.devtools) if isinstance(user_data.devtools, list) else user_data.devtools
        )

        print("SQL 실행 전 데이터 확인:", params)  # 디버깅용

        # SQL 실행
        cursor.execute(query, params)
        results = cursor.fetchall()
        print("Results:", results)  # 디버깅용 출력

        if results:
            # 결과가 있는 경우 첫 번째 결과의 text 값을 가져와 반환
            return True, results[0][0]  # `True`와 `text` 값 반환
        else:
            return False, None  # 결과가 없을 경우 `False`와 `None` 반환

    except Exception as e:
        # print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}

    finally:
        if connection:
            connection.close()




def category_search(search_request):
    """
    tech_stack 테이블에서 데이터를 조회하는 함수.(사용안함)
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
