from app.models.user_input_data import UserInputData
from app.database.sqliteserver import get_connection

import os
import ast
import pandas as pd

from openai import OpenAI
from dotenv import load_dotenv

def get_api_key():
    # 프로젝트 루트의 .env 파일을 로드 (web/.env)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    load_dotenv(dotenv_path)

    # 환경 변수에서 API_KEY 가져오기
    API_KEY = os.getenv("CHATGPT_API_KEY")
    return API_KEY

def get_openai_response(prompt, model='gpt-3.5-turbo', temperature=0.5):
    # ChatGPT API를 이용용
    client = OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "당신은 IT 전문가입니다. 주어진 질문에 모두 답하세요."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def analyze_customize(user_data:UserInputData):
    duty = user_data.jobs[0]
    it_language = sorted(user_data.languages)
    framework = sorted(user_data.frameworks)
    library = sorted(user_data.libraries)
    tool = sorted(user_data.devtools)
    categories = {'it_language': ['언어', it_language], 'framework': ['프레임워크', framework], 'library': ['라이브러리', library], 'tool': ['툴', tool]}

    data = get_customized_analysis(duty, it_language, framework, library, tool)
    print(data)
    if data is None:
        # DB에 분석 결과가 없음
        improvement_reulst = improvement(duty, categories)
        # report_conclusion = analyze_conclusion(duty, data)

    report_improvement = get_improvement_html(improvement_reulst) # get_improvement_html(improvement_reulst)
    # report_conclusion = data[2]

    return report_improvement


def get_customized_analysis(duty, it_language, framework, library, tool):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        query = '''
                SELECT
                        improvement, conclusion
                FROM
                        customized_analysis
                WHERE
                        duty = ? AND it_language = ? AND framework = ? AND library = ? AND tool = ?
        '''
        purchases = (duty, ', '.join(it_language), ', '.join(framework), ', '.join(library), ', '.join(tool), )
        cursor.execute(query, purchases)
        return cursor.fetchone()
    except Exception as e:
        return 'get customized analysis error: ' + e
    finally:
        if connection:
            connection.close()

def insert_customized_analysis(duty, it_language, framework, library, tool):
    connection = get_connection()
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(seq) FROM customized_analysis ')
        data = cursor.fetchone()[0]
        seq = data + 1 if data is not None else 0
        
        query = """
                INSERT INTO
                customized_analysis
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?)
        """
        purchases = (seq, ', '.join(it_language), ', '.join(framework), ', '.join(library), ', '.join(tool), report, '2025.02.06', duty, )
        cursor.execute(query, purchases)
        return cursor.fetchone()
    except Exception as e:
        return 'insert_customized analysis error: ' + e
    finally:
        if connection:
            connection.close()

def find_matching_text(skill_value, res_eval):
    for key, text in res_eval.items():
        if all(k in skill_value for k in key.split(", ")):  # key의 모든 스킬이 포함되면 매칭
            return text
    return ""  # 매칭되는 키가 없으면 빈 문자열 반환

def improvement(duty, categories):
    # 보완사항
    connection = get_connection()

    try:
        result = dict()
        for category in categories.keys():
            combination_df = get_skill_combination(duty, category, categories[category][0])

            prompt = make_improvement_prompt(duty, combination_df)

            response = get_openai_response(prompt)
            try:
                res_eval = ast.literal_eval(response)
                print(res_eval)
                combination_df["text"] = combination_df["skill"].apply(find_matching_text, args=(res_eval, ))
            except SyntaxError as e:
                return print('literal_eval error: ' + str(e))
            except Exception as e:
                print(e)

            result[categories[category][0]] = combination_df.to_dict()
        print(result)

        return result
    except Exception as e:
        return 'get_skill_prob_rank error' + e
    finally:
        if connection:
            connection.close()

def get_skill_combination(duty, category, user_skill, limit=2, probability=0.05):
    connection = get_connection()

    try:
        query = """
            WITH Ranked AS (
                SELECT
                    skill,
                    probability,
                    RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC, skill ASC) AS rank
                FROM skill_probability
                WHERE category = ?
                AND duty = ?
                AND unit = 1
                ORDER BY rank
                LIMIT ?
            ),
            Filtered AS (
                SELECT
                    sp.skill,
                    sp.probability,
                    sp.pre_probability,
                    r.skill AS rskill,
                    r.probability AS rprobability,
                    r.rank AS rrank,
                    ROW_NUMBER() OVER (PARTITION BY r.rank ORDER BY sp.probability DESC, sp.pre_probability DESC) AS rn
                FROM skill_probability sp
                RIGHT OUTER JOIN Ranked r 
                    ON sp.skill LIKE '%' || r.skill || '%'
                WHERE sp.category = ?
                AND sp.duty = ?
                AND sp.unit > 1
                AND sp.probability >= ?
                AND sp.pre_probability != 0
                AND sp.skill NOT IN (?)
            )
            SELECT skill, probability, rskill, rprobability, rrank
            FROM Filtered
            WHERE rn <= 2  -- rrank별로 최대 2개 선택
            ORDER BY rrank, probability DESC;
        """
        purchases = (category, duty, limit, category, duty, probability, ', '.join(user_skill), )
        data = pd.read_sql_query(query, connection, params=purchases)
        return data
    except Exception as e:
        return 'skill_combination error ' + str(e)
    finally:
        if connection:
            connection.close()

