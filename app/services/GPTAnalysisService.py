from app.models.user_input_data import UserInputData
from app.database.sqliteserver import get_connection

import os
import ast
import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

from ..models.category_weights import get_weight

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
    print('data: ', data)
    if data is None:
        # DB에 분석 결과가 없음
        improvement_result = analyze_improvement(duty, categories)
        conclusion_result = analyze_conclusion(user_data)
        if improvement_result is not False and conclusion_result is not False:
            set_customized_analysis(duty, categories, improvement_result, conclusion_result)
    else:
        improvement_result = ast.literal_eval(data[0])
        conclusion_result = ast.literal_eval(data[1])

    if improvement_result is not False:
        report_improvement = get_improvement_html(improvement_result)
    else:
        report_improvement = "분석 도중 문제가 발생했습니다. 재요청 부탁드립니다🥲."
    
    if conclusion_result is not False:
        report_conclusion = get_conclusion_html(conclusion_result)
    else:
        report_conclusion = "분석 도중 문제가 발생했습니다. 재요청 부탁드립니다🥲."

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
                    duty = ?
                    AND it_language = COALESCE(NULLIF(?, ''), it_language)
                    AND framework = COALESCE(NULLIF(?, ''), framework)
                    AND library = COALESCE(NULLIF(?, ''), library)
                    AND tool = COALESCE(NULLIF(?, ''), tool)
        '''
        purchases = (duty, ', '.join(categories['it_language'][1]), ', '.join(categories['framework'][1]), ', '.join(categories['library'][1]), ', '.join(categories['tool'][1]), )
        cursor.execute(query, purchases)
        return cursor.fetchone()
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return None
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
            if category == 'tool':
                continue

            combination_df = get_skill_combination(duty, category, categories[category][1])
            if combination_df is None:
                result[categories[category][0]] = ''
                continue

            prompt = make_improvement_prompt(duty, combination_df)

            response = get_openai_response(prompt)
            try:
                res_eval = ast.literal_eval(response)
                combination_df["text"] = combination_df["skill"].apply(find_matching_text, args=(res_eval, ))
            except SyntaxError as e:
                print("Error during openai api response change eval(analyze_improvement):", str(e))
                return False
            except Exception as e:
                print("Error during openai api response change eval(analyze_improvement):", str(e))
                return False

            result[categories[category][0]] = combination_df.to_dict()

        return result
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return False
    finally:
        if connection:
            connection.close()

def get_skill_combination(duty, category, user_skill, limit=2, probability=1.0):
    connection = get_connection()

    try:
        not_like_conditions = ''
        if user_skill:  # 데이터가 있으면
            not_like_conditions = f'AND sp.skill NOT IN ("{'", "'.join(', '.join(com) for com in combinations(user_skill, 3))}")'

        query = f"""
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
            )
            SELECT
                sp.skill,
                ROUND(sp.probability, 2) AS probability,
                r.skill AS rskill,
                r.probability AS rprobability,
                r.rank AS rrank,
                ROW_NUMBER() OVER (PARTITION BY r.rank ORDER BY sp.probability DESC, sp.pre_probability DESC) AS rn
            FROM skill_probability sp
            RIGHT OUTER JOIN Ranked r
                ON sp.skill LIKE r.skill || ',%'
                OR sp.skill LIKE '% ' || r.skill
                OR sp.skill LIKE '% ' || r.skill || ',%'
            WHERE sp.category = ?
            AND sp.duty = ?
            AND sp.unit = 3
            AND sp.probability >= ?
            {not_like_conditions}
            ORDER BY rrank ASC, rn ASC, sp.probability DESC;
        """
        purchases = (category, duty, limit, category, duty, probability, )
        df = pd.read_sql_query(query, connection, params=purchases)


        if df.empty:
            return None

         # 중복 호출되는 unique() 값 저장
        unique_rskills = sorted(df['rskill'].unique())
        rank_skills = ', '.join(unique_rskills)

        # 필터링 수행
        df_filtered = df[df['skill'] != rank_skills].copy()
        df_filtered.reset_index(drop=True, inplace=True)

        df_filtered = df_filtered.loc[
            df_filtered[df_filtered['rrank'] == 1].iloc[:2].index.to_list() +
            df_filtered[df_filtered['rrank'] != 1].index.to_list()
        ].reset_index(drop=True)

        # 중복된 skill을 가진 행 중 첫 번째 값만 유지
        df_filtered.drop_duplicates(subset=['skill'], keep='first', inplace=True)

        # rrank 별 상위 2개 선택
        df_filtered = df_filtered.groupby('rrank').head(2)

        return df_filtered
    except Exception as e:
        print("Error get_skill_combination:", str(e))
        return None # {"error": str(e)}
    finally:
        if connection:
            connection.close()

def make_improvement_prompt(duty, combination):
    """ 보완사항에 대한 프롬프트 작성 """
    prompt = f'''다음은 {duty} 직무에서 사용하는 기술 조합이다.
JSON 딕셔너리 형식을 따르며 키는 스킬 조합, 값은 "조합끼리의 시너지 효과(50자 이내)을 가진다. JSON만 반환해라.'''
    
    prompt += '(예시: {"c#, c++, java, rust": "성능 최적화, 메모리 관리, 네트워크 프로그래밍에 강점을 가짐"}).'

    # 중괄호 이슈 해결 및 리스트 변환
    skills = list(combination['skill'])  # Pandas Series가 아닐 경우 to_list() 필요 없음
    skill_str = ', '.join(f'"{item}"' for item in skills)
    prompt += f'''
    기술 조합: {{{skill_str}}}'''
    
    return prompt

