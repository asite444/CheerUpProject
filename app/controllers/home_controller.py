from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import app.services.sqliteService as sql
import app.services.GPTAnalysisService as gpt
from app.models.user_input_data import UserInputData

import os

router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "../templates")
templates = Jinja2Templates(directory=templates_dir)



@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    '''
    main 화면 함수
    '''
        #기술명 데이터 조회해서 가져오기
    stack_data = sql.fetch_tech_stack()
    return templates.TemplateResponse(
        "main.html",  # HTML 템플릿 파일 이름
        {"request": request,"stack_data":stack_data}
        )




@router.post("/user-input-data")
async def process_user_data(user_data: UserInputData):
    # 데이터 수신 확인
    #print("Received Data:", user_data.dict())

    # 사용자가 이전에 선택한 기술선택이 존재하는지여부 판단(수정예정)
    # report=sql.is_existing_tech_stack(user_data)
    # if(report[0]):
    #     print(report[1])
    # else :
    #     print("없음")


    report = gpt.analyze_user_stack(user_data)
    report_graph_career = "\n".join(sql.career_graph_search(user_data))      # 경력 그래프
    report_graph_degree = "\n".join(sql.degree_graph_search(user_data))      # 학력 그래프
    report_graph_language =  "\n".join(sql.language_graph_search(user_data)) # 어학 그래프

    

    # JSON 응답 생성
    return JSONResponse(content={
        "report": report,
        "report_graph_career":report_graph_career,
        "report_graph_degree":report_graph_degree,
        "report_graph_language":report_graph_language
        })