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
    if data is not None:
        # DB에 분석 결과가 있음
        return data
    else:
        # DB에 분석 결과가 없음
        report_user_tech = user_tech(duty, categories)
        report_improvement = improvement(duty, categories)

    return report_user_tech, report_improvement, analyze_conclusion()


def get_customized_analysis(duty, it_language, framework, library, tool):
    connection = get_connection()

    try:
        cursor = connection.cursor()
        query = '''
                SELECT
                        seq, text
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

def user_tech(duty, categories):
    connection = get_connection()

    try:
        cursor = connection.cursor()

        result = list()
        for category in categories.keys():
            query = f'''
                    WITH Ranked AS (
                        SELECT 
                                skill, 
                                probability, 
                                pre_probability,
                                RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC) AS rank
                        FROM skill_prob_unit
                        WHERE category = ? AND duty = ?
                    )
                    SELECT skill, rank, probability, pre_probability
                    FROM Ranked
                    WHERE skill IN ({", ".join(["?"] * len(categories[category][1]))})
                    ORDER BY rank
            '''
            purchases = (category, duty, *categories[category][1], )
            cursor.execute(query, purchases)
            skill_probability = cursor.fetchall() # [('nodejs', 2, 28.16, 17.28), ('django', 7, 11.18, 14.62), ('flask', 11, 3.82, 3.65)]

            temp = [categories[category][0]]
            for i in skill_probability:
                    prompt = make_user_tech_prompt(category, i[0])
                    response = get_openai_response(prompt)

                    temp.append(list(i) + response.replace('\"', '').replace('.', '').split('/'))
            
            result.append(temp)

        return get_user_tech_html(result)
    except Exception as e:
        return 'user_tech ' + e
    finally:
        if connection:
            connection.close()

def make_user_tech_prompt(category, skill):
    if category == 'it_language':
        return f'{skill}에 대한 강점을 15자 "주요 특징" 형식으로 요약해줘. 예시: "객체지향적이고 이식성 높은 언어"'
    elif category == 'framework':
        return f'{skill}에 대한 강점을 "언어/주요 기능(20자 이내)" 형식으로 요약해줘. 예시: "Python/빠른 개발이 가능하며 확장성이 좋은 프레임워크"'
    elif category == 'library':
        return f'{skill}에 대한 강점을 "언어/주요 기능(20자 이내)" 형식으로 요약해줘. 예시: "Python/데이터 처리 및 분석에 특화된 라이브러리리"'
    elif category == 'tool':
        return f'{skill}에 대한 설명을 "사용 분야/주요 특징(20자 이내)" 형식으로 요약해줘. 예시: "컨테이너 가상화/애플리케이션 배포 및 관리"'

def get_user_tech_html(data):
    columns = {'언어': ['언어', '순위', '자격 조건(%)', '우대 조건(%)', '설명'],
            '프레임워크': ['프레임워크', '순위', '자격 조건(%)', '우대 조건(%)', '기반 언어', '설명'],
            '라이브러리': ['라이브러리', '순위', '자격 조건(%)', '우대 조건(%)', '기반 언어', '설명'],
            '툴': ['언어', '순위', '자격 조건(%)', '우대 조건(%)', '분야', '설명']}

    report = """<ul>"""
    for i in data:
        report += f'''<h3>{i[0]}</h3>
        <table>
            <tr>
        '''
        # 테이블 헤더 추가
        for col in columns[i[0]]:
            report += f'<th scope="col">{col}</th>'
        report += '</tr>'

        # 테이블 데이터 추가
        for row in i[1:]:
            report += '<tr>'
            for cell in row:
                report += f'<td>{cell}</td>'
            report += '</tr>'
        
        report += '</table>'
    report += '''</ul>'''
    return report

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
                    FROM skill_prob_unit
                    WHERE category = ? AND duty = ?
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
                prompt = make_improvement_prompt(duty, i[0])
                combination = get_skill_combination(duty, category, i[0])
                response = get_openai_response(prompt).replace('-', '').split('\n')

                temp.append([i[0], response, combination])

            result.append(temp)

        return get_improvement_html(result)
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
                    AND LENGTH(skill) - LENGTH(REPLACE(skill, ',', '')) >= 1
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
    # prompt = f"다음은 '{duty}' 직무에서 가장 많이 요구되는 기술 스택입니다. 기술에 대한 설명을 반드시 다음 주어진 리스트 형식에 맞춰서 출력하세요.:"
    # prompt = f'''다음 형식에 맞춰 개조식(itemization)으로 존댓말로 출력해줘:'''
    # prompt = f'''공통 요구사항
    # - 문장은 "- "로 시작하며, 독립적으로 작성할 것. 말투는 존댓말로 통일.
    # - 직무명({duty})과 기술명({skill})은 반드시 언급하지 말 것.
    # - 설명형 어투를 유지하되 불필요한 서술어 없이 간결하게 직접적인 기능 설명.'''

    # prompt += f'''
    # - {skill}을/를 {duty} 직무에서 왜 배워야하고 어떻게 활용되는지 필요성을 설명해줘(80자 이내).'''

    # if combination:
    #     for com in combination:
    #         prompt += f'''
    # - {com[0]}이/가 {duty} 직무에서 어떻게 활용되는지를 설명해줘(50자 이내).'''

    prompt = f'''"{skill}"의 "{duty}" 직무에서의 필요성을 개조식(itemization)으로 본론만 출력해주세요.  
        - 문장은 "- "로 시작하며, 각 문장은 독립적으로 작성할 것.  
        - "~을 높여줌.", "~을 가능하게 함.", "~을 최적화함." 같은 동작 중심 표현 사용.  
        - 150자 이내로 두 문장 출력.  
        - 설명형 어투를 유지하되 간결하게 표현할 것.  
        - "백엔드", "TypeScript" 같은 기술명이나 직무명을 반복하지 말 것.'''
    
    return prompt

def get_improvement_html(data):
    report = """<ul>"""

    for i in data:
        category = i[0]
        report += f"<h3>{category}</h3>"

        for tech in i[1:]:  # 각 기술 항목
            tech_name = tech[0]
            descriptions = tech[1]
            combinations = tech[2]

            report += f"<li><strong>{tech_name}</strong><ul>"

            # 필요성 설명 추가
            for desc in descriptions:
                report += f"<li>{desc}</li>"

            # 기술 조합 설명 추가
            if combinations and category != '언어':
                report += "<li><strong>조합 추천</strong><ul>"
                for comb in combinations:
                    report += f"<li>{comb[0]}(자격 조건: {round(comb[1], 2)}%)</li>"
                report += "</ul></li>"

            report += "</ul></li>"

    report += "</ul>"
    return report

def analyze_conclusion():
            # 데이터 처리 및 HTML 텍스트 생성
        """결론"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report