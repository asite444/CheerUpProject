import os
import requests
from PIL import Image
import pytesseract
from io import BytesIO
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Tesseract 경로 설정 (Windows 사용자만 필요)
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# TESSDATA_PREFIX 설정
os.environ["TESSDATA_PREFIX"] = r"C:\\Program Files\\Tesseract-OCR"

# 이미지 다운로드 함수
def download_image(img_url, save_path="downloaded_image.png"):
    try:
        # 세션 설정 및 재시도 로직
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount('http://', HTTPAdapter(max_retries=retries))
        session.mount('https://', HTTPAdapter(max_retries=retries))

        # 이미지 다운로드
        response = session.get(img_url, timeout=10)
        response.raise_for_status()
        
        with open(save_path, "wb") as f:
            f.write(response.content)
        return save_path
    except Exception as e:
        print(f"Error downloading image {img_url}: {e}")
        return None

# OCR 실행 함수
def run_ocr_on_image(image_path):
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang="kor+eng")  # 한국어와 영어 동시에 인식
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None

# 통합 프로세스 함수
def process_image_with_ocr(img_url):
    print(f"Processing image: {img_url}")
    downloaded_image_path = download_image(img_url)
    if downloaded_image_path:
        ocr_text = run_ocr_on_image(downloaded_image_path)
        return ocr_text
    else:
        return None

# CSV 파일에서 이미지 URL 읽고 OCR 수행 및 저장
def process_images_from_csv(input_csv, output_csv):
    import pandas as pd

    # CSV 파일 읽기
    df = pd.read_csv(input_csv)

    # OCR 결과 저장
    ocr_results = []

    for index, row in df.iterrows():
        print(f"Processing {index + 1}/{len(df)}: {row['채용 내용(이미지)']}")
        img_url = row['채용 내용(이미지)']
        ocr_text = process_image_with_ocr(img_url)
        ocr_results.append(ocr_text)

    # OCR 결과를 데이터프레임에 추가
    df['채용 내용(세부 내용)'] = ocr_results

    # 결과를 CSV로 저장
    df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"OCR 결과가 저장된 파일: {output_csv}")

# 실행 부분
if __name__ == "__main__":
    input_csv = "2_2_zighang_job_details_with_images.csv"  # 입력 CSV 파일 경로
    output_csv = "3_zighang_job_details_with_ocr.csv"  # 출력 CSV 파일 경로

    process_images_from_csv(input_csv, output_csv)
