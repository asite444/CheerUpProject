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





def analyze_stack_top5(user_data:UserInputData):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        query = """ 
        SELECT *
        FROM skill_probability 
        WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))

   
        cursor.execute(query, tuple(user_data.jobs))
        result = cursor.fetchall()


      
        for row in result:
            try:
               print()

            except (SyntaxError, ValueError, IndexError) as e:
                print(f"Error converting career data: {row[0]}, Error: {str(e)}")


        html_outputs = {
            "언어":  "언어 내용",
            "프레임워크":"프레임워크 내용",
            "라이브러리": "라이브러리 내용",
            "툴": "툴 내용",
        }

        return html_outputs

    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
    
    finally:
        if connection:
            connection.close()


def career_graph_search(user_data:UserInputData):
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
                career_data = row[1].replace("/n", "")  # 개행 문제 해결
                career_list = ast.literal_eval(career_data)  # 문자열을 리스트로 변환

                if career_list and isinstance(career_list, list):
                    img_path = career_list[0]  # 첫 번째 요소(이미지 경로)
                    graph_text = career_list[1]

                    # 숫자(예: "1. ", "2. ")를 제거하고 <li> 태그로 변환
                    formatted_list = [
                        f"<li>{line.split('. ', 1)[-1].strip()}</li>"
                        for line in graph_text.splitlines()
                        if line.strip()
                    ]
                    formatted_graph_text = f"<ul>{''.join(formatted_list)}</ul>"

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



def degree_graph_search(user_data:UserInputData):
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

                    # '-' 기호 제거 후 문장을 분리 (마침표 '. ' 또는 '- ' 기준)
                    sentences = re.split(r'(?<!\d)\.\s+|- ', graph_text)
                    
                    # <li> 태그 적용
                    formatted_list = [
                        f"<li>{sentence.strip()}</li>"
                        for sentence in sentences
                        if sentence.strip()
                    ]
                    formatted_graph_text = f"<ul>{''.join(formatted_list)}</ul>"

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


                    # 숫자+점(".") 뒤에 공백이 오는 패턴을 찾아 분리
                    formatted_list = [
                        f"<li>{sentence.strip()}</li>"
                        for sentence in re.split(r'\d+\.\s+', graph_text)  # 숫자+점(". ")로 분리
                        if sentence.strip()  # 빈 문장 제외
                    ]
                    formatted_graph_text = f"<ul>{''.join(formatted_list)}</ul>"

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