def make_improvement_prompt(duty, combination):
    """ 보완사항에 대한 프롬프트 작성 """
    prompt = f'''다음 스킬 조합을 "{duty}"에 지원하는 사람에게 추천하는 이유를 JSON 딕셔너리 형식으로 감싸서 반환하세요.
반드시 "JSON 형식"을 따르며 키는 스킬 조합, 값은 "조합끼리의 시너지 효과(50자 이내)"의 형태여야 하며 본론만 말하세요.'''
    
    prompt += '(예시: {"c#, c++, java, rust": "성능 최적화, 메모리 관리, 네트워크 프로그래밍에 강점을 가짐"}): '

    # 중괄호 이슈 해결 및 리스트 변환
    skills = list(combination['skill'])  # Pandas Series가 아닐 경우 to_list() 필요 없음
    skill_str = ', '.join(f'"{item}"' for item in skills)
    print("skill_str:"+f'{{{skill_str}}}')
    prompt += f'{{{skill_str}}}'
    
    return prompt

def get_improvement_html(data_dict):
    columns = {'skill': '기술 조합', 'probability': '자격조건(%)', 'text': '설명'}
    html_content = ""

    for category, values in data_dict.items():
        # ✅ 데이터가 없는 카테고리는 건너뛰기
        if not values or not any(values.values()):
            print(f"⚠️ Warning: {category} 데이터 없음, 건너뜀")
            continue  # 데이터 없는 카테고리 생략

        html_content += f"<h2>{category}</h2>\n"
        
        rskill_groups = {}
        
        # ✅ rskill 데이터가 없을 경우 방어 코드 추가
        if "rskill" not in values or not values["rskill"]:
            html_content += "<p>데이터 없음</p>\n"
            continue

        # ✅ rskill별 그룹 생성
        for i in range(len(values["rskill"])):
            rskill = values["rskill"][i]
            if rskill not in rskill_groups:
                rskill_groups[rskill] = {col: {} for col in columns.keys()}
            
            for col in columns.keys():
                rskill_groups[rskill][col][len(rskill_groups[rskill][col])] = values[col][i]

        # ✅ rskill 그룹이 없으면 데이터 없음 메시지 출력
        if not rskill_groups:
            html_content += "<p>데이터 없음</p>\n"
            continue

        # ✅ rskill별 테이블 생성
        for rskill, rvalues in rskill_groups.items():
            html_content += f"<h3>{rskill} 관련 기술</h3>\n"
            html_content += "<table border='1'>\n"

            # ✅ 테이블 헤더 생성
            headers = [columns[col] for col in columns.keys()]
            html_content += "<tr>" + "".join(f"<th>{col}</th>" for col in headers) + "</tr>\n"

            # ✅ rvalues 데이터 확인
            if not any(rvalues.values()):
                html_content += "<tr><td colspan='3'>데이터 없음</td></tr>\n"
            else:
                # ✅ 행 생성
                num_rows = len(next(iter(rvalues.values())))
                for i in range(num_rows):
                    html_content += "<tr>" + "".join(
                        f"<td>{rvalues[col].get(i, '데이터 없음')}</td>" for col in columns.keys()
                    ) + "</tr>\n"

            html_content += "</table>\n<br>\n"

    return html_content


def analyze_conclusion(duty, data):
    """결론"""
    prompt = f'''기술 스택을 기반으로 {duty} 직무에 대한 최종 결론을 350자 이내로 출력해주세요.
    - 설명형 어투로 구체적으로 작성할 것
    - 보유 기술이 {duty} 직무에서 어떻게 활용되는지 설명할 것.
    - 부족한 기술이 실무에서 왜 중요한지, 이를 학습하면 어떤 장점이 있는지 설명할 것.
    - 마지막에는 응원하는 메시지를 포함할 것.  
    - 기술 스택의 순위는 {duty} 직무 공고에서 기술 스택이 나온 순위임.
    기술스택: ['''
    for i in data[0]:
        prompt += f'{i[0]}:['
        for j in i[1:]:
            prompt += f'''{j[0]}({j[1]}위),'''
        prompt += '],'

    prompt += f''']
    부족한 기술: ['''
    for i in data[1]:
        prompt += f'{i[0]}:['
        for j in i[1:]:
            prompt += f'''{j[0]},'''
        prompt += '],'
    prompt += ']'

    response = get_openai_response(prompt)
        
    return response