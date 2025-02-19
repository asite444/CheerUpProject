import os
from PIL import Image
import pytesseract

# Tesseract 실행 파일 경로 설정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# TESSDATA_PREFIX 경로 설정
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR"

# OCR 테스트용 이미지 파일 경로
image_path = r"abc.png"

try:
    # 이미지에서 텍스트 추출 (한글 언어 설정)
    text = pytesseract.image_to_string(Image.open(image_path), lang="kor")
    print("추출된 텍스트:")
    print(text)
except Exception as e:
    print(f"Error: {e}")
