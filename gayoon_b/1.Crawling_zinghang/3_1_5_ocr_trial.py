# Hugging Face의 'ddobokki/ko-trocr' 모델
# 허깅페이스 모델 사용(한국어 인식) : 한국어에 특화된 OCR 모델로, 한글의 초성, 중성, 종성을 정확하게 인식하도록 설계
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

# 모델 및 프로세서 로드
processor = TrOCRProcessor.from_pretrained('ddobokki/ko-trocr')
model = VisionEncoderDecoderModel.from_pretrained('ddobokki/ko-trocr')

# 이미지 파일 경로
image_path = "downloaded_image.png"

# 이미지 열기 및 전처리
try:
    image = Image.open(image_path).convert("RGB")  # RGB로 변환
    image = image.resize((384, 384))  # 필요한 경우 크기 조정
except Exception as e:
    print(f"Error loading or preprocessing image: {e}")
    exit()

# 이미지 전처리 및 추론
try:
    pixel_values = processor(images=image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print("추출된 텍스트:\n", generated_text)
except Exception as e:
    print(f"Error processing OCR: {e}")
