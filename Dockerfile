# Python 3.9 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# 먼저 `requirements.txt`를 복사
COPY requirements.txt /app/

# 패키지 설치
RUN pip install --no-cache-dir -r /app/requirements.txt

# 프로젝트 전체 복사
COPY . /app/

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
