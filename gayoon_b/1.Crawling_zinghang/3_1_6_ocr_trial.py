# easy ocr 강력 추천(한글) - 이영배 멘토님

import easyocr

# EasyOCR 리더 초기화
reader = easyocr.Reader(['ko', 'en'])  # 한글과 영어 지원

# 이미지 파일 경로
image_path = "downloaded_image.png"

# OCR 수행
results = reader.readtext(image_path)

# 텍스트만 추출하여 출력
extracted_text = [text for (_, text, _) in results]
final_result = "\n".join(extracted_text)

print("인식된 텍스트:")
print(final_result)
