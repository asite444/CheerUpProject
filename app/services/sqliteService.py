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



def extract_percentage(text):
    """ 문자열에서 자격 조건(%)과 우대 조건(%)을 추출하는 함수 """
    match = re.search(r'(\d+\.\d+)%.*?(\d+\.\d+)%', text)
    if match:
        return float(match.group(1)), float(match.group(2))
    return 0.0, 0.0  # 기본값

def generate_html_table_from_analysis(data, title="언어"):
    col_headers = ["순위", "이름", "자격 조건(%)", "우대 조건(%)", "설명"]

    html_output = f"""
    <h3>{html.escape(title)}</h3>
    <table id="analysis_top5">
        <tr>
    """

    for header in col_headers:
        html_output += f'<th scope="col">{html.escape(header)}</th>'
    html_output += '</tr>\n'

    for index, row in enumerate(data, start=1):
        name = html.escape(row[0])
        qualification = f"{row[1]:.2f}%" if isinstance(row[1], (int, float)) else "N/A"
        preference = f"{row[2]:.2f}%" if isinstance(row[2], (int, float)) else "N/A"
        description = html.escape("\n".join(row[3])) if len(row) > 3 else "설명 없음"

        html_output += f"""
        <tr>
            <td>{index}</td>
            <td>{name}</td>
            <td class="requirement high">{qualification}</td>
            <td class="preference very-high">{preference}</td>
            <td>{description}</td>
        </tr>
        """

    html_output += '</table>'
    return html_output


def analyze_stack_top5(user_data:UserInputData):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        
        query = """ 
        SELECT duty, it_language, framework, library, tool 
        FROM duty_analysis 
        WHERE duty IN ({})
        """.format(','.join(['?'] * len(user_data.jobs)))

        #print(f"Executing SQL query: {query}")  # 🟢 SQL 쿼리 확인
        cursor.execute(query, tuple(user_data.jobs))
        result = cursor.fetchall()

        #print(f"SQL Result Count: {len(result)}")  # 🟢 SQL 결과 개수 확인

        sections = {"언어": [], "프레임워크": [], "라이브러리": [], "툴": []}

        for row in result:
            try:
                #print(f"Processing row: {row}")  # 🟢 SQL 행 데이터 출력

                it_lang_list = ast.literal_eval(row[1]) if isinstance(row[1], str) else row[1] or []
                framework_list = ast.literal_eval(row[2]) if isinstance(row[2], str) else row[2] or []
                library_list = ast.literal_eval(row[3]) if isinstance(row[3], str) else row[3] or []
                tool_list = ast.literal_eval(row[4]) if isinstance(row[4], str) else row[4] or []

                #print(f"Parsed it_lang_list: {it_lang_list}")  # 🟢 데이터 변환 확인

                # 데이터 정리
                def parse_stack_data(stack_list):
                    parsed_data = []
                    for item in stack_list:
                        if isinstance(item, list) and len(item) == 2:  # 데이터가 ['Java (자격 조건: 47.02%, 우대 조건: 8.4%)', ['설명1', '설명2']] 형태인지 확인
                            name_raw, description_list = item
                            qualification, preference = extract_percentage(name_raw)  # 자격 조건과 우대 조건 추출
                            name = name_raw.split(" (자격 조건")[0]  # "Java" 부분만 추출
                            parsed_data.append((name, qualification, preference, description_list))
                    return parsed_data

                sections["언어"].extend(parse_stack_data(it_lang_list))
                sections["프레임워크"].extend(parse_stack_data(framework_list))
                sections["라이브러리"].extend(parse_stack_data(library_list))
                sections["툴"].extend(parse_stack_data(tool_list))

            except (SyntaxError, ValueError, IndexError) as e:
                print(f"Error converting career data: {row[0]}, Error: {str(e)}")

        # print(f"Sections filled: {sections}")  # 🟢 섹션에 데이터 추가 여부 확인

        top5_sections = {
            category: sorted(items, key=lambda x: x[1], reverse=True)[:5]
            for category, items in sections.items() if items
        }

        # print(f"Top 5 Sections: {top5_sections}")  # 🟢 최종 상위 5개 데이터 확인

        html_output = "".join(
            generate_html_table_from_analysis(items, category) for category, items in top5_sections.items()
        )

        return html_output

    except Exception as e:
        print("Error during SQL execution:", str(e))
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
                career_data = row[1].replace("/n", "")  # 백슬래시 문제 해결
                career_list = ast.literal_eval(career_data)  # 문자열을 리스트로 변환

                if career_list and isinstance(career_list, list):
                    img_path = career_list[0]  # 첫 번째 요소(이미지 경로)
                    graph_text = career_list[1]

                    # 숫자 목록("1. ", "2. ")을 기준으로 줄바꿈 유지 및 <div>로 감싸기
                    formatted_graph_text = "\n".join(
                        [f"<div>{line.strip()}</div>" for line in graph_text.splitlines() if line.strip()]
                    )

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