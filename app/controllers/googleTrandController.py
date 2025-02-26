from fastapi import APIRouter, Form
import io
import matplotlib.pyplot as plt
from matplotlib import rc
from pytrends.request import TrendReq
from fastapi.responses import StreamingResponse, JSONResponse

router = APIRouter()

# 한글 폰트 설정
rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

@router.post("/process_ajax/")
async def googleTrandSearch_ajax(keywords: str = Form(...)):
    try:
        pytrends = TrendReq(hl='ko-KR', tz=360, timeout=(5, 15))  # 타임아웃 값 축소
        keywords_list = [keyword.strip() for keyword in keywords.split(',')]

        # Google Trends 데이터 요청
        pytrends.build_payload(keywords_list, timeframe='today 12-m', geo='KR')
        data = pytrends.interest_over_time()

        # 데이터가 없을 경우 예외 처리
        if data.empty:
            return JSONResponse(content={"error": "No data available"}, status_code=404)

        # fillna(False) 대신 infer_objects(copy=False) 적용
        data = data.drop(columns=['isPartial'], errors='ignore').infer_objects(copy=False).reset_index()

        # 그래프 생성
        plt.figure(figsize=(10, 5))
        for keyword in keywords_list:
            if keyword in data.columns:
                plt.plot(data['date'], data[keyword], label=keyword)

        plt.title('Google Trends Search Trend')  # ✅ 영어로 변경
        plt.xlabel('Date')  # ✅ 영어로 변경
        plt.ylabel('Search Interest')  # ✅ 영어로 변경
        plt.legend()
        plt.grid()

        # ✅ 안내 문구 최상단 중앙에 배치 (최대한 기존 코드 유지)
        max_value = max(data[keywords_list].max()) if not data.empty else 100  # y축 최대값
        center_x = data['date'].iloc[len(data) // 2]  # x축 중앙 (가운데 날짜)

        # plt.text(center_x, max_value + (max_value * 0.1), 
        #          "이 그래프는 6개월간 검색 정도를 나타내는 그래프입니다.", 
        #          fontsize=10, color='gray', ha='center', fontweight='bold')

        # 이미지 반환
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight")  # ✅ bbox_inches="tight" 추가
        buf.seek(0)
        plt.close()

        return StreamingResponse(buf, media_type="image/png")

    except Exception as e:
        print(e)
        return JSONResponse(content={"error": f"Error: {str(e)}"}, status_code=500)
