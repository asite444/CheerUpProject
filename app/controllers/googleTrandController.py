import warnings
import pandas as pd
from fastapi import APIRouter, Request,Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pytrends.request import TrendReq
from fastapi.responses import JSONResponse
import matplotlib
from time import sleep
templates = Jinja2Templates(directory="templates")


router = APIRouter()




@router.post("/process/")
async def googleTrandSearch(keywords: str = Form(...)):
    """
    사용자로부터 원하는 데이터를 넘겨받아 Google Trends 검색을 수행하고, 그래프 이미지를 반환하는 함수
    """
    import io
    import matplotlib.pyplot as plt
    from matplotlib import rc
    from pytrends.request import TrendReq
    from fastapi.responses import StreamingResponse

    # 한글 폰트 설정
    rc('font', family='Malgun Gothic')
    plt.rcParams['axes.unicode_minus'] = False

    # Google Trends 연결
    pytrends = TrendReq(hl='ko-KR', tz=360, timeout=(10, 25))

    # 키워드 처리
    keywords_list = keywords.split(',')
    keywords_list = [keyword.strip() for keyword in keywords_list]

    # Google Trends 데이터 요청
    pytrends.build_payload(keywords_list, timeframe='today 12-m', geo='KR')
    data = pytrends.interest_over_time().reset_index().drop(columns=['isPartial'])

    # 그래프 생성
    plt.figure(figsize=(12, 6))
    for keyword in keywords_list:
        plt.plot(data['date'], data[keyword], label=keyword)

    plt.title('Google Trends: 사용자 키워드', fontsize=16)
    plt.xlabel('날짜', fontsize=12)
    plt.ylabel('관심도', fontsize=12)
    plt.legend(title='키워드')
    plt.grid()

    # 이미지를 메모리 버퍼에 저장
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    # StreamingResponse로 반환 (버퍼 닫기 지연)
    return StreamingResponse(buf, media_type="image/png")

@router.post("/process_ajax/")
async def googleTrandSearch_ajax(keywords: str = Form(...)):
    import io
    import matplotlib.pyplot as plt
    from matplotlib import rc
    from pytrends.request import TrendReq
    from fastapi.responses import StreamingResponse

    rc('font', family='Malgun Gothic')
    plt.rcParams['axes.unicode_minus'] = False

    try:
        pytrends = TrendReq(hl='ko-KR', tz=360, timeout=(10, 25))
        keywords_list = [keyword.strip() for keyword in keywords.split(',')]

        # 요청 사이에 딜레이 추가
        sleep(1)  # 10초 딜레이 (적절히 조정 가능)
        
        pytrends.build_payload(keywords_list, timeframe='today 12-m', geo='KR')
        data = pytrends.interest_over_time()

        if data.empty:
            plt.figure(figsize=(12, 6))
            plt.text(0.5, 0.5, "No data available", ha='center', va='center', fontsize=16)
            plt.axis('off')

            buf = io.BytesIO()
            plt.savefig(buf, format="png")
            buf.seek(0)
            plt.close()
            return StreamingResponse(buf, media_type="image/png")

        data = data.infer_objects(copy=False).fillna(False).reset_index()

        plt.figure(figsize=(12, 6))
        for keyword in keywords_list:
            if keyword in data.columns:
                plt.plot(data['date'], data[keyword], label=keyword)

        plt.title('Google Trends')
        plt.xlabel('Date')
        plt.ylabel('Interest Over Time')
        plt.legend()
        plt.grid()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        return {"error": f"Error: {str(e)}"}