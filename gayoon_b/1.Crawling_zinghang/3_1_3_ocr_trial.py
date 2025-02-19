# 네트워크 이미지 1개를 로컬 환경으로 다운받은 후 ocr 수행 
# 성공 

import os
import requests
import pytesseract
from PIL import Image
from io import BytesIO

# Tesseract 경로 설정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# TESSDATA_PREFIX 환경 변수 설정
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# 이미지 URL에서 다운로드 및 OCR 수행
def download_and_perform_ocr(img_url, local_image_path):
    try:
        print(f"Downloading image from: {img_url}")

        # 이미지 다운로드
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()

        # 로컬에 이미지 저장
        with open(local_image_path, "wb") as file:
            file.write(response.content)
        print(f"Image saved to: {local_image_path}")

        # OCR 수행
        img = Image.open(local_image_path)
        text = pytesseract.image_to_string(img, lang="kor+eng")
        print("OCR 결과:\n", text.strip())
        return text.strip()
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# 이미지 URL과 로컬 파일 경로
img_url = "https://d2juy7qzamcf56.cloudfront.net/2024-11-21/661bf865-56f1-4240-b1ea-598ea8324a0b.png"
local_image_path = "downloaded_image.png"

# OCR 수행
ocr_result = download_and_perform_ocr(img_url, local_image_path)
