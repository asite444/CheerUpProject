# 1.6 오후 15시, easy ocr 그나마 괜찮은 결과 

import easyocr
import re
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

# EasyOCR 리더 초기화
reader = easyocr.Reader(['ko', 'en'], gpu=False)  # 한글과 영어 지원

# 이미지 전처리 함수
def preprocess_image(image_path):
    try:
        img = Image.open(image_path)
        img = img.convert("L")  # 흑백 변환
        img = ImageEnhance.Contrast(img).enhance(2.5)  # 명암 대비 강화
        img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)  # 경계선 강조
        img = img.resize((int(img.width * 2), int(img.height * 2)), Image.Resampling.LANCZOS)  # 해상도 증가
        return np.array(img)  # EasyOCR에 전달할 수 있도록 Numpy 배열로 변환
    except Exception as e:
        print(f"Error during image preprocessing: {e}")
        return None

# 텍스트 정리 함수
def format_text(results):
    try:
        # EasyOCR 결과 텍스트 결합
        combined_text = " ".join([text for (_, text, _) in results])

        # 문장 단위로 나누기
        sentences = re.split(r'(?<=[.?!])\s+', combined_text)

        # 정돈된 문장 반환
        return "\n".join([sentence.strip() for sentence in sentences if sentence.strip()])
    except Exception as e:
        print(f"Error during text formatting: {e}")
        return "텍스트 정리 중 오류가 발생했습니다."

# OCR 수행 및 텍스트 정리
def perform_ocr(image_path):
    try:
        # 이미지 전처리
        preprocessed_img = preprocess_image(image_path)
        if preprocessed_img is None:
            return "이미지 전처리 중 오류가 발생했습니다."

        # OCR 수행
        results = reader.readtext(preprocessed_img)
        if results:
            return format_text(results)
        else:
            return "OCR 결과가 비어 있습니다."
    except Exception as e:
        print(f"Error during OCR: {e}")
        return "OCR 수행 중 오류가 발생했습니다."

# 메인 실행
if __name__ == "__main__":
    # 이미지 파일 경로
    image_path = "downloaded_image.png"

    # OCR 수행 및 결과 출력
    print("Performing OCR and Text Formatting...")
    final_output = perform_ocr(image_path)

    print("\n가독성 있게 정리된 텍스트:")
    print(final_output)
