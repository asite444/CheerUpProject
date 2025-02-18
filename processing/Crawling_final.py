from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import pandas as pd
import re
import datetime
import urllib
import requests
import json
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sqlite3
# 초기 세팅
crawling_dt = datetime.now().strftime('%Y-%m-%d-%H')

session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0'}
session.headers.update(headers)

pro_url = []
i=1
previous_response = None

while True:
    # url 불러오기
    url = f'https://career.programmers.co.kr/api/job_positions?order=recent&page={i}&job_category_ids[]=1&job_category_ids[]=4&job_category_ids[]=25&job_category_ids[]=2&job_category_ids[]=3&job_category_ids[]=5&job_category_ids[]=11&job_category_ids[]=12&job_category_ids[]=92&job_category_ids[]=7&job_category_ids[]=16&job_category_ids[]=20&job_category_ids[]=9&job_category_ids[]=18&job_category_ids[]=59&job_category_ids[]=22&job_category_ids[]=26&job_category_ids[]=27&job_category_ids[]=10&job_category_ids[]=13&job_category_ids[]=17&job_category_ids[]=6&job_category_ids[]=125&job_category_ids[]=126&job_category_ids[]=127&job_category_ids[]=128&job_category_ids[]=129&job_category_ids[]=130&job_category_ids[]=158'

    res = requests.get(url,headers= headers)
    res_list = json.loads(res.text)

    # 이전 응답과 비교하여 같으면 정지
    if res_list == previous_response:
        print("프로그래머스 url 수집 종료")
        break

    # 현재 응답을 이전 응답으로 저장
    previous_response = res_list

    for j in range(len(res_list['jobPositions'])):
        pro_url.append('https://career.programmers.co.kr/'+res_list['jobPositions'][j]['url'])

    i += 1

def fetch_job_pro(href):
    try:
        id = re.findall(r'\d+',href)
        url = f'https://career.programmers.co.kr/api/job_positions/{id[0]}'
        res = session.get(url)
        res.raise_for_status()
        pro_json = res.json()
        return json.dumps(pro_json, ensure_ascii=False)
    except Exception as e:
        print(f"Error processing {href}: {e}")
        return None

# 병렬 처리
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(fetch_job_pro, href): href for href in pro_url}
    pro_json = []
    for future in as_completed(future_to_url):
        result = future.result()
        if result:
            pro_json.append(result)

# --------------------------------------------------------------------------------------------------------
### json 데이터 프레임화

# 직군 매핑 딕셔너리
job_dic = {
    1: "서버/백엔드", 4: "프론트엔드", 25: "웹 풀스택", 2: "안드로이드", 3: "iOS",
    5: "머신러닝", 11: "인공지능(AI)", 12: "데이터 엔지니어링", 92: "DBA",
    7: "모바일 게임", 16: "게임 클라이언트", 20: "게임 서버", 9: "시스템/네트워크",
    18: "시스템 소프트웨어", 59: "데브옵스", 22: "인터넷 보안", 26: "임베디드 소프트웨어",
    27: "로보틱스 미들웨어", 10: "QA", 13: "사물인터넷(IoT)", 17: "응용 프로그램",
    6: "블록체인", 125: "개발PM", 126: "웹 퍼블리싱", 127: "크로스 플랫폼",
    128: "VR/AR/3D", 129: "ERP", 130: "그래픽스", 158: "데이터 분석"
}

# 데이터 초기화
data = {
    'text': [], 'id': [], 'url': [], 'career_all': [], 'title': [], 'location': [], 
    'duty': [], 'technicalTags': [], 'countryCode': [],
    'description': [], 'requirement': [], 'preferredExperience': [], 
    'company_name': [], 'crawling_dt': []
}

# JSON 데이터 파싱 및 처리
for job in pro_json:
    job = json.loads(job)
    job_position = job.get('jobPosition')
    if not job_position:
        print("Skipping job without 'jobPosition':", job)
        continue

    # 데이터 추가
    data['text'].append(json.dumps(job, ensure_ascii=False))
    data['id'].append(job_position.get('id'))
    data['url'].append('https://career.programmers.co.kr' + job_position.get('url', ''))
    data['career_all'].append(job_position.get('career', ''))
    data['title'].append(job_position.get('title', ''))
    data['location'].append(job_position.get('address', ''))
    data['duty'].append(", ".join(job_dic[j] for j in job_position.get('jobCategoryIds', [])))
    data['technicalTags'].append(", ".join(tag['name'] for tag in job_position.get('technicalTags', [])))
    data['countryCode'].append(job_position.get('countryCode', ''))
    data['description'].append(job_position.get('description', ''))
    data['requirement'].append(job_position.get('requirement', ''))
    data['preferredExperience'].append(job_position.get('preferredExperience', ''))
    data['company_name'].append(job_position['company'].get('name', ''))
    data['crawling_dt'].append(crawling_dt)

