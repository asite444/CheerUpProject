from app.models.user_input_data import UserInputData
from app.database.sqliteserver import get_connection

import os
import ast
import pandas as pd

from openai import OpenAI
from dotenv import load_dotenv

def make_message(category, skill):
    if category == 'it_language':
        return f'{skill}에 대한 강점을 15자 "주요 특징" 형식으로 요약해줘. 예시: "객체지향적이고 이식성 높은 언어"'
    elif category == 'framework':
        return f'{skill}에 대한 강점을 "언어/주요 기능(20자 이내)" 형식으로 요약해줘. 예시: "Python/빠른 개발이 가능하며 확장성이 좋은 프레임워크"'
    elif category == 'library':
        return f'{skill}에 대한 강점을 "언어/주요 기능(20자 이내)" 형식으로 요약해줘. 예시: "Python/데이터 처리 및 분석에 특화된 라이브러리리"'
    elif category == 'tool':
        return f'{skill}에 대한 설명을 "사용 분야/주요 특징" 형식으로 요약해줘. 예시: "컨테이너 가상화/애플리케이션 배포 및 관리"'

def get_api_key():
        # 프로젝트 루트의 .env 파일을 로드 (web/.env)
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        load_dotenv(dotenv_path)

        # 환경 변수에서 API_KEY 가져오기
        API_KEY = os.getenv("CHATGPT_API_KEY")
        return API_KEY

def customize(duty, category, stack):
        connection = get_connection()

        try:
                cursor = connection.cursor()

                query = '''
                        WITH Ranked AS (
                        SELECT 
                                skill, 
                                probability, 
                                pre_probability,
                                RANK() OVER (PARTITION BY category ORDER BY probability DESC, pre_probability DESC, skill) AS rank
                        FROM skill_prob_unit
                        WHERE category = ? AND duty = ?
                        )
                        SELECT skill, rank, probability, pre_probability
                        FROM Ranked
                        WHERE skill IN ({})
                        ORDER BY rank
                '''

                stack_placeholder = ", ".join(["?"] * len(stack))
                query = query.format(stack_placeholder)

                cursor.execute(query, (category, duty, *stack))
                skill_probability = cursor.fetchall() # [('nodejs', 2, 28.16, 17.28), ('django', 7, 11.18, 14.62), ('flask', 11, 3.82, 3.65)]

                result = list()
                client = OpenAI(api_key=get_api_key())
                for i in skill_probability:
                        message = make_message(category, i[0])
                        response = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        temperature=0.7,
                        messages=[
                                {'role': 'system', 'content': 'You are a reporter specializing in IT.'},
                                {'role': 'user', 'content': message}
                        ]
                        )

                        result.append(list(i) + response.choices[0].message.content.replace('\"', '').split('/'))
                return result

        except Exception as e:
                return 'customize error ' + e
        finally:
                if connection:
                        connection.close()

def generate_html_table(data, title="언어"):
        col = {'언어': ['언어', '순위', '자격 조건(%)', '우대 조건(%)', '설명'],
                '프레임워크': ['프레임워크', '순위', '자격 조건(%)', '우대 조건(%)', '기반 언어', '설명'],
                '라이브러리': ['라이브러리', '순위', '자격 조건(%)', '우대 조건(%)', '기반 언어', '설명'],
                '툴': ['언어', '순위', '자격 조건(%)', '우대 조건(%)', '분야', '설명']}

        # HTML 테이블 시작
        html = f'''<h3>{title}</h3>
        <table>
                <tr>
        '''
        
        # 테이블 헤더 추가
        for col in col[title]:
                html += f'<th scope="col">{col}</th>'
        html += '</tr>'

        # 테이블 데이터 추가
        for row in data:
                html += '<tr>'
                for cell in row:
                        html += f'<td>{cell}</td>'
                        html += '</tr>'
        
        html += '</table>'
        return html

