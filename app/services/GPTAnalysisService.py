from app.models.user_input_data import UserInputData
from app.database.sqliteserver import get_connection

import os
import ast
import pandas as pd
import numpy as np
from datetime import datetime

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
    categories = {'it_language': ['언어', sorted(user_data.languages)],
                  'framework': ['프레임워크', sorted(user_data.frameworks)],
                  'library': ['라이브러리', sorted(user_data.libraries)],
                  'tool': ['툴', sorted(user_data.devtools)]}

    data = get_customized_analysis(duty, categories)
    if data is None:
        # DB에 분석 결과가 없음
        improvement_reulst = analyze_improvement(duty, categories)
        report_conclusion = analyze_conclusion(user_data)
        set_customized_analysis(duty, categories, improvement_reulst, report_conclusion)
    else:
        improvement_reulst = ast.literal_eval(data[0])
        report_conclusion = data[1]

    report_improvement = get_improvement_html(improvement_reulst)

    return report_improvement, report_conclusion

def get_customized_analysis(duty, categories):
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
        purchases = (duty, ', '.join(categories['it_language'][1]), ', '.join(categories['framework'][1]), ', '.join(categories['library'][1]), ', '.join(categories['tool'][1]), )
        cursor.execute(query, purchases)
        return cursor.fetchone()
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()

def set_customized_analysis(duty, categories, improvement, conclusion):
    connection = get_connection()
    
    try:
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(seq) FROM customized_analysis')
        data = cursor.fetchone()[0]
        seq = data + 1 if data is not None else 0
        
        query = """
                INSERT INTO
                customized_analysis
                (seq, duty, it_language, framework, library, tool, improvement, conclusion, an_dt)
                VALUES
                (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        purchases = (seq, duty, ', '.join(categories['it_language'][1]), ', '.join(categories['framework'][1]), ', '.join(categories['library'][1]), ', '.join(categories['tool'][1]), str(improvement), str(conclusion), str(datetime.now()))
        cursor.execute(query, purchases)
        return True
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
    finally:
        if connection:
            connection.commit()
            connection.close()

def find_matching_text(skill_value, res_eval):
    for key, text in res_eval.items():
        if all(k in skill_value for k in key.split(", ")):  # key의 모든 스킬이 포함되면 매칭
            return text
    return ""  # 매칭되는 키가 없으면 빈 문자열 반환

def analyze_improvement(duty, categories):
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
                combination_df["text"] = combination_df["skill"].apply(find_matching_text, args=(res_eval, ))
            except SyntaxError as e:
                print("Error during openai api response change eval:", str(e))
                return {"error": str(e)}
            except Exception as e:
                print("Error during openai api response change eval:", str(e))
                return {"error": str(e)}

            result[categories[category][0]] = combination_df.to_dict()

        return result
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
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
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
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

def analyze_conclusion(user_data:UserInputData):
    # 보완사항
    duty = user_data.jobs[0]
    data = user_data.languages + user_data.frameworks + user_data.libraries + user_data.devtools

    score = get_duty_scores(data)

    prompt = make_conclusion_prompt(duty, data, score)

    response = get_openai_response(prompt)
    return response

def get_duty_scores(skills, duty_num=3):
    connection = get_connection()

    try:
        query = """
            SELECT skill, category, duty,
                RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC, skill ASC) AS rank 
            FROM skill_probability
            WHERE unit = 1
            AND duty NOT IN ('언어별 개발자')
            ORDER BY duty, category
        """
        data = pd.read_sql_query(query, connection)

        score_series = data.groupby(by='duty', group_keys=False).apply(lambda x: calculate_score(x.drop(columns=['duty']), skills))
        score_series.sort_values(ascending=False)

        return score_series[:duty_num].to_dict()
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()

def calculate_score(df, user_skills):
    # 카테고리 가중치
    category_weights = {
        'it_language': 0.3,
        'framework': 0.3,
        'library': 0.2,
        'tool': 0.2
    }

    # 사용자 스킬 필터링
    user_skills_df = df[df['skill'].isin(user_skills)].copy()

    if user_skills_df.empty:
        return 0  # 일치하는 기술이 없으면 0점 반환

    # 지수 가중치 계산 (rank가 낮을수록 가중치 높음)
    user_skills_df['weight'] = np.exp(-user_skills_df['rank'])

    # 카테고리 가중치 적용
    user_skills_df['category_weight'] = user_skills_df['category'].map(category_weights)
    user_skills_df['final_weight'] = user_skills_df['weight'] * user_skills_df['category_weight']

    # 최종 점수 계산 (100점 만점)
    total_score = round(user_skills_df['final_weight'].sum() * 100, 2)
    return total_score

def make_conclusion_prompt(duty, skills, score):
    prompt = f"""다음 양식에 맞춰서 작성해줘
    사용자의 기술 스택: {','.join(skills)}
    score: {score}
    양식:
    사용자의 기술 스택을 기반으로 직무별 점수를 계산한 결과, <b>{duty} 직무의 점수는 ?점</b>입니다. 보다 높은 점수를 받기 위해 "사용자 기술 분석"과 "보완 사항"을 참고하여 부족한 기술을 보완하는 것을 추천합니다.<br>
    또한, 사용자의 기술 스택을 고려했을 때 가장 적합한 상위 3개 직무는 다음과 같습니다.<br><br>
    <ol><li><b>score.key (score.val점)</b>: 어떤 직무이며 어떤 기술 스택 때문에 적합한지 설명(30자 이내)</li></ol><br>
    현재 점수는 성장 가능성을 보여줄 뿐, 실력을 증명하는 절대적인 기준이 아닙니다. 꾸준한 학습과 실전 경험을 쌓으면 목표하는 직무에 도달할 수 있습니다. 포기하지 말고 나아가세요! 🚀 여러분의 도전을 응원합니다.
    """
    return prompt