from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import app.services.sqliteService as sql
import app.services.GPTAnalysisService as gpt
from app.models.user_input_data import UserInputData

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

    # 데이터 처리 및 HTML 텍스트 생성
    languages = ", ".join(user_data.languages) if user_data.languages else "없음"
    frameworks = ", ".join(user_data.frameworks) if user_data.frameworks else "없음"
    libraries=  ", ".join(user_data.libraries) if user_data.libraries else "없음"
    devtools=  ", ".join(user_data.devtools) if user_data.devtools else "없음"
    jobs=  ", ".join(user_data.jobs) if user_data.jobs else "없음"

    career_html = "\n".join(sql.career_graph_search(user_data))  # 리스트를 HTML로 변환

    report = f"""
    <h1>분석 결과</h1>
    <p><strong>직업:</strong> {jobs}</p>
    <p><strong>언어:</strong> {languages}</p>
    <p><strong>프레임워크:</strong> {frameworks}</p>
    <p><strong>라이브러리:</strong> {libraries}</p>
    <p><strong>개발툴:</strong> {devtools}</p>

    
    <h2>주요 언어 Top 5 언어에 대한 설명</h2>
    <p>(자격 조건이 높은 언어 먼저 나오고 그 다음에 우대 조건 기준 정렬)</p>

    <ul>
        <li><strong>Python (자격 조건: 10.51%, 우대 조건: 15.99%)</strong><br>
            데이터 분석, 인공지능, 웹 개발 등에 활용되는 다목적 프로그래밍 언어. Django 및 Flask와 함께 백엔드 개발에 많이 사용됨.
        </li>
        <li><strong>Java (자격 조건: 14.27%, 우대 조건: 9.30%)</strong><br>
            객체 지향 프로그래밍 언어로, 엔터프라이즈 애플리케이션과 대규모 시스템 개발에서 널리 사용되며, Spring 프레임워크와 함께 활용됨.
        </li>
        <li><strong>JavaScript (자격 조건: 2.77%, 우대 조건: 4.94%)</strong><br>
            웹 개발의 필수 언어로, 프론트엔드와 백엔드(Node.js) 개발 모두 가능하며, 다양한 프레임워크 및 라이브러리를 지원함.
        </li>
        <li><strong>HTML/CSS (자격 조건: 2.97%, 우대 조건: 0.87%)</strong><br>
            웹 페이지의 구조(HTML)와 디자인(CSS)을 구성하는 기본 요소로, 백엔드 개발에서도 프론트엔드와의 연계를 위해 필요함.
        </li>
    </ul>

    <h2>사용자의 기술 분석</h2>

    <h3>강점 분석</h3>
    <ul>
        <li><strong>Python과 Java 모두 활용 가능</strong> → Python 기반의 빠른 웹 개발과 Java 기반의 대규모 애플리케이션 개발 모두 대응 가능</li>
        <li><strong>JavaScript 사용 가능</strong> → Node.js 활용 시 풀스택 개발이 가능하여 채용 시장에서 경쟁력 강화</li>
        <li><strong>기본적인 프론트엔드 기술 보유</strong> → 웹 개발 환경에서 백엔드와의 연계성을 높일 수 있음</li>
    </ul>

    <h3>보완 사항</h3>
    <ul>
        <li>Top 5 기술 중에서 1, 2위의 기술이 사용자의 기술 스택에 없다면 공부할 것을 권장 (확률과 함께 제공)</li>
        <li>사용자가 입력한 프레임워크에 대해 확률이 높은 3개의 기술 조합 추천</li>
    </ul>

    <h2>많이 사용되는 언어 조합</h2>
    <ul>
        <li><strong>Python & Java (자격 조건: 1.78%, 우대 조건: 1.74%)</strong> → 백엔드 개발에서 많이 활용됨.</li>
        <li><strong>Java & JavaScript (자격 조건: 1.88%, 우대 조건: 0.29%)</strong> → 웹 개발 및 서버-클라이언트 연계 개발에 자주 사용됨.</li>
        <li><strong>JavaScript & TypeScript (자격 조건: 4.76%, 우대 조건: 2.03%)</strong> → 프론트엔드 및 풀스택 개발을 위한 필수 조합.</li>
        <li><strong>Python & TypeScript (자격 조건: 0.69%, 우대 조건: 0.58%)</strong> → 백엔드 API 개발에 적합한 조합.</li>
    </ul>

    <h2>주요 백엔드 프레임워크 Top 5</h2>
        
        <ol>
            <li>
                <strong>Node.js</strong> (자격 조건: 11.05%, 우대 조건: 2.1%)<br>
                자바스크립트 런타임 환경. 서버 사이드 애플리케이션 개발에 널리 활용됩니다. 
                백엔드 직무에서 <strong>비동기 처리와 실시간 데이터 처리</strong>가 필요한 애플리케이션(예: 채팅 서비스, 스트리밍 서버) 개발에 활용됩니다.
                JavaScript 기반으로 <strong>프론트엔드와 백엔드의 통합 개발</strong>이 용이하며, Express.js 등의 프레임워크와 함께 사용됩니다.
            </li>
            <li>
                <strong>Spring</strong><br>
                백엔드 직무에서 <strong>대규모 엔터프라이즈 애플리케이션</strong> 개발에 활용됩니다. 
                객체 지향 설계를 기반으로 한 <strong>의존성 주입(DI)</strong> 및 <strong>트랜잭션 관리 기능</strong>을 제공하여 유지보수와 확장성이 뛰어나며, 
                금융, 공공기관, 기업 시스템 등에 널리 사용됩니다.
            </li>
            <li>
                <strong>Spring Boot</strong><br>
                백엔드 직무에서 <strong>빠른 애플리케이션 개발 및 배포</strong>가 필요할 때 활용됩니다.
                기존 Spring보다 설정이 간소화되어, <strong>마이크로서비스 아키텍처(MSA)</strong> 및 RESTful API 개발에 최적화되어 있습니다. 
                자동 설정 기능과 내장 서버(Tomcat, Jetty)를 지원하여 개발 시간을 단축할 수 있습니다.
            </li>
            <li>
                <strong>Django</strong><br>
                백엔드 직무에서 <strong>데이터 중심 웹 애플리케이션</strong> 개발에 활용됩니다.
                <strong>ORM(Object-Relational Mapping)</strong> 기능을 제공하여 데이터베이스와의 연동이 쉽고, 
                보안 기능이 내장되어 있어 <strong>관리 시스템, 블로그, 웹 애플리케이션</strong> 등에서 많이 사용됩니다.
            </li>
            <li>
                <strong>NestJS</strong><br>
                백엔드 직무에서 <strong>대규모 TypeScript 기반 애플리케이션</strong> 개발에 활용됩니다.
                <strong>모듈화된 아키텍처</strong>와 <strong>의존성 주입(DI)</strong>을 통해 확장성과 유지보수성을 높일 수 있으며, 
                GraphQL, WebSockets 등의 기능을 쉽게 구현할 수 있어 <strong>API 서버 및 마이크로서비스 개발</strong>에 적합합니다.
            </li>
        </ol>

    <h2>사용자의 강점 분석</h2>
    <p>사용자의 기술 스택과 요구 기술을 비교하여 부족한 부분을 보완할 방법을 제안</p>

    <h2>추천 학습 방향</h2>
    <ul>
        <li>Spring 학습 필수: Java 기반의 백엔드 채용 확률이 높음.</li>
        <li>Node.js 기반 Express.js 학습: 백엔드 개발에서 Node.js의 활용도를 높이기 위해 추천.</li>
        <li>FastAPI 학습 고려: Python 백엔드 개발에서 Flask보다 빠른 성능을 제공하며, 현대적인 API 개발에 적합.</li>
    </ul>
    <h2>경력</h2>
    {career_html}  <!-- career 이미지가 삽입될 부분 -->
    """ 

    # JSON 응답 생성
    return JSONResponse(content={"message": report})