from pydantic import BaseModel
from typing import List


class UserInputData(BaseModel):
    """
    사용자 입력 데이터
    """
    languages: List[str]
    frameworks: List[str]
    libraries: List[str]  # 기존 오타 수정 (librarys -> libraries)
    devtools: List[str]
    jobs: List[str]

class SearchRequest(BaseModel):
    '''
    사용자 검색데이터
    '''
    category: str
    keyword: str