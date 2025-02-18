from fastapi import APIRouter, Form
import io
import matplotlib.pyplot as plt
from matplotlib import rc
from pytrends.request import TrendReq
from fastapi.responses import StreamingResponse, JSONResponse
import time

router = APIRouter()

rc('font', family='Malgun Gothic')
plt.rcParams['axes.unicode_minus'] = False

@router.post("/process_ajax/")
async def googleTrandSearch_ajax(keywords: str = Form(...)):
    try:
        pytrends = TrendReq(hl='ko-KR', tz=360, timeout=(10, 25))
        keywords_list = [keyword.strip() for keyword in keywords.split(',')]

        time.sleep(1)  # 딜레이 감소

        pytrends.build_payload(keywords_list, timeframe='today 12-m', geo='KR')
        data = pytrends.interest_over_time()

        if data.empty:
            return JSONResponse(content={"error": "No data available"}, status_code=404)

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
        return JSONResponse(content={"error": f"Error: {str(e)}"}, status_code=500)
