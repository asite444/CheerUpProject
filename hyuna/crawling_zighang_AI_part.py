# selenium의 webdriver를 사용하기 위한 import
from selenium import webdriver

# selenium으로 키를 조작하기 위한 import
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# 페이지 로딩을 기다리는데에 사용할 time 모듈 import
import time
import pandas as pd

#OCR import
# from paddleocr import PaddleOCR
import easyocr
import cv2
import numpy as np
import requests
import re


# Selenium WebDriver 설정
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저를 보이지 않게 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

#메인 ai 화면에서 채용공고의 href 링크를 리스트에 저장
def get_href_link():
    driver = setup_driver()
    try:
        url = "https://zighang.com/ai/"  # 대상 URL로 변경
        driver.get(url)

        # 페이지 로드 대기
        time.sleep(2)

        # 페이지 끝까지 스크롤하기
        scroll_pause_time = 2  # 스크롤 후 대기 시간
        last_height = driver.execute_script("return document.body.scrollHeight")


        while True:
            # 페이지 끝까지 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            # 스크롤 후 새로운 높이 가져오기
            new_height = driver.execute_script("return document.body.scrollHeight")
            # 더 이상 스크롤이 없으면 종료
            if new_height == last_height:
                break
            last_height = new_height


        # 클래스 조건 충족하는 a 태그 찾기
        a_tags = driver.find_elements(By.CSS_SELECTOR, "a[class*='flex w-full flex-col justify-center gap-4 truncate rounded-2xl border border-gray-200 p-4 hover:shadow-md active:shadow-lg active:ring-2 active:ring-primary md:h-full md:gap-4 md:px-6 md:py-5 ']")
        # href 속성 값 추출
        href_list = list(set([a.get_attribute("href") for a in a_tags if a.get_attribute("href")]))#중복 제거함(없지만만)
        # 결과 출력
        print("총 링크 개수 :",len(href_list))

    finally:
        # 드라이버 종료
        driver.quit()
        return href_list
        # return ['https://zighang.com/recruitment/beedc502-423d-422c-9922-7e325161ce18','https://zighang.com/recruitment/ecd6120e-b011-46a2-a543-1cb8a1c47593']
    



#href_list의 각 채용 공고의 채용정보(text,img) 크롤링링 
def get_text_img_per(href_link_list):
    #모든 채용정보 저장할 변수
    all_job_data = []
    for idx,href in enumerate(href_link_list):
        driver = setup_driver()
        try:
            print(f"크롤링 중인 공고 사이트 : {href}")
            driver.get(href)

            # 페이지 로드 대기
            time.sleep(1)  # 필요에 따라 조정

            # # 텍스트 추출
            # 회사 이름
            company_name = driver.find_element(By.CSS_SELECTOR,"a[class*='w-fit cursor-pointer text-lg font-semibold text-[#5E5E5E] underline underline-offset-4 md:text-2xl']").text
            # 채용 직군
            job_title = driver.find_element(By.CSS_SELECTOR, "h1[class*='break-all text-xl font-extrabold text-black md:gap-5 md:text-3xl']").text
            # 경력, 관련직군, 학력, 근무 지역, 근무 형태
            attributes = driver.find_elements(By.CSS_SELECTOR, "div[class*='flex w-full flex-[4] justify-start font-medium text-black']")
            section = []
            for attr in attributes:
                try:
                    # 한 단계 하위 div 찾기
                    sub_div = attr.find_element(By.TAG_NAME, "div").text
                    section.append(sub_div)
                except Exception as e:
                    print(f"Error processing section: {e}")
                    continue

            # # 이미지 추출
            images = driver.find_elements(By.CSS_SELECTOR, "img[class*='w-full cursor-pointer px-4']")
            image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]
            image_alt = [img.get_attribute("alt") for img in images if img.get_attribute("alt")]


            # # 추출한 텍스트와 이미지 정제하여 저장장
            job_data = {
                "채용 링크": href,
                "회사 이름": company_name,
                "채용 직군": job_title,
                "경력": section[0],
                "관련 직군": section[1],
                "학력": section[2],
                "근무 지역": section[3],
                "근무 형태": section[4],
                "채용 내용(이미지)": image_urls,
                "채용 내용(간단 설명)": image_alt,
                "채용 내용(세부 내용)": None
            }
            all_job_data.append(job_data)
            print(f"모집공고 {len(href_link_list)}개의 진행률 ({idx+1}/{len(href_link_list)})")

        finally:
            driver.quit()

    return all_job_data



# 채용 정보를 csv형태로 저장
def save_all_job_list_to_csv(all_job_list, filename="all_job_data.csv"):
    try:
        # 데이터프레임 생성
        df = pd.DataFrame(all_job_list)

        # CSV로 저장
        df.to_csv(filename, index=False, encoding="utf-8-sig")  # utf-8-sig로 한글 깨짐 방지
        print(f"데이터가 {filename}에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"CSV 저장 중 오류 발생: {e}")


def preprocess_image(url):
    # URL에서 이미지 다운로드
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        raise ValueError("이미지를 다운로드할 수 없습니다.")
    image_data = np.asarray(bytearray(response.content), dtype=np.uint8)
    img = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

    # 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


    # 이진화 처리 (Otsu's thresholding)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # # 이미지 크기 확대
    binary = cv2.resize(binary, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)

    return binary


# 임시 파일 저장
def img_to_text_easyocr():
    # 이미지 읽기
    # image_path = "https://d2juy7qzamcf56.cloudfront.net/2024-11-29/7cca04e0-6970-4e03-8b50-ce2ecf56604b.png"
    image_path= 'https://d2juy7qzamcf56.cloudfront.net/2024-12-13/be9d03c0-1d78-478d-8e15-5644f3245678.png'
    # processed_image = preprocess_image(image_path)
    # cv2.imwrite("temp_image.jpg", processed_image)
    # OCR 리더 생성
    reader = easyocr.Reader(['ko', 'en'])

    # 이미지에서 텍스트 추출
    results = reader.readtext(image_path,decoder='beamsearch')

    #후처리
    for result in results:
        text = result[1]
        # 특수문자 제거
        text = re.sub(r'[^\w\s가-힣a-zA-Z]', '', text)
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text).strip()

        #결과 출력
        print(f"{text}")






def main():
    # #직행 페이지에서 채용 공고 크롤링
    # href_link_list = get_href_link()
    
    # #채용 링크별 텍스트, 이미지 크롤링
    # all_job_list = get_text_img_per(href_link_list)

    # #csv형식으로 정제한 데이터 저장
    # save_all_job_list_to_csv(all_job_list)

    # img의 OCR(easyocr)
    img_to_text_easyocr()




if __name__=="__main__":
    main()

    