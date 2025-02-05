from app.database.sqliteserver import get_connection
from app.models.user_input_data import UserInputData 
import ast


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
        where name !='언어별 개발자'
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


def career_graph_search(user_data: UserInputData):
    """
    사용자가 선택한 직무(jobs)에 해당하는 career 데이터를 조회하여 HTML <img> 태그를 생성
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # SQL Query 실행
        query = """
        SELECT duty,career FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # career 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                # career 컬럼이 문자열 리스트로 저장되어 있으므로 변환
                career_list = ast.literal_eval(row[1])  # 문자열을 실제 리스트로 변환
                duty_list=row[0]
                if career_list and isinstance(career_list, list):
                    img_path = career_list[0]  # career 리스트에서 첫 번째 요소(이미지 경로)
                    graph_text=career_list[1]
                    img_tag = f'''
                                <figure>
                    <h3>{duty_list}</h3>
                    <div class="content-wrapper">
                        <img class="fit-picture" src="..\\static\\image\\{img_path}" alt="경력 분석 이미지" />
                        <figcaption>
                            {graph_text}
                        </figcaption>
                    </div>
                </figure>
                   
                    '''
                    img_tags.append(img_tag)  # 생성된 <img> 태그 추가
            except (SyntaxError, ValueError) as e:
                print(f"Error converting career data: {row[0]}, Error: {str(e)}")

        return img_tags  # HTML <img> 태그 리스트 반환

    except Exception as e:
        print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}
    
    finally:
        if connection:
            connection.close()  # DB 연결 종료

def degree_graph_search(user_data: UserInputData):
    """
    사용자가 선택한 직무(jobs)에 해당하는 degree 데이터를 조회하여 HTML <img> 태그를 생성
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # SQL Query 실행
        query = """
        SELECT duty,degree FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # degree 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                # degree 컬럼이 문자열 리스트로 저장되어 있으므로 변환
                degree_list = ast.literal_eval(row[1])  # 문자열을 실제 리스트로 변환
                duty_list=row[0]
                if degree_list and isinstance(degree_list, list):
                    img_path = degree_list[0]  # degree 리스트에서 첫 번째 요소(이미지 경로)
                    graph_text=degree_list[1]
                    img_tag = f'''
                                <figure>
                    <h3>{duty_list}</h3>
                    <div class="content-wrapper">
                        <img class="fit-picture" src="..\\static\\image\\{img_path}" alt="학력 분석 이미지" />
                        <figcaption>
                            {graph_text} 
                        </figcaption>
                    </div>
                </figure>
                   
                    '''
                    img_tags.append(img_tag)  # 생성된 <img> 태그 추가
            except (SyntaxError, ValueError) as e:
                print(f"Error converting degree data: {row[0]}, Error: {str(e)}")

        return img_tags  # HTML <img> 태그 리스트 반환

    except Exception as e:
        print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}
    
    finally:
        if connection:
            connection.close()  # DB 연결 종료




def language_graph_search(user_data: UserInputData):
    """
    사용자가 선택한 직무(jobs)에 해당하는 language 데이터를 조회하여 HTML <img> 태그를 생성
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # SQL Query 실행
        query = """
        SELECT duty,language FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # career 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                # career 컬럼이 문자열 리스트로 저장되어 있으므로 변환
                language_list = ast.literal_eval(row[1])  # 문자열을 실제 리스트로 변환
                duty_list=row[0]
                if language_list and isinstance(language_list, list):
                    img_path = language_list[0]  # language 리스트에서 첫 번째 요소(이미지 경로)
                    graph_text=language_list[1]
                    img_tag = f'''
                                <figure>
                    <h3>{duty_list}</h3>
                    <div class="content-wrapper">
                        <img class="fit-picture" src="..\\static\\image\\{img_path}" alt="어학 분석 이미지" />
                        <figcaption>
                            {graph_text}
                        </figcaption>
                    </div>
                </figure>
                   
                    '''
                    img_tags.append(img_tag)  # 생성된 <img> 태그 추가
            except (SyntaxError, ValueError) as e:
                print(f"Error converting language data: {row[0]}, Error: {str(e)}")

        return img_tags  # HTML <img> 태그 리스트 반환

    except Exception as e:
        print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}
    
    finally:
        if connection:
            connection.close()  # DB 연결 종료