# 데이터프레임 생성
pro_df = pd.DataFrame(data)

# 경력 정보에서 min_career와 max_career를 추출하는 함수
def parse_career(career):
    if "경력 무관" in career or not career:
        return 0, 100
    if "신입" in career:
        return 0, 1
    match = re.search(r"(\d+)\s*~\s*(\d+)", career)
    if match:
        return map(int, match.groups())
    match = re.search(r"(\d+)", career)
    if match:
        year = int(match.group(1))
        return year, year
    return 0, 100

# min_career와 max_career 계산
pro_df["career"], pro_df["max_career"] = zip(*pro_df["career_all"].apply(parse_career))

# 주요 지역 추출 함수
def extract_region(address):
    if not isinstance(address, str) or pd.isna(address):
        return '기타'
    patterns = {
        '서울': r'(서울|서울특별시)', '경기': r'(경기|경기도)', '인천': r'(인천|인천광역시)',
        '강원': r'(강원|강원도)', '부산': r'(부산|부산광역시)', '대구': r'(대구|대구광역시)',
        '대전': r'(대전|대전광역시)', '광주': r'(광주|광주광역시)', '울산': r'(울산|울산광역시)',
        '세종': r'(세종|세종특별자치시)', '제주': r'(제주|제주특별자치도)', '전북': r'(전북|전라북도)',
        '전남': r'(전남|전라남도)', '충북': r'(충북|충청북도)', '충남': r'(충남|충청남도)',
        '경북': r'(경북|경상북도)', '경남': r'(경남|경상남도)', '재택': r'(재택|재택근무|재택 근무)'
    }
    for region, pattern in patterns.items():
        if re.search(pattern, address):
            return region
    return '기타'

# 지역 정보 추출
pro_df['location'] = pro_df['location'].apply(extract_region)

# 중복 제거
pro_df.drop_duplicates(inplace=True)

# HTML 파싱 및 데이터 정리 함수
def parse_html_to_columns(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 데이터 분류
    description = []
    preferred_experience = []
    requirements = []

    for tag in soup.find_all(["h3", "h2", 'strong', "ul", "li"]):
        tag_text = tag.get_text(strip=True)

        # 직무 설명
        if ("직무 설명" in tag_text or 
            "포지션 소개" in tag_text or
            "주요업무" in tag_text or
            "주요 업무" in tag_text or
            "[주요업무]" in tag_text or
            "주요 소개" in tag_text or
            "조직소개" in tag_text or
            "직무 소개" in tag_text or
            "직무소개" in tag_text):
            next_ul = tag.find_next("ul")
            if next_ul:  # ul 태그가 있는 경우만 처리
                description.append(next_ul.get_text(strip=True))

        # 자격 요건
        elif ("자격 요건" in tag_text or
              "자격요건" in tag_text or
              "자격 조건" in tag_text or
              "자격조건" in tag_text or
              "[자격 요건]" in tag_text or
              "[자격요건]" in tag_text or
              "[자격 조건]" in tag_text or
              "[자격조건]" in tag_text or
              "지원자격" in tag_text or
              "지원 자격" in tag_text or
              "[지원자격]" in tag_text or
              "[지원 자격]" in tag_text):
            next_ul = tag.find_next("ul")
            if next_ul:
                requirements.append(next_ul.get_text(strip=True))
                
        # 우대 사항
        elif ("우대 사항" in tag_text or 
              "우대사항" in tag_text or
              "우대 조건" in tag_text or 
              "우대조건" in tag_text or
              "[우대사항]" in tag_text or 
              "[우대 사항]" in tag_text or
              "[우대조건]" in tag_text or
              "[우대 조건]" in tag_text):
            next_ul = tag.find_next("ul")
            if next_ul:
                preferred_experience.append(next_ul.get_text(strip=True))


    return {
        "description": " ".join(description),
        "requirement": " ".join(requirements),
        "preferredExperience": " ".join(preferred_experience)
    }

# 데이터 처리
parsed_data = pro_df["description"].apply(parse_html_to_columns)

# 결과를 새로운 데이터프레임으로 정리
parsed_df = pd.DataFrame(parsed_data.tolist())
parsed_df['id'] = pro_df['id']  # id를 유지

for col in ["description", "requirement", "preferredExperience"]:
    parsed_df[col] = parsed_df[col].replace('', np.nan)  # 빈 문자열을 NaN으로 변환
    parsed_df[col] = parsed_df[col].fillna(pro_df[col])  # NaN을 원본 데이터로 채우기

# 태그 제거 함수 정의
def remove_html_tags(text):
    if pd.isna(text):  # NaN 처리
        return text
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(strip=True)

# 각 열에 HTML 태그 제거 적용
columns_to_clean = ["description", "requirement", "preferredExperience"]
for col in columns_to_clean:
    parsed_df[col] = parsed_df[col].apply(remove_html_tags)

# requirement 또는 preferredExperience 열에서 NaN 값 또는 빈 문자열인 행 삭제
parsed_df = parsed_df.dropna(subset=["requirement", "preferredExperience"])  # NaN 값 제거
parsed_df = parsed_df[(parsed_df["requirement"] != '') & (parsed_df["preferredExperience"] != '')]  # 빈 문자열 제거

# 원본 데이터에서 requirement, preferredExperience, description 열 제거
columns_to_remove = ["description", "requirement", "preferredExperience", "career_all", "max_career"]
pro_df = pro_df.drop(columns=[col for col in columns_to_remove if col in pro_df.columns], errors="ignore")

# 나머지 열과 parsed_df 병합
programmers_df = pd.merge(pro_df, parsed_df, on='id')
programmers_df.drop_duplicates(keep='first', inplace=True, ignore_index=True)


# -------------------------------------------------------------------------------------------------------------------------------

### 원티드 url 크롤링

SCROLL_PAUSE_TIME = 4
WANTED_URL = 'https://www.wanted.co.kr/wdlist/518?country=kr&job_sort=job.recommend_order&years=-1&locations=all'

global start_time

def chrome_driver():
    # 크롬드라이버 위치
    path1 = r"C:/Users/Anichan/Downloads/chromedriver-win64/chromedriver.exe"

    s = Service(path1)
    driver = webdriver.Chrome(service=s)

    driver.get(WANTED_URL)
    time.sleep(3)

    print(f'driver wanted loading 완료 : {time.time() - start_time: .5f}')

    last_height = driver.execute_script('return document.body.scrollHeight')
    actions = driver.find_element(By.CSS_SELECTOR, 'body')

    try:
        print(f'wanted page scroll 시작 : {time.time() - start_time: .5f}')

        retry = 0
        while True:
            # 페이지 끝까지 스크롤
            actions.send_keys(Keys.END)
            time.sleep(SCROLL_PAUSE_TIME)

            # 새로운 페이지 높이 확인
            new_height = driver.execute_script('return document.body.scrollHeight')
            if new_height == last_height:
                print(f'wanted page retry : {retry}')
                retry += 1
                if retry >= 5:
                    break
            else:
                retry = 0
                last_height = new_height

        print('모든 컨텐츠가 로드되었습니다.')
        print(f'wanted page scroll 종료 : {time.time() - start_time: .5f}')

    except Exception as e:
        print(f'Error : {time.time() - start_time: .5f}')
        print(e)
        return False

    href_list = Extract_href(driver)
    driver.quit()
    return href_list

def Extract_href(driver):
    print(f'href element extraction 시작 : {time.time() - start_time: .5f}')

    href_list = []

    job_cards = driver.find_elements(By.CSS_SELECTOR, 'ul[data-cy="job-list"] li a')
    for job_card in job_cards:
        href = job_card.get_attribute('href')

        if href and href not in href_list:
            href_list.append(href)

    print(f'href element extraction 종료 : {time.time() - start_time: .5f}')
    print(f'총 href 개수 : {len(href_list)}')

    return href_list

if __name__ == "__main__":
    start_time = time.time()
    print(f'프로그램 시작 : {time.time() - start_time: .5f}')
    href_list = chrome_driver()
    print(f'프로그램 종료 : {time.time() - start_time: .5f}')

# json 데이터 수집

def fetch_job_wanted(href):
    try:
        wid = re.findall(r'\d+', href)[-1]
        url = f'https://www.wanted.co.kr/api/chaos/jobs/v3/{wid}/details?1736076088092='
        res = session.get(url)
        res.raise_for_status()
        wanted_json = res.json()
        return json.dumps(wanted_json, ensure_ascii=False)
    except Exception as e:
        print(f"Error processing {href}: {e}")
        return None

# 병렬 처리
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_url = {executor.submit(fetch_job_wanted, href): href for href in href_list}
    wanted_json = []
    for future in as_completed(future_to_url):
        result = future.result()
        if result:
            wanted_json.append(result)

def extract_job_data(job):
    job = json.loads(job)
    if 'job' not in job:
        print("Skipping job without 'job':", job)
        return None

    wjob_position = job['job']['detail']
    job_data = {
        'text': json.dumps(job, ensure_ascii=False),
        'id': job['job']['id'],
        'url': f"https://www.wanted.co.kr/wd/{job['job']['id']}",
        'title': wjob_position['position'],
        'location': job['job']['address']['location'],
        'duty': ", ".join([tag['text'] for tag in job['job']['category_tag']['child_tags']]) if job['job']['category_tag']['child_tags'] else None,
        'technicalTags': ", ".join([tag['text'] for tag in job['job']['skill_tags']]) if job['job']['skill_tags'] else None,
        'countryCode': job['job']['address']['country_code'],
        'company_name': job['job']['company']['name'],
        'career': job['job']['annual_from'],
        # 'max_career': job['job']['annual_to'],
        'description': wjob_position['main_tasks'],
        'requirement': wjob_position['requirements'],
        'preferredExperience': wjob_position['preferred_points'],
        'crawling_dt': crawling_dt
    }
    return job_data

job_data_list = [extract_job_data(job) for job in wanted_json if job is not None]
wanted_df = pd.DataFrame(job_data_list)

wanted_df['countryCode'] = wanted_df['countryCode'].str.upper()
wanted_df.drop_duplicates(keep='first', inplace=True, ignore_index=True)

# 데이터프레임 병합
merged_df = pd.concat([programmers_df, wanted_df], axis=0, ignore_index=True)

# # JSON 파일 로드
# with open('./csv/duty_replace.json', 'r', encoding='utf-8') as f:
#     duty_replace = json.load(f)

# duty_replace = {
#     "PM": ["개발PM", "개발 매니저", "프로덕트 매니저", 'PM'],
#     "데이터 직무": ["DBA", "데이터 엔지니어링", "데이터 엔지니어", "빅데이터 엔지니어", "데이터 직무"],
#     "백엔드": ["서버/백엔드", "서버 개발자", "웹 개발자", "백엔드"],
#     "인프라 엔지니어": ["데브옵스", "인터넷 보안", "DevOps / 시스템 관리자", "보안 엔지니어", "네트워크 관리자", "소프트웨어 엔지니어", "인프라 엔지니어"],
#     "앱 개발자": ["iOS", "안드로이드", "안드로이드 개발자", "iOS 개발자", "크로스플랫폼 앱 개발자", "앱 개발자"],
#     "게임": ["모바일 게임", "게임 클라이언트", "게임 서버", "게임"],
#     "AI": ["머신러닝", "인공지능(AI)", "머신러닝 엔지니어", "음성 엔지니어", "AI"],
#     "임베디드": ["사물인터넷(IoT)", "로보틱스 미들웨어", "임베디드 소프트웨어", "하드웨어 엔지니어", "임베디드 개발자", "시스템 소프트웨어", "임베디드"],
#     "프론트 엔드": ["웹 퍼블리싱", "웹 퍼블리셔", "프론트엔드 개발자", "그래픽스", "그래픽스 엔지니어", "크로스 플랫폼", "프론트엔드", "프론트 엔드"],
#     "QA": ["QA", "테스트 엔지니어"],
#     "데이터 분석": ["데이터 분석", "BI 엔지니어", "데이터 사이언티스트"],
#     "VR": ["VR/AR/3D", "VR 엔지니어", "VR"],
#     "시스템": ["시스템/네트워크", "응용 프로그램", "시스템"],
#     "블록체인": ["블록체인", "블록체인 플랫폼 엔지니어"],
#     "ERP": ["ERP전문가", "ERP"],
#     "언어별 개발자": ["파이썬 개발자", "자바 개발자", "C", "C++ 개발자", ".NET 개발자", "Node.js 개발자", "PHP 개발자", "언어별 개발자"],
#     "삭제": ["Chief Information Officer", "Chief Technology Officer", "CIO", "CTO", "루비온레일즈 개발자", "기술지원", "영상", "삭제"],
#     "백엔드, 프론트 엔드": ["웹 풀스택"]
# }

# SQLite 데이터베이스 파일 경로 지정 (예: database.db)
db_path = "./asia.db"

# 데이터베이스 연결
conn = sqlite3.connect(db_path)

query = "SELECT * FROM duty_element"
df_duty_element = pd.read_sql_query(query, conn)

duty_replace = {}
for _, row in df_duty_element.iterrows():
    if row['name'] not in duty_replace:
        duty_replace[row['name']] = {}
    duty_replace[row['name']] = row['synonym'].split(',')

# 딕셔너리를 반대로 매핑 (value -> key)
reverse_duty = {v: k for k, values in duty_replace.items() for v in values}

def process_categories(categories):
    if pd.isna(categories):  # NaN 값 처리
        return None

    # 정규식을 사용하여 ,로 구분된 단어 리스트로 변환
    category_list = re.split(r",\s*|\s*,|\s*,\s*", categories)
    processed = set()
    unmapped_words = set()

    for word in category_list:
        word = word.strip()
        if word in reverse_duty:
            mapped_values = reverse_duty[word].split(", ")  # 여러 개의 매핑 값을 리스트로 변환
            for mapped_value in mapped_values:
                if mapped_value != "삭제":
                    processed.add(mapped_value)  # 개별 항목을 추가하여 중복 제거
        else:
            unmapped_words.add(word)

    if unmapped_words:
        print(f"----------------------------------맵핑되지 않은 단어: {', '.join(unmapped_words)}")
        
    if not processed:  # 처리된 카테고리가 없으면 None 반환
        return None

    return ", ".join(sorted(processed))  # 중복 제거 후 정렬된 결과 반환

# duty 열 처리
merged_df["duty"] = merged_df["duty"].apply(process_categories)

# ---------------------------------------------------------------------------------------------------------------------
# csv 파일에 저장

# 현재 스크립트의 디렉토리 경로를 가져옵니다
script_dir = os.path.dirname(os.path.abspath(__file__))

# csv 디렉토리의 절대 경로를 생성합니다
csv_dir = os.path.join(script_dir, 'csv')

# csv 디렉토리가 없으면 생성합니다
os.makedirs(csv_dir, exist_ok=True)

# programmers_df.to_csv(os.path.join(csv_dir, f'{crawling_dt}_programmers.csv'), encoding='utf-8-sig')
# wanted_df.to_csv(os.path.join(csv_dir, f'{crawling_dt}_wanted_df.csv'), encoding='utf-8-sig')
# test = pd.concat([programmers_df, wanted_df], axis=0, ignore_index=True)
# test.to_csv(os.path.join(csv_dir, f'{crawling_dt}_merged_df.csv'), encoding='utf-8-sig')

# 파일 경로를 생성합니다
file_path = os.path.join(csv_dir, f'{crawling_dt}_final.csv')

# CSV 파일에 저장
merged_df.to_csv(file_path, index=False, encoding='utf-8-sig')
print(f"CSV 파일 저장: {file_path}")
print('공고 개수: ', len(merged_df))

# all_df_path = os.path.join(csv_dir, 'all.csv')

# # 파일이 존재하지 않으면 빈 all_df 생성
# if not os.path.exists(all_df_path):
#     all_df = pd.DataFrame(columns=merged_df.columns)
# else:
#     # 기존 all_df 읽기
#     all_df = pd.read_csv(all_df_path)

# all_df = pd.concat([all_df, merged_df], ignore_index=True)

# # 중복된 행 제거
# all_df = all_df.drop_duplicates(
#     subset=["id", "url", "title", "location", "duty", "technicalTags",
#             "countryCode", "company_name", "career",
#             "description", "requirement", "preferredExperience"],
#     keep="last"
# )

# # 오늘자 까지의 총 데이터
# output_path1 = os.path.join(csv_dir, f"{crawling_dt}_all.csv")
# all_df.to_csv(output_path1, index=False, encoding="utf-8-sig")
# print(f"오늘 총 데이터 저장: {output_path1}")

# # 지금까지의 총 데이터
# output_path = os.path.join(csv_dir, "all.csv")
# all_df.to_csv(output_path, index=False, encoding="utf-8-sig")
# print(f"총 데이터 저장: {output_path}")