def analyze_user_tech(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """
                GPT에게 사용자 스택을 분석 요청
        """

        connection = get_connection()

        try:
                duty = user_data.jobs[0]
                it_language = sorted(user_data.languages)
                framework = sorted(user_data.frameworks)
                library = sorted(user_data.libraries)
                tool = sorted(user_data.devtools)

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
                data = cursor.fetchone()

                if data is not None: # not null
                        return data[1]
                else:   # seq == None
                        report = """
                        <ul>
                        """
                        result = []
                        category = {'it_language': ['언어', it_language], 'framework': ['프레임워크', framework], 'library': ['라이브러리', library], 'tool': ['툴', tool]}
                        for c in ['it_language', 'framework', 'library', 'tool']:
                                result = customize(duty, c, category[c][1])  # [['java', 1, 47.02, 8.4, '"객체지향적이며 플랫폼 독립적인 언어"'], ['python', 5, 21.3, 8.47, '"간결하고 읽기 쉬운 문법"']]
                                if result == []:
                                        continue

                                report += generate_html_table(result, category[c][0])
                        
                        report += '''</ul>'''

                        # cursor.execute('SELECT MAX(seq) FROM customized_analysis ')
                        # data = cursor.fetchone()[0]
                        # seq = data + 1 if data is not None else 0

                        # query = """
                        #         INSERT INTO
                        #         customized_analysis
                        #         VALUES
                        #         (?, ?, ?, ?, ?, ?, ?, ?)
                        # """
                        # purchases = (seq, ', '.join(it_language), ', '.join(framework), ', '.join(library), ', '.join(tool), report, '2025.02.06', duty, )
                        # cursor.execute(query, purchases)
                        return report
        except Exception as e:
               return e
        finally:
               connection.commit()
               if connection:
                      connection.close()

# SQLite 데이터베이스에서 상위 2개 기술 스택 가져오기
def skill_top():
        connection = get_connection()

        try:
                # cursor = connection.cursor()
                query = """
                        WITH Ranked AS (
                        SELECT
                                seq, duty, category, skill, probability, pre_probability,
                                RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC) AS rank
                        FROM skill_prob_unit
                        )
                        SELECT * FROM Ranked WHERE rank <= 2;
                """
                return pd.read_sql_query(query, connection)
        except Exception as e:
              return 'skill_top error' + e
        finally:
              if connection:
                    connection.close()

# 특정 기술의 조합을 가져오기
def skill_combination(duty, skill_keyword, category):
        connection = get_connection()

        try:
                query = """
                WITH Filtered AS (
                        SELECT seq, duty, category, skill, probability, pre_probability
                        FROM skill_probability
                        WHERE probability >= 1
                        AND duty = ? AND category = ? AND skill LIKE '%' || ? || '%'
                        AND LENGTH(skill) - LENGTH(REPLACE(skill, ',', '')) >= 1
                ),
                Ranked AS (
                        SELECT *, RANK() OVER (PARTITION BY duty, category ORDER BY probability DESC, pre_probability DESC) AS rank
                        FROM Filtered
                )
                SELECT * FROM Ranked WHERE rank <= 2;
                """
                return pd.read_sql_query(query, connection, params=(duty, category, skill_keyword))
        except Exception as e:
                return 'skill_combination error ' + e
        finally:
              if connection:
                    connection.close()

def generate_prompt(df, duty, language = [], framework = [], library = [], tool = []):
    """ 특정 직무(duty)에 대한 기술 스택 설명을 생성하는 프롬프트 작성 """
    categories = ["it_language", "framework", "library", "tool"]
    prompt = f"다음은 '{duty}' 직무에서 가장 많이 요구되는 기술 스택입니다. 각 기술에 대한 설명을 반드시 다음 주어진 리스트 형식에 맞춰 그대로 출력하세요.:\n"
    for category in categories:
        subset = df[(df["duty"] == duty) & (df["category"] == category)]
        if subset.empty:
            continue
        prompt += f"{category}**\n"
        prompt += "["
        if category == 'it_language':
            category_list = language
        elif category == 'framework':
            category_list = framework
        elif category == 'library':
            category_list = library
        elif category == 'tool':
            category_list = tool
        for _, row in subset.iterrows():
            skill = row["skill"]
            if skill not in category_list:
                if category != 'it_language':
                    prompt += '['
                prompt += f"['{skill.title()} (자격 조건: {row['probability']}%)',"
                prompt += f"'이 기술을 {duty} 직무에서 왜 배워야하고 어떻게 활용되는지 설명'],"
                if category != 'it_language':
                    for _, skill_c in skill_combination(duty, skill, category).iterrows():
                        prompt += f"['{skill_c['skill']} (자격 조건: {skill_c['probability']}%)', '이 조합이 어떻게 활용되는지 설명'],"
                    prompt += '],'
        prompt += "]\n\n"
    return prompt

def get_openai_response(prompt):
    """ OpenAI API를 사용하여 기술 스택 설명을 생성 """
    client = OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature=0.5,
        messages=[
            {"role": "system", "content": "당신은 IT 전문가입니다. 주어진 질문에 모두 답하세요."},
            {"role": "user", "content": prompt}
        ]
    )
    print(response.choices[0].message.content, end='\n\n')
    return response.choices[0].message.content.strip()

def analyze_improvement(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """보완완사항"""
        duty = user_data.jobs[0]
        it_language = sorted(user_data.languages)
        framework = sorted(user_data.frameworks)
        library = sorted(user_data.libraries)
        tool = sorted(user_data.devtools)

        df = skill_top()
        prompt = generate_prompt(df, duty, it_language, framework, library, tool)
        response = get_openai_response(prompt)

        report = '''<ul>'''
        category = {'it_language': ['언어'], 'framework': ['프레임워크'], 'library': ['라이브러리'], 'tool': ['툴']}

        print(prompt)
        print(response)

        test = response.split('\n\n')
        temp = test[0].split('**')
        pro = ast.literal_eval(temp[1])
        report += f"""
                <h3>{category[temp[0]][0]}</h3>
                <li>{pro[0][0]}
                        <li>{pro[0][1]}</li>
                </li>"""
        for i in test[1:]:
                # print(i)
                temp = i.split('**')
                pro = ast.literal_eval(temp[1])
                report += f"""
                <h3>{category[temp[0]][0]}</h3>"""
                for j in pro:
                        report += f"""
                        <li>{j[0][0]}"""

                        report += f"""
                                <li>{j[0][1]}"""
                        for k in j[1:]:
                                report += f"""
                                <li>{k[0]}
                                <li>{k[1]}</li>
                                </li>"""
                        report += """
                        </li>"""
        report += """</ul>"""
        
        return report

def analyze_conclusion(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """결론"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report