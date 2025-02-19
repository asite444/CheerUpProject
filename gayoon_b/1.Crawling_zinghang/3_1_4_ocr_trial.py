# ocr 성능 높이기 - tesseract ocr 옵션 사용 psm과 oem(ocr engine mode)
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Tesseract 실행 파일 경로 설정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 이미지 전처리 및 OCR 수행
def preprocess_and_ocr(image_path):
    try:
        # 이미지 열기
        img = Image.open(image_path)

        # 이미지 전처리
        img = img.convert("L")  # 흑백 변환
        img = ImageEnhance.Contrast(img).enhance(3.0)  # 명암 대비 강화
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 경계선 강조

        # Tesseract 설정
        custom_config = r"--psm 3 --oem 3 -l kor+eng"

        # OCR 실행
        text = pytesseract.image_to_string(img, config=custom_config)
        return text.strip()

    except Exception as e:
        print(f"Error processing image: {e}")
        return None

# 이미지 파일 경로
image_path = "downloaded_image.png"

# OCR 수행
result_text = preprocess_and_ocr(image_path)
print("추출된 텍스트:\n", result_text)
