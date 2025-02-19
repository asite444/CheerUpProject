# easyocr 성능 높이기
# 돋보기 기능 적당히 하기 , 토스뱅크를 토스 방크로 읽는 문제 
import easyocr
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

# EasyOCR 리더 초기화
reader = easyocr.Reader(['ko', 'en'], gpu=False)

# 이미지 전처리 함수
def preprocess_image(image_path):
    img = Image.open(image_path)
    img = ImageEnhance.Contrast(img).enhance(2.0)  # 명암 대비 강화
    img = img.filter(ImageFilter.SHARPEN)  # 선명화 필터
    img = img.resize((int(img.width * 1.1), int(img.height * 1.1)), Image.Resampling.LANCZOS)  # 확대
    return np.array(img)

# 텍스트 감지 및 그룹화 함수
def extract_and_format_text(image_path):
    # 전처리된 이미지 생성
    preprocessed_img = preprocess_image(image_path)

    # EasyOCR로 텍스트 및 위치 정보 추출
    results = reader.readtext(preprocessed_img, detail=1)

    # 텍스트 위치 정보 저장
    texts_with_positions = []
    for (bbox, text, _) in results:
        x_min = min([point[0] for point in bbox])
        y_min = min([point[1] for point in bbox])
        x_max = max([point[0] for point in bbox])
        y_max = max([point[1] for point in bbox])
        box_height = y_max - y_min
        texts_with_positions.append({
            "text": text,
            "x_min": x_min,
            "y_min": y_min,
            "x_max": x_max,
            "y_max": y_max,
            "box_height": box_height
        })

    # 텍스트를 Y축 기준으로 정렬
    texts_with_positions = sorted(texts_with_positions, key=lambda x: x['y_min'])

    # 강조 텍스트와 설명 텍스트 그룹화
    grouped_texts = []
    current_group = []

    for i, current_text in enumerate(texts_with_positions):
        # 마지막 텍스트 처리
        if i == len(texts_with_positions) - 1:
            current_group.append(current_text)
            grouped_texts.append(current_group)
            break

        # 현재 텍스트와 다음 텍스트 비교
        next_text = texts_with_positions[i + 1]
        if next_text['y_min'] - current_text['y_max'] > current_text['box_height'] * 1.5:
            # 두 텍스트의 Y축 간격이 크면 다른 그룹으로 간주
            current_group.append(current_text)
            grouped_texts.append(current_group)
            current_group = []
        else:
            # 같은 그룹으로 간주
            current_group.append(current_text)

    # 강조 텍스트와 설명 텍스트 분리 및 정렬
    formatted_output = []
    for group in grouped_texts:
        if len(group) == 1:
            formatted_output.append(f"강조 텍스트: {group[0]['text']}")
        else:
            highlighted_text = group[0]['text']
            description_texts = " ".join([item['text'] for item in group[1:]])
            formatted_output.append(f"강조 텍스트: {highlighted_text}\n설명 텍스트: {description_texts}")

    return "\n\n".join(formatted_output)

# 메인 실행
if __name__ == "__main__":
    # 이미지 파일 경로
    image_path = "downloaded_image.png"

    # 강조 텍스트와 설명 텍스트 추출 및 정렬
    print("Extracting and formatting text...")
    final_output = extract_and_format_text(image_path)

    print("\n정렬된 텍스트:")
    print(final_output)
