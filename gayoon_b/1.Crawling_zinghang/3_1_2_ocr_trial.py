# 네트워크 이미지 ocr 수행 - 실패 
import os
import pytesseract
from PIL import Image
import requests
from io import BytesIO

# Tesseract 실행 파일 경로 설정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# TESSDATA_PREFIX 설정
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

# 이미지 URL에서 텍스트 추출
def extract_text_from_image(img_url):
    try:
        print(f"Processing image: {img_url}")
        # 이미지 다운로드
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))

        # OCR 실행 (한국어와 영어 동시 인식)
        text = pytesseract.image_to_string(img, lang="kor+eng")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None

# 테스트 실행
img_url = "https://d2juy7qzamcf56.cloudfront.net/2024-12-31/94109af2-3c4b-489e-9bb8-3f4170b77632.png"
text = extract_text_from_image(img_url)
print("추출된 텍스트:\n", text)
