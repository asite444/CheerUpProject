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




    report_top5 = sql.analyze_stack_top5(user_data)
    # report_user_tech ="현재 임시 차단"#gpt.analyze_user_tech(user_data)
    # report_improvement = gpt.analyze_improvement(user_data)
    # report_conclusion = gpt.analyze_conclusion(user_data)

    report_user_tech, report_improvement, report_conclusion = gpt.analyze_customize(user_data)

    report_graph_career = "\n".join(sql.career_graph_search(user_data))      # 경력 그래프
    report_graph_degree = "\n".join(sql.degree_graph_search(user_data))      # 학력 그래프
    report_graph_language =  "\n".join(sql.language_graph_search(user_data)) # 어학 그래프

    

    # JSON 응답 생성
    return JSONResponse(content={
        "report_top5": report_top5,
        "report_user_tech": report_user_tech,
        "report_improvement": report_improvement,
        "report_conclusion": report_conclusion,
        "report_graph_career":report_graph_career,
        "report_graph_degree":report_graph_degree,
        "report_graph_language":report_graph_language
        })