# easy ocr로 성능 높이기 
# 문장 단위 출력
# 정규표현식 사용하여 분할 단위 지정(마침표 기준 등)
# pipeline 함수 사용하여 어색한 문맥 교정 

import easyocr
import re
from transformers import pipeline

# EasyOCR 리더 초기화
reader = easyocr.Reader(['ko', 'en'])  # 한글과 영어 지원

# Hugging Face의 언어 모델로 교정
corrector = pipeline("text2text-generation", model="facebook/bart-large-cnn")

# 텍스트 정리 함수
def format_and_correct_text(results):
    # EasyOCR 결과 텍스트 결합
    combined_text = " ".join([text for (_, text, _) in results])
    # 문장 단위로 나누기
    sentences = re.split(r'(?<=[.?!])\s+', combined_text)
    # 언어 모델을 이용한 교정 수행
    corrected_sentences = []
    for sentence in sentences:
        try:
            corrected = corrector(sentence, max_length=50, truncation=True)[0]['generated_text']
            corrected_sentences.append(corrected)
        except Exception as e:
            print(f"Error correcting sentence '{sentence}': {e}")
            corrected_sentences.append(sentence)  # 교정 실패 시 원문 유지
    return "\n".join(corrected_sentences)

# 이미지 파일 경로
image_path = "downloaded_image.png"

# OCR 수행
results = reader.readtext(image_path)

# 결과 정리 및 교정
formatted_text = format_and_correct_text(results)

# 결과 출력
print("가독성 있게 정리되고 교정된 텍스트:")
print(formatted_text)
