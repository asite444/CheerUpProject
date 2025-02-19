# easyocr의 결과를 tesseract ocr 옵션 결과와 병합 사용
import easyocr
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

# Tesseract 실행 파일 경로 설정
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# EasyOCR 리더 초기화
easyocr_reader = easyocr.Reader(['ko', 'en'])  # 한글과 영어 지원

# 이미지 파일 경로
image_path = "downloaded_image.png"

# EasyOCR 수행
print("--- EasyOCR 결과 ---")
easyocr_results = easyocr_reader.readtext(image_path)
easyocr_extracted_text = [text for (_, text, _) in easyocr_results]
easyocr_final_result = "\n".join(easyocr_extracted_text)
print(easyocr_final_result)

# Tesseract OCR 수행
print("--- Tesseract OCR 결과 ---")
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

tesseract_result_text = preprocess_and_ocr(image_path)
print(tesseract_result_text)

# 결과 비교
print("--- 결과 비교 ---")
print("EasyOCR 결과:")
print(easyocr_final_result)
print("\nTesseract 결과:")
print(tesseract_result_text)