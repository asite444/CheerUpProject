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
        report_improvement = get_improvement_html(improvement(duty, categories))
        report_conclusion = analyze_conclusion(duty, data)

    report_improvement = get_improvement_html(data[1])
    # report_conclusion = data[2]

    return report_improvement, report_conclusion


def get_customized_analysis(duty, it_language, framework, library, tool):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        query = '''
                SELECT
                        user_tech, improvement, conclusion
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

def improvement(duty, categories, rank=2):
    # 보완사항
    connection = get_connection()

    try:
        cursor = connection.cursor()

        result = list()
        for category in categories.keys():
            query = f"""
                WITH Ranked AS (
                    SELECT
                            skill,
                            probability,
                            RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC) AS rank
                    FROM skill_probability
                    WHERE category = ? AND duty = ? AND unit = 1
                )
                SELECT skill, probability
                FROM Ranked
                WHERE rank <= ? AND skill NOT IN ({", ".join(["?"] * len(categories[category][1]))})
                ORDER BY rank
            """
            purchases = (category, duty, rank, *categories[category][1], )
            cursor.execute(query, purchases)
            skill_probability = cursor.fetchall()

            if skill_probability is None:   # df가 비어있는 경우
                continue

            temp = [categories[category][0]]
            for i in skill_probability:
                combination = get_skill_combination(duty, category, i[0])

                prompts = make_improvement_prompt(duty, i[0], combination if category != 'it_language' else None)
                temp.append([i[0], combination])

                for prompt in prompts:
                    response = get_openai_response(prompt).replace('-', '').strip().split('\n')
                    temp[-1].append(response)

            result.append(temp)

        return result
    except Exception as e:
        return 'get_skill_prob_rank error' + e
    finally:
        if connection:
            connection.close()

def get_skill_combination(duty, category, skill_keyword, probability=1, rank=2):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        query = f"""
            WITH Filtered AS (
                    SELECT
                        skill,
                        probability
                    FROM skill_probability
                    WHERE probability >= ? AND duty = ? AND category = ?
                    AND skill LIKE '%' || ? || '%'
                    AND unit > 1
            ),
            Ranked AS (
                    SELECT *, RANK() OVER (ORDER BY probability DESC) AS rank
                    FROM Filtered
            )
            SELECT skill, probability
            FROM Ranked
            WHERE rank <= ?
            ORDER BY rank
        """
        purchases = (probability, duty, category, skill_keyword, rank, )
        cursor.execute(query, purchases)    # [('javascript, typescript', 4.757185332011893, 1), ('css, html, javascript, typescript', 4.558969276511397, 2)]
        return cursor.fetchall()
    except Exception as e:
        return 'skill_combination error ' + e
    finally:
        if connection:
            connection.close()

def make_improvement_prompt(duty, skill, combination=None):
    """ 보완사항에 대한 프롬프트 작성 """
    prompt = [f'''"{skill}"의 "{duty}" 직무에서의 필요성을 개조식(itemization)으로 본론만 출력해주세요.  
        - 문장은 "- "로 시작하며, 각 문장은 독립적으로 작성할 것.  
        - "~을 높여줍니다.", "~을 가능하게 합니다.", "~을 최적화합니다." 같은 동작 중심 표현 사용.  
        - 150자 이내로 두 문장 출력.  
        - 설명형 어투를 유지하되 간결하게 표현할 것.  
        - "백엔드", "TypeScript" 같은 기술명이나 직무명을 반복하지 말 것.''']

    if combination:
        for com in combination:
            prompt.append(f'''"{com[0]}"의 "{duty}" 직무에서의 기술 조합의 역할을 개조식(itemization)으로 본론만 출력해주세요.  
    - 문장은 "- "로 시작하며, 각 문장은 독립적으로 작성할 것.  
    - "~로 관리하고 ~로 구현합니다." 같은 조합의 효과를 설명.  
    - 50자 이내로 한 문장 출력.  
    - 설명형 어투를 유지하되 간결하게 표현할 것.  
    - "백엔드", "TypeScript" 같은 기술명이나 직무명을 반복하지 말 것.''')
    
    return prompt

def get_improvement_html(data):
    report = """<ul>"""

    for category in data:
        category_name = category[0]  # 예: '언어', '프레임워크', '라이브러리', '툴'
        report += f"<h3>{category_name}</h3>"

        for tech in category[1:]:  # 각 기술 항목
            tech_name = tech[0]  # 기술명
            combinations = tech[1] if len(tech) > 1 else []  # 기술 조합 리스트 (최대 2개)
            descriptions = tech[2] if len(tech) > 2 else []  # 필요성 설명 리스트
            comb1_details = tech[3] if len(tech) > 3 else []  # 기술조합 1에 대한 설명
            comb2_details = tech[4] if len(tech) > 4 else []  # 기술조합 2에 대한 설명

            report += f"<ul><li><strong>{tech_name}</strong><ul>"

            # 필요성 설명 추가
            if descriptions:
                report += "<li><strong>📌 필요성</strong><ul>"
                for desc in descriptions:
                    report += f"<li>{desc}</li>"
                report += "</ul></li>"

            # 함께 많이 사용하는 조합 추가 (최대 2개)
            if combinations:
                report += "<li><strong>🔗 함께 많이 사용하는 조합</strong><ul>"
                for i, comb in enumerate(combinations):
                    report += f"<li>{comb[0]} (자격 조건: {round(comb[1], 2)}%)</li>"
                    
                    # 조합 1에 대한 설명 추가
                    if i == 0 and comb1_details:
                        report += "<ul>"
                        for detail in comb1_details:
                            report += f"<li>{detail}</li>"
                        report += "</ul>"

                    # 조합 2에 대한 설명 추가
                    if i == 1 and comb2_details:
                        report += "<ul>"
                        for detail in comb2_details:
                            report += f"<li>{detail}</li>"
                        report += "</ul>"

                report += "</ul></li>"

            report += "</ul></li></ul>"

    report += "</ul>"
    return report


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