# OCR 진행 코드
import requests
import pytesseract
from PIL import Image
from io import BytesIO

# C:\Program Files\Tesseract-OCR
# Tesseract 경로 설정 (Windows 사용자만 필요)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 이미지 URL에서 텍스트 추출
def extract_text_from_image(img_url):
    try:
        # 이미지 다운로드
        response = requests.get(img_url)
        img = Image.open(BytesIO(response.content))

        # OCR 실행
        text = pytesseract.image_to_string(img, lang="kor+eng")  # 한국어와 영어 인식
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None

# 예시 이미지 URL
img_url = "https://d2juy7qzamcf56.cloudfront.net/2024-12-31/94109af2-3c4b-489e-9bb8-3f4170b77632.png"
text = extract_text_from_image(img_url)
print("추출된 텍스트:\n", text)
