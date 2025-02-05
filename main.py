from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.controllers.home_controller import router as home_router
from app.controllers.googleTrandController import router as googleTrand_router
from fastapi.templating import Jinja2Templates
import os
app = FastAPI()

# 정적 파일 설정 (CSS, JS 등)
# app/static 경로를 명시적으로 설정
static_dir = os.path.join(os.path.dirname(__file__), "app/static")
print(f"Static directory path: {static_dir}")  # 디버깅용 출력

# 정적 파일 마운트
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# 템플릿 디렉터리 설정
templates_dir = os.path.join(os.path.dirname(__file__), "app/templates")
templates = Jinja2Templates(directory=templates_dir)

# 라우터 등록
app.include_router(home_router)
app.include_router(googleTrand_router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
# 실행 로컬접속URL http://127.0.0.1:8000/
# 실행 인터넷 접속 http://192.168.0.187:8000/