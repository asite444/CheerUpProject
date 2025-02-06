from app.models.user_input_data import UserInputData
from app.database.sqliteserver import get_connection

import os
import openai

from dotenv import load_dotenv

def analyze_stack_top5(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """ top5"""
        report=f"""
                <ul>
                        <li><strong>Python (자격 조건: 10.51%, 우대 조건: 15.99%)</strong><br>
                        데이터 분석, 인공지능, 웹 개발 등에 활용되는 다목적 프로그래밍 언어. Django 및 Flask와 함께 백엔드 개발에 많이 사용됨.
                        </li>
                        <li><strong>Java (자격 조건: 14.27%, 우대 조건: 9.30%)</strong><br>
                        객체 지향 프로그래밍 언어로, 엔터프라이즈 애플리케이션과 대규모 시스템 개발에서 널리 사용되며, Spring 프레임워크와 함께 활용됨.
                        </li>
                        <li><strong>JavaScript (자격 조건: 2.77%, 우대 조건: 4.94%)</strong><br>
                        웹 개발의 필수 언어로, 프론트엔드와 백엔드(Node.js) 개발 모두 가능하며, 다양한 프레임워크 및 라이브러리를 지원함.
                        </li>
                        <li><strong>HTML/CSS (자격 조건: 2.97%, 우대 조건: 0.87%)</strong><br>
                        웹 페이지의 구조(HTML)와 디자인(CSS)을 구성하는 기본 요소로, 백엔드 개발에서도 프론트엔드와의 연계를 위해 필요함.
                        </li>
                </ul>

                
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
        return report

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
                for i in skill_probability:
                        message = make_message(category, i[0])
                        response = openai.chat.completions.create(
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
                languages=['java', 'python'] frameworks=['django', 'flask'] libraries=['pandas', 'recoil'] devtools=['docker', 'git', 'mysql'] jobs=['백엔드']
        """

        print('analyze user tech-----------')
        print(user_data)

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
                print(data)

                if data is not None: # not null
                        return data[1]
                else:   # seq == None
                        openai.api_key = get_api_key()
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
                        return report
        except Exception as e:
               return e
        finally:
               connection.commit()
               if connection:
                      connection.close()

def analyze_security(user_data:UserInputData):
            # 데이터 처리 및 HTML 텍스트 생성
        """보안사항"""
        report=f"""
                <ul>
                        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
                        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
                </ul>

        """
        
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