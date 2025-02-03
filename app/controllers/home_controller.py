from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import app.services.sqliteService as sql
from app.services.graph_service import  generate_pie_chart 
from app.models.user_input_data import UserInputData
from app.models.user_input_data import SearchRequest
import os
from typing import List, Optional
router = APIRouter()

templates_dir = os.path.join(os.path.dirname(__file__), "../templates")
templates = Jinja2Templates(directory=templates_dir)



@router.get("/", response_class=HTMLResponse)
async def read_home(request: Request):
    '''
    main 화면 함수
    '''
    test_file_path = os.path.join(os.path.dirname(__file__), "../../data/backlang.txt")
    backend_language_analysis_path = os.path.join(os.path.dirname(__file__), "../../data/backend_language_analysis.txt")

    try:
        # 파일 읽기
        with open(test_file_path, "r", encoding="utf-8") as file:
            back_lang = file.read()
        with open(backend_language_analysis_path, "r", encoding="utf-8") as file:
            lang_text = file.read()

        #기술명 데이터 조회해서 가져오기
        stack_data = sql.fetch_tech_stack()
        #print(stack_data)
        #career_data = {0: 81, 1: 60, 2: 99, 3: 312, 4: 45, 5: 200, 6: 27, 7: 54, 8: 14, 9: 2, 10: 22, 15: 2}
        #graph_image = generate_pie_chart(career_data)

        # HTML 템플릿 렌더링
        return templates.TemplateResponse(
            "main.html",  # HTML 템플릿 파일 이름
            {"request": request, "back_lang": back_lang,"lang_text":lang_text,"stack_data":stack_data,"graph_image":"/career-chart/"}
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.post("/search-category")
# async def search_ajax(search_request: SearchRequest):
#     '''
#     카테고리별 검색
#     '''
#      # 요청 데이터 출력
#     print("Category:", search_request.category)
#     print("Keyword:", search_request.keyword)
#     searched_data=sql.category_search(search_request)

#     return JSONResponse(content={"searched_data": searched_data})



@router.post("/user-input-data")
async def process_user_data(user_data: UserInputData):
    # 데이터 수신 확인
    print("Received Data:", user_data.dict())

    # 데이터 처리 및 HTML 텍스트 생성
    languages = ", ".join(user_data.languages) if user_data.languages else "없음"
    frameworks = ", ".join(user_data.frameworks) if user_data.frameworks else "없음"
    libraries=  ", ".join(user_data.libraries) if user_data.libraries else "없음"
    devtools=  ", ".join(user_data.devtools) if user_data.devtools else "없음"
    jobs=  ", ".join(user_data.jobs) if user_data.jobs else "없음"



    report = f"""
    <h1>분석 결과</h1>
    <p><strong>직업:</strong> {jobs}</p>
    <p><strong>언어:</strong> {languages}</p>
    <p><strong>프레임워크:</strong> {frameworks}</p>
    <p><strong>라이브러리:</strong> {libraries}</p>
    <p><strong>개발툴:</strong> {devtools}</p>
\


    <hr>
    <h2>추천 리포트</h2>
    <ul>
        <li><strong>기술 스택 강화:</strong> {languages}를 활용한 다양한 알고리즘 문제를 해결하며, 언어에 대한 깊은 이해를 쌓아보세요.</li>
        <li><strong>프레임워크 학습:</strong> {frameworks}를 활용하여 RESTful API를 설계하고, 대규모 시스템 설계를 연습해보세요.</li>
        <li><strong>라이브러리 활용:</strong> {libraries}를 사용하여 데이터 처리, 시각화 및 머신러닝을 적용해보세요.</li>
        <li><strong>개발툴 숙달:</strong> {devtools}를 통해 개발 환경을 최적화하고, 협업 생산성을 높이세요.</li>
   \
    </ul>
    <hr>
    <h3>세부 분석 및 제안</h3>
    <p>현재 선택하신 기술 스택과 프레임워크는 현대 IT 시장에서 높은 수요를 보이고 있습니다. {languages}와 같은 언어는 강력한 도구로 작용하며, {frameworks}는 빠른 개발과 안정성을 제공합니다.</p>
    <p>{libraries} 라이브러리는 데이터 분석, 머신러닝 및 이미지 처리를 포함한 다양한 분야에서 강력한 도구로 활용됩니다.</p>
    <p>{devtools} 개발툴은 개발 생산성을 높이고 팀 협업을 강화하는 데 필수적인 도구입니다.</p>
    
   
    <hr>
    <h3>추가 학습 및 추천 강의</h3>
    <ul>
        <li><strong>머신러닝 및 데이터 분석:</strong> {libraries} 라이브러리를 활용하여 데이터 중심의 프로젝트를 진행해보세요.</li>
        <li><strong>클라우드 컴퓨팅:</strong> AWS, GCP, Azure 플랫폼을 활용한 실습 프로젝트에 참여해보세요.</li>
        <li><strong>DevOps 도구 활용:</strong> {devtools}를 사용하여 CI/CD 파이프라인을 설정하고 팀의 생산성을 높이세요.</li>
        <li><strong>글로벌 프로젝트 준비:</strong> 국제 IT 협업을 위한 Agile 및 DevOps 워크플로우를 학습하세요.</li>
    </ul>
    <p>지속적으로 최신 기술 트렌드를 파악하며, 실무에서 이를 효과적으로 활용할 수 있는 방법을 고민해보세요. 성장 가능성이 무궁무진하니, 현재의 기술을 강화하며 새로운 기회를 모색해보시길 바랍니다.</p>
    """


    # JSON 응답 생성
    return JSONResponse(content={"message": report})