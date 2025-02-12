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




def analyze_stack_top5(user_data: UserInputData):
    connection = get_connection()
    try:
        cursor = connection.cursor()

        # 카테고리 매핑 (SQL 쿼리에서 사용할 기술 카테고리를 설정)
        categories = {
            "언어": ("it_language", user_data.languages),
            "프레임워크": ("framework", user_data.frameworks),
            "라이브러리": ("library", user_data.libraries),
            "툴": ("tool", user_data.devtools),
        }

        # 기본적으로 '내용 없음'으로 초기화
        html_outputs = {
            "언어": "내용 없음",
            "프레임워크": "내용 없음",
            "라이브러리": "내용 없음",
            "툴": "내용 없음",
        }

        def generate_html_table(title, top5_data, extra_selected_data):
            """
            HTML 테이블을 생성하는 함수
            - top5_data: 상위 5개 기술 데이터
            - extra_selected_data: 사용자가 선택한 기술 중 5위 밖인 기술
            """
            if not top5_data and not extra_selected_data:
                return f"<h3>{title}</h3><p>데이터 없음</p>"

            # ⭐ 범례 추가
            html_output = f"""
            <p class="legend-right">⭐  사용자 선택 기술</p>
            <table class="analysis_top5">
                <tr>
                    <th>순위</th>
                    <th>기술명</th>
                    <th>자격 요건(%)</th>
                    <th>우대 사항(%)</th>
                </tr>
            """

            # 상위 5개 기술 출력 (사용자가 선택한 경우 강조)
            for skill, rank, probability, pre_probability in top5_data:
                highlight_class = "user-selected" if skill in (
                    user_data.languages + user_data.frameworks + user_data.libraries + user_data.devtools
                ) else "ranked"

                html_output += f"""
                <tr class="{highlight_class}">
                    <td>{rank}</td>
                    <td>{skill} {"⭐" if highlight_class == "user-selected" else ""}</td>
                    <td>{probability:.2f}%</td>
                    <td>{pre_probability:.2f}%</td>
                </tr>
                """

            # 사용자가 선택한 기술 중 최상위 순위를 가져옴
            extra_selected_data.sort(key=lambda x: x[1])  # 순위 기준 정렬
            first_selected_rank = extra_selected_data[0][1] if extra_selected_data else None

            # 중간 생략 문구 추가 (사용자가 선택한 기술이 7위 이상일 때만)
            if extra_selected_data and first_selected_rank and first_selected_rank >= 7:
                html_output += """
                <tr class="skipped">
                    <td colspan="4" style="text-align:center;">(중간 생략)</td>
                </tr>
                """

            # 사용자가 선택한 기술 중 5순위 밖인 경우 출력 (강조)
            for skill, rank, probability, pre_probability in extra_selected_data:
                html_output += f"""
                <tr class="user-selected">
                    <td>{rank}</td>
                    <td>{skill} ⭐</td>
                    <td>{probability:.2f}%</td>
                    <td>{pre_probability:.2f}%</td>
                </tr>
                """

            html_output += "</table>"
            return html_output

        # 각 카테고리에 대해 SQL 실행 및 결과 처리
        for display_name, (category, selected_skills) in categories.items():
            query = f"""
            WITH Ranked AS (
                SELECT
                    skill,
                    probability,
                    pre_probability,
                    RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC) AS rank
                FROM skill_probability
                WHERE category = ? AND duty IN ({','.join(['?'] * len(user_data.jobs))}) AND unit = 1
            )
            SELECT skill, rank, probability, pre_probability
            FROM Ranked
            ORDER BY rank
            """

            cursor.execute(query, (category, *user_data.jobs))
            result = cursor.fetchall()

            # 상위 5개 기술 추출
            top5_data = result[:5]

            # 사용자가 선택한 기술 중 5순위 밖인 기술 필터링
            extra_selected_data = [row for row in result if row[0] in selected_skills and row not in top5_data]

            # HTML 테이블 생성
            html_outputs[display_name] = generate_html_table(display_name, top5_data, extra_selected_data)

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