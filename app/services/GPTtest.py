import os
import ast
import pandas as pd

from openai import OpenAI
from dotenv import load_dotenv

def get_api_key():
    # 프로젝트 루트의 .env 파일을 로드 (web/.env)
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    load_dotenv(dotenv_path)

    # 환경 변수에서 API_KEY 가져오기
    API_KEY = os.getenv("CHATGPT_API_KEY")
    return API_KEY

def get_openai_response(prompt, model='gpt-3.5-turbo', temperature=0.5):
    # ChatGPT API를 이용용
    client = OpenAI(api_key=get_api_key())
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": "당신은 IT 전문가입니다. 주어진 질문에 모두 답하세요.단, 간결하게 답변하세요"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content