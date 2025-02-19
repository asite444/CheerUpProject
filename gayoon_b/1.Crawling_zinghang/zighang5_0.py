# 이미지 태그 시도 전 성공했던 코드
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os

# Selenium WebDriver 설정
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저를 보이지 않게 실행
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# 각 채용 링크에서 데이터 추출
def extract_job_details(driver, job_link):
    try:
        driver.get(job_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "relative"))
        )
        
        job_data = {
            "채용 링크": job_link,
            "회사 이름": None,
            "채용 직군": None,
            "경력": None,
            "관련 직군": None,
            "학력": None,
            "근무 지역": None,
            "근무 형태": None,
            "채용 내용(이미지)": None,
            "채용 내용(간단 설명)": None,
            "채용 내용(세부 내용)": None
        }

        # 회사 이름
        company_name = driver.find_element(By.CSS_SELECTOR, "a.text-lg.font-semibold.underline")
        job_data["회사 이름"] = company_name.text.strip()

        # 채용 직군
        job_title = driver.find_element(By.CSS_SELECTOR, "h1.break-all.text-xl.font-extrabold")
        job_data["채용 직군"] = job_title.text.strip()

        # 경력, 관련직군, 학력, 근무 지역, 근무 형태
        attributes = driver.find_elements(By.CSS_SELECTOR, "section.grid.gap-4 div.flex.items-center")
        for attr in attributes:
            label = attr.find_element(By.CSS_SELECTOR, "span.flex-shrink-0").text.strip()
            value = attr.find_element(By.CSS_SELECTOR, "div.flex.font-medium.text-black").text.strip()

            if label == "경력":
                job_data["경력"] = value
            elif label == "직군":
                job_data["관련 직군"] = value
            elif label == "학력":
                job_data["학력"] = value
            elif label == "근무지역":
                job_data["근무 지역"] = value
            elif label == "근무형태":
                job_data["근무 형태"] = value

        # 채용 내용(이미지, 간단 설명)
        img_tag = driver.find_element(By.CSS_SELECTOR, "div.relative img")
        job_data["채용 내용(이미지)"] = img_tag.get_attribute("src")
        job_data["채용 내용(간단 설명)"] = img_tag.get_attribute("alt")

        # 채용 내용(세부 내용) - 현재는 비워 둠, 추후 OCR 결과를 저장
        job_data["채용 내용(세부 내용)"] = None

        return job_data

    except Exception as e:
        print(f"Error extracting details from {job_link}: {e}")
        print(traceback.format_exc())
        return None

# CSV 파일에서 링크를 읽어와 데이터를 수집
def scrape_job_links(input_csv, output_csv, failed_csv):
    job_links = pd.read_csv(input_csv)["채용 공고 링크"].tolist()
    all_job_data = []
    failed_links = []  # 에러가 발생한 링크 저장

    # 기존 CSV 파일이 있으면 로드
    if os.path.exists(output_csv):
        all_job_data = pd.read_csv(output_csv).to_dict("records")
    
    if os.path.exists(failed_csv):
        failed_links = pd.read_csv(failed_csv)["채용 링크"].tolist()

    driver = setup_driver()

    try:
        for index, job_link in enumerate(job_links):
            # 이미 처리된 링크는 스킵
            if job_link in [data["채용 링크"] for data in all_job_data] or job_link in failed_links:
                print(f"Skipping already processed link: {job_link}")
                continue

            print(f"Processing {index + 1}/{len(job_links)}: {job_link}")
            job_details = extract_job_details(driver, job_link)
            if job_details:
                all_job_data.append(job_details)
                # 실시간 저장
                pd.DataFrame(all_job_data).to_csv(output_csv, index=False)
            else:
                failed_links.append(job_link)
                # 실패한 링크 저장
                pd.DataFrame(failed_links, columns=["채용 링크"]).to_csv(failed_csv, index=False)
            time.sleep(1)  # 서버 과부하 방지

    finally:
        driver.quit()

# 데이터 저장
def main():
    input_csv = "zighang_jobs.csv"  # 기존에 저장된 CSV 파일 경로
    output_csv = "zighang_job_details_with_details.csv"  # 결과를 저장할 파일 경로
    failed_csv = "zighang_failed_links.csv"  # 실패한 링크 저장

    scrape_job_links(input_csv, output_csv, failed_csv)

    print(f"Job details saved to '{output_csv}'")
    print(f"Failed links saved to '{failed_csv}'")

if __name__ == "__main__":
    main()

