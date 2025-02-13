# Python 3.9 이미지 사용
FROM python:3.9

# 작업 디렉토리 설정
WORKDIR /app

# `requirements.txt` 복사 및 패키지 설치
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 전체를 컨테이너 내부 `/app` 디렉토리로 복사
COPY ../ ./

# FastAPI 실행 (app.main이 아니라 main.py를 직접 실행)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

