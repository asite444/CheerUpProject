from fastapi import APIRouter
# from app.services.sqliteService import fetch_table_data

router = APIRouter()

@router.get("/combined_all")
def get_combined_all():
    """
    combined_all 테이블 데이터를 반환하는 엔드포인트.
    """
    data = 0
    print(data)
    if isinstance(data, dict) and "error" in data:
        return {"status": "error", "message": data["error"]}
    return {"status": "success", "data": data}