def get_improvement_html(data_dict):
    columns = {'skill': '기술 조합', 'probability': '자격조건(%)', 'text': '설명'}
    html_content = ""

    if all(value is None for value in data_dict.values()):
        return '<p class="no_data">현재 보유한 기술 스택이 직무에 적합하여 추가적인 보완이 필요하지 않습니다. 그대로 자신 있게 지원하시면 좋겠습니다😊!</p>'

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
        for i in values["rskill"].keys():
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
            html_content += f"<h3>{rskill} 관련 기술 조합</h3>\n"
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

    prompt = make_conclusion_prompt(data, score)

    response = get_openai_response(prompt)
    try:
        res_eval = ast.literal_eval(response)
       
        result_dict = {'duty': duty, 'score': score, 'description': res_eval}
    except SyntaxError as e:
        print("Error during openai api response change eval(analyze_conclusion):", str(e))
        return False
    except Exception as e:
        print("Error during openai api response change eval(analyze_conclusion):", str(e))
        return False
    return result_dict

def get_duty_scores(skills):
    connection = get_connection()

    try:
        query = f"""
            SELECT skill, category, duty, probability,
                RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC, skill ASC) AS rank 
            FROM skill_probability
            WHERE unit = 1
            AND duty NOT IN ('언어별 개발자')
            AND probability != 0.0
            AND skill IN ({','.join(['?'] * len(skills))})
            ORDER BY duty, category
        """
        data = pd.read_sql_query(query, connection, params=(*skills, ))

        score_series = data.groupby(by='duty', group_keys=False).apply(calculate_score)
        score_dict = score_series.to_dict()
        return dict(sorted(score_dict.items(), key=lambda item: item[1], reverse=True))
    except Exception as e:
        print("Error during SQL execution:", str(e))
        return {"error": str(e)}
    finally:
        if connection:
            connection.close()

def calculate_score(df):
    if df.empty:
        return 0

    # 카테고리 가중치
    duty = df['duty'].unique()[0]
    category_weight = get_weight(duty)


    # 지수함수, 소프트맥스 함수 적용
    category_prob_sum_df = df.groupby("category")['probability'].sum().reset_index()
    category_prob_sum_df["except_prob"] = 100 - category_prob_sum_df["probability"]

    category_prob_sum_df["e_func"] = (10 **(category_prob_sum_df["probability"]/100))-1
    category_prob_sum_df["except_e_func"]=(10 **(category_prob_sum_df["except_prob"]/100))-1
    category_prob_sum_df["score"] = 100*category_prob_sum_df["e_func"]/(category_prob_sum_df['e_func']+category_prob_sum_df['except_e_func'])

    # 카테고리 가중치 적용
    category_prob_sum_df['category_weight'] = category_prob_sum_df['category'].map(category_weight)
    category_prob_sum_df['final_score'] = category_prob_sum_df['score'] * category_prob_sum_df['category_weight']
    total_score = round(category_prob_sum_df['final_score'].sum(), 2)
    return total_score

def make_conclusion_prompt(skills, score, top=3):
    prompt = '''다음은 사용자의 기술 스택을 기반으로 직무별 점수를 계산한 결과이다.
JSON 딕셔너리 형식을 따르며 키는 직무, 값은 ["직무에 대한 설명(50자 이내), 직무를 추천하는 이유에 대한 설명(100자 이내, 관련 스택이 없다면 "관련된 기술 스택이 없어 직무에 대한 판단을 드릴 수 없습니다.")"]을 반환해라
(예시: {"AI": ["AI 개발 및 데이터 분석을 수행하는 직무","Python, Pandas, FastAPI를 활용한 데이터 처리 및 AI 모델 개발 역량 보유"]}).'''

    prompt += f'''
    사용자의 기술 스택: {', '.join(skills)}
    score: {list(score.items())[:top]}
    '''
    return prompt

def get_conclusion_html(conclusion):
    duty = conclusion['duty']
    score = conclusion['score']
    description = conclusion['description']

    report = f'''<h3>📊 직무 점수 분석</h3>
    <p>
        사용자의 기술 스택을 기반으로 직무별 점수를 계산한 결과, 
        <strong>{duty} 직무의 점수는 {score[duty]}점</strong>입니다.
        보다 높은 점수를 받기 위해 "사용자 기술 분석"과 "보완 사항"을 참고하여 부족한 기술을 보완하는 것을 추천합니다.
    </p>

    <h3>🏆 가장 적합한 상위 3개 직무</h3>
    <ol>'''

    for key, val in description.items():
        report += f'''
    <li><b>{key} ({score[key]}점)</b>: {val[0]}<br>
    <span class="indent">{val[1]}</span>
    </li>'''
    

    report += '''
    </ol>

    <p>
        현재 점수는 성장 가능성을 보여줄 뿐, 실력을 증명하는 절대적인 기준이 아닙니다. 꾸준한 학습과 실전 경험을 쌓으면 목표하는 직무에 도달할 수 있습니다. 💪
        <br><strong>포기하지 말고 나아가세요! 🚀 여러분의 도전을 응원합니다.</strong>
    </p>'''

    return report