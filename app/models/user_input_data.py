from pydantic import BaseModel
from typing import List


class UserInputData(BaseModel):
    """
    사용자 입력 데이터
    """
    languages: List[str]
    frameworks: List[str]
    libraries: List[str]  
    devtools: List[str]
    jobs: List[str]
