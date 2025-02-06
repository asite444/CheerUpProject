from app.database.sqliteserver import get_connection
from app.models.user_input_data import UserInputData 
import ast
import html
import re 

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


def analyze_stack_top5(user_data: UserInputData):
    """
    top5 불러오기
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # SQL Query 실행
        query = """ 
        SELECT duty, it_language, framework, library, tool 
        FROM duty_analysis 
        WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, tuple(user_data.jobs))  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # career 데이터 가져오기
        
        sections = {"언어": [], "프레임워크": [], "라이브러리": [], "툴": []}
        
        for row in result:
            try:
                # 데이터 변환
                it_lang_list = ast.literal_eval(row[1]) if isinstance(row[1], str) else row[1] or []
                framework_list = ast.literal_eval(row[2]) if isinstance(row[2], str) else row[2] or []
                library_list = ast.literal_eval(row[3]) if isinstance(row[3], str) else row[3] or []
                tool_list = ast.literal_eval(row[4]) if isinstance(row[4], str) else row[4] or []

                # 각 카테고리에 데이터 추가
                sections["언어"].extend(it_lang_list)
                sections["프레임워크"].extend(framework_list)
                sections["라이브러리"].extend(library_list)
                sections["툴"].extend(tool_list)
            
            except (SyntaxError, ValueError) as e:
                print(f"Error converting career data: {row[0]}, Error: {str(e)}")

        # HTML 변환
        html_output = "".join(
            f"""
            <h2>{html.escape(category)}</h2>
            <ol>
                {''.join(
                    f'''
                    <li>
                        <strong>{html.escape(item[0])}</strong>
                        <p>{html.escape(item[1][0])}</p>
                        <p>{html.escape(item[1][1])}</p>
                    </li>
                    ''' if isinstance(item, list) and len(item) == 2 and isinstance(item[1], list) and len(item[1]) == 2
                    else f'<li>{html.escape(str(item))}</li>'
                for item in items)}
            </ol>
            """ for category, items in sections.items() if items
        )

       
        return html_output

    except Exception as e:
        print("Error during SQL execution:", str(e))  # 에러 내용 출력
        return {"error": str(e)}
    
    finally:
        if connection:
            connection.close()  # DB 연결 종료

def career_graph_search(user_data: UserInputData):
    """
    사용자가 선택한 직무(jobs)에 해당하는 career 데이터를 조회하여 HTML <img> 태그를 생성
    """
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        # SQL Query 실행
        query = """
        SELECT duty, career FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # career 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                duty_list = row[0]
                
                # 데이터가 문자열 형태라면 변환
                career_data = row[1].replace("\\", "/")  # 백슬래시 문제 해결
                career_list = ast.literal_eval(career_data)  # 문자열을 리스트로 변환

                if career_list and isinstance(career_list, list):
                    img_path = career_list[0]  # 첫 번째 요소(이미지 경로)
                    graph_text = career_list[1]

                    # 숫자 목록("1. ", "2. ")의 공백을 제거하여 줄바꿈 방지
                    formatted_graph_text = re.sub(r"(\d+)\.\s+", r"\1.", graph_text)

                    # 목록 기호 `-` 앞에 줄바꿈 추가
                    formatted_graph_text = re.sub(r"- ", "</div><div>- ", formatted_graph_text)

                    # HTML 태그 적용 (문장별 <div> 처리)
                    formatted_graph_text = "<div>" + formatted_graph_text.replace(". ", ".</div><div>") + "</div>"

                    # HTML 태그 생성
                    img_tag = f'''
                    <figure>
                        <h3>{html.escape(duty_list)}</h3>
                        <div class="content-wrapper">
                            <img class="fit-picture" src="..\\static\\image\\{html.escape(img_path)}" alt="경력 분석 이미지" />
                            <figcaption class="analysis-text">
                                {formatted_graph_text}
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
        SELECT duty, degree FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # degree 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                duty_list = row[0]
                
                # 데이터가 문자열 형태라면 변환
                degree_data = row[1].replace("\\", "/")  # 백슬래시 문제 해결
                degree_list = ast.literal_eval(degree_data)  # 문자열을 리스트로 변환

                if degree_list and isinstance(degree_list, list):
                    img_path = degree_list[0]  # 첫 번째 요소(이미지 경로)
                    graph_text = degree_list[1]

                    # 숫자 목록("1. ", "2. ")의 공백을 제거하여 줄바꿈 방지
                    formatted_graph_text = re.sub(r"(\d+)\.\s+", r"\1.", graph_text)

                    # HTML 태그 적용 (문장별 <div> 처리)
                    formatted_graph_text = "<div>" + formatted_graph_text.replace(". ", ".</div><div>") + "</div>"

                    # HTML 태그 생성
                    img_tag = f'''
                    <figure>
                        <h3>{html.escape(duty_list)}</h3>
                        <div class="content-wrapper">
                            <img class="fit-picture" src="..\\static\\image\\{html.escape(img_path)}" alt="학력 분석 이미지" />
                            <figcaption class="analysis-text">
                                {formatted_graph_text}
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
        SELECT duty, language FROM duty_analysis WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))  # 다중 직무 검색을 위한 플레이스홀더

        cursor.execute(query, user_data.jobs)  # 사용자의 직무 리스트 바인딩
        result = cursor.fetchall()  # language 데이터 가져오기
        
        img_tags = []  # HTML <img> 태그 리스트
        for row in result:
            try:
                duty_list = row[0]
                
                # 데이터가 문자열 형태라면 변환
                language_data = row[1].replace("\\", "/")  # 백슬래시 문제 해결
                language_list = ast.literal_eval(language_data)  # 문자열을 리스트로 변환

                if language_list and isinstance(language_list, list):
                    img_path = language_list[0]  # 첫 번째 요소(이미지 경로)
                    graph_text = language_list[1]

                    # 숫자 목록("1. ", "2. ")의 공백을 제거하여 줄바꿈 방지
                    formatted_graph_text = re.sub(r"(\d+)\.\s+", r"\1.", graph_text)

                    # HTML 태그 적용 (문장별 <div> 처리)
                    formatted_graph_text = "<div>" + formatted_graph_text.replace(". ", ".</div><div>") + "</div>"

                    # HTML 태그 생성
                    img_tag = f'''
                    <figure>
                        <h3>{html.escape(duty_list)}</h3>
                        <div class="content-wrapper">
                            <img class="fit-picture" src="..\\static\\image\\{html.escape(img_path)}" alt="어학 분석 이미지" />
                            <figcaption class="analysis-text">
                                {formatted_graph_text}
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