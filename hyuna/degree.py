import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import rc
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
from dotenv import load_dotenv

# 객체 생성 (openai 라이브러리 사용 예시)
import openai

path = './sql'

# degree_graph 폴더 생성
output_folder = 'Degree_charts'
os.makedirs(output_folder, exist_ok=True)


#학력 차트용 데이터 가져오기기
def select_degree(cursor):
    cursor.execute("""WITH total_count AS (
    SELECT
        category AS duty_category,
        COUNT(*) AS total_jobs
    FROM (
        SELECT 'PM' AS category, degree FROM processing WHERE duty LIKE '%PM%'
        UNION ALL
        SELECT '데이터 직무' AS category, degree FROM processing WHERE duty LIKE '%데이터 직무%'
        UNION ALL
        SELECT '백엔드' AS category, degree FROM processing WHERE duty LIKE '%백엔드%'
        UNION ALL
        SELECT '인프라 엔지니어' AS category, degree FROM processing WHERE duty LIKE '%인프라 엔지니어%'
        UNION ALL
        SELECT '앱 개발자' AS category, degree FROM processing WHERE duty LIKE '%앱 개발자%'
        UNION ALL
        SELECT '게임' AS category, degree FROM processing WHERE duty LIKE '%게임%'
        UNION ALL
        SELECT 'AI' AS category, degree FROM processing WHERE duty LIKE '%AI%'
        UNION ALL
        SELECT '임베디드' AS category, degree FROM processing WHERE duty LIKE '%임베디드%'
        UNION ALL
        SELECT '프론트 엔드' AS category, degree FROM processing WHERE duty LIKE '%프론트 엔드%'
        UNION ALL
        SELECT 'QA' AS category, degree FROM processing WHERE duty LIKE '%QA%'
        UNION ALL
        SELECT '데이터 분석' AS category, degree FROM processing WHERE duty LIKE '%데이터 분석%'
        UNION ALL
        SELECT 'VR' AS category, degree FROM processing WHERE duty LIKE '%VR%'
        UNION ALL
        SELECT '시스템' AS category, degree FROM processing WHERE duty LIKE '%시스템%'
        UNION ALL
        SELECT '블록체인' AS category, degree FROM processing WHERE duty LIKE '%블록체인%'
        UNION ALL
        SELECT 'ERP' AS category, degree FROM processing WHERE duty LIKE '%ERP%'
        UNION ALL
        SELECT '언어별 개발자' AS category, degree FROM processing WHERE duty LIKE '%언어별 개발자%'
    ) AS filtered_data
    GROUP BY category
    )
    SELECT
        f.category AS duty_category,
        CASE
            WHEN f.degree = 0 THEN '무관/없음'
            WHEN f.degree = 1 THEN '학사'
            WHEN f.degree = 2 THEN '석사&박사'
        END AS degree_required,
        COUNT(*) AS count,
        t.total_jobs,
        ROUND(100.0 * COUNT(*) / t.total_jobs, 2) AS percentage
    FROM (
        SELECT 'PM' AS category, degree FROM processing WHERE duty LIKE '%PM%'
        UNION ALL
        SELECT '데이터 직무' AS category, degree FROM processing WHERE duty LIKE '%데이터 직무%'
        UNION ALL
        SELECT '백엔드' AS category, degree FROM processing WHERE duty LIKE '%백엔드%'
        UNION ALL
        SELECT '인프라 엔지니어' AS category, degree FROM processing WHERE duty LIKE '%인프라 엔지니어%'
        UNION ALL
        SELECT '앱 개발자' AS category, degree FROM processing WHERE duty LIKE '%앱 개발자%'
        UNION ALL
        SELECT '게임' AS category, degree FROM processing WHERE duty LIKE '%게임%'
        UNION ALL
        SELECT 'AI' AS category, degree FROM processing WHERE duty LIKE '%AI%'
        UNION ALL
        SELECT '임베디드' AS category, degree FROM processing WHERE duty LIKE '%임베디드%'
        UNION ALL
        SELECT '프론트 엔드' AS category, degree FROM processing WHERE duty LIKE '%프론트 엔드%'
        UNION ALL
        SELECT 'QA' AS category, degree FROM processing WHERE duty LIKE '%QA%'
        UNION ALL
        SELECT '데이터 분석' AS category, degree FROM processing WHERE duty LIKE '%데이터 분석%'
        UNION ALL
        SELECT 'VR' AS category, degree FROM processing WHERE duty LIKE '%VR%'
        UNION ALL
        SELECT '시스템' AS category, degree FROM processing WHERE duty LIKE '%시스템%'
        UNION ALL
        SELECT '블록체인' AS category, degree FROM processing WHERE duty LIKE '%블록체인%'
        UNION ALL
        SELECT 'ERP' AS category, degree FROM processing WHERE duty LIKE '%ERP%'
        UNION ALL
        SELECT '언어별 개발자' AS category, degree FROM processing WHERE duty LIKE '%언어별 개발자%'
    ) AS f
    JOIN total_count t ON f.category = t.duty_category
    GROUP BY f.category, degree_required, t.total_jobs
    ORDER BY f.category, percentage DESC;
    """)

    rows = cursor.fetchall()
    return rows


#전체공고에 대해 학력별 퍼센트 구하기기
def select_degree_avg(cursor):
    cursor.execute("""
        SELECT 
            CASE 
                WHEN degree = 0 THEN '무관/없음'
                WHEN degree = 1 THEN '학사'
                WHEN degree = 2 THEN '석사&박사'
            END AS 학력사항,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM processing), 2) AS 퍼센트
        FROM processing
        GROUP BY degree
        ORDER BY degree;
    """)
    rows = cursor.fetchall()
    print(rows)
    return rows


#openai api key로 설명 추출하고 리스트에 저장
def prompt_degree(data,avg_data):
    # 같은 직군끼리 리스트에 담기
    job_groups = {}
    job_list = []  # 직군(직무) 이름을 저장할 리스트

    # 직군별로 데이터를 그룹화
    for item in data:
        job = item[0]  # 직군 이름
        if job not in job_groups:
            job_groups[job] = []        # 직군이 처음 나오면 빈 리스트 생성
            job_list.append(job)        # 직군 이름을 job_list에 추가
        job_groups[job].append(item)    # 해당 직군에 데이터 추가

    # 직무별 설명을 리스트형식으로 저장
    job_explain_data = []
  
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

   # 객체 생성
    llm = ChatOpenAI(
        temperature=0,
        max_tokens=2048,
        model_name="gpt-4o",
        openai_api_key=api_key  # 여기서 직접 API 키 전달
    )
    for i,group in enumerate( job_groups.values()):
        prompt = ChatPromptTemplate.from_template("""
            역할 : 개발분야의 취업준비생을 위한 채용공고 데이터분석가 
            청자 :  취업준비생 
            직군 데이터 구조 : (직군, 학력사항, 해당학력공고개수, 직군의전체공고개수, 퍼센트) 
            직군 데이터 설명 
            1. 직군 : {duty}
            2. 학력사항 : 무관/없음, 학사 , 석사&박사 
            3. 해당학력공고개수 : int 
            4. 직군의 전체공고 개수 : int 
            5. 해당학력공고개수/직군의 전체공고개수 : 퍼센트 
            직군 데이터 : {data}

            전체 공고수의 비율 데이터
            {avg_data}

            조건 : 100글자 내외, ~입니다 말투 사용, 각 학력사항에 대해 개조식으로 설명, 직군 데이터의 퍼센트 포함할 것, 결론에서만 전체 공고수의 비율 데이터를 참고할 것
            직군 데이터가 ('게임', '무관/없음', 23, 23, 100.0)와 같이 일부만 존재할 경우 아래의 ###보고서 내용###에서 없는 내용은 제외할 것,
            출력값에서 ###보고서 내용###이라는 제목은 제외, 내용만 출력할 것, 줄바꿈 없이 출력할 것
                                                  
            ###보고서 내용###
                                                  
            - 무관/없음: 무관/없음에 대한 한줄 설명 - 학사 : 학사에 대한 한줄 설명 - 석사&박사 : 석사&박사에 대한 한줄 설명 - 결론 : 전체 공고수의 비율 데이터와 직군 데이터의 퍼센트를 비교하여 특이한점 한두줄 설명                 
                                                  """)
        # chain 연결 (LCEL)
        chain = prompt | llm
        # chain 호출
        response = chain.invoke({"duty":{job_list[i]}, "data": {str(group)},"avg_data": {str(avg_data)}})
        # print("사용 데이터 : ",str(group))
        # print(response.content)
        # print("===================================")
        job_explain_data.append(response.content)
    return job_explain_data
        

# 학력 그래프 만들고 경로, 설명 db에 넣기
def update_degree(data,job_explain_list,cursor):
    rc('font', family='Malgun Gothic')
    plt.rcParams['axes.unicode_minus'] = False

    job_groups = {}
    for item in data:
        job, degree, _, _, percent = item
        if job not in job_groups:
            job_groups[job] = []
        job_groups[job].append((degree, percent))

    colors = {'무관/없음': '#66b3ff', '학사': '#99ff99', '석사&박사': '#ffcc99'}

    for idx, (job, values) in enumerate( job_groups.items()):
        labels = [v[0] for v in values]
        sizes = [v[1] for v in values]
        color_list = [colors.get(label, '#dddddd') for label in labels]
        plt.figure(figsize=(6, 6))
        plt.pie(sizes, labels=labels, colors=color_list, autopct='%1.1f%%', startangle=140)
        plt.title(f'{job} 학력 분포')
        plt.legend(loc='upper right', title='학력 사항')

        image_path = f"degree_charts/{job}.png"
        img_path = os.path.join(output_folder, f'{job}.png')
        plt.savefig(img_path)
        plt.close()

        # asia.db 업데이트
        cursor.execute("""
        UPDATE duty_analysis
        SET degree = ?
        WHERE duty = ?;
        """, ("['"+img_path+"', '"+str(job_explain_list[idx])+"']", job))


def select_degree_answer(cursor):
    cursor.execute("""
        SELECT 
            career,
            degree
                   
        FROM duty_analysis
    """)
    rows = cursor.fetchall()


    for i in rows:
        print(i)

    
def main():
    connect = sqlite3.connect('./app/database/asia.db')
    cursor = connect.cursor()
    data = select_degree(cursor)
    avg_data = select_degree_avg(cursor)                                                                        
    job_explain_list = prompt_degree(data,avg_data)  
    update_degree(data,job_explain_list,cursor)       
    # select_degree_answer(cursor)
    connect.commit()
    connect.close()

if __name__ == '__main__':
    main()





