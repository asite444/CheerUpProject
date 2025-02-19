import json
import sqlite3
import pandas as pd

path = './sql'

def insert_duty(cursor):
    duty_dict = {
        "PM": ["개발PM", "개발 매니저", "프로덕트 매니저"],
        "데이터 직무": ["DBA", "데이터 엔지니어링", "데이터 엔지니어", "빅데이터 엔지니어"],
        "백엔드": ["서버/백엔드", "서버 개발자", "웹 개발자"],
        "인프라 엔지니어": ["데브옵스", "인터넷 보안", "DevOps / 시스템 관리자", "보안 엔지니어", "네트워크 관리자", "소프트웨어 엔지니어"],
        "앱 개발자": ["iOS", "안드로이드", "안드로이드 개발자", "iOS 개발자", "크로스플랫폼 앱 개발자"],
        "게임": ["모바일 게임", "게임 클라이언트", "게임 서버"],
        "AI": ["머신러닝", "인공지능(AI)", "머신러닝 엔지니어", "음성 엔지니어"],
        "임베디드": ["사물인터넷(IoT)", "로보틱스 미들웨어", "임베디드 소프트웨어", "하드웨어 엔지니어", "임베디드 개발자", "시스템 소프트웨어"],
        "프론트 엔드": ["웹 퍼블리싱", "웹 퍼블리셔", "프론트엔드 개발자", "그래픽스", "그래픽스 엔지니어", "크로스 플랫폼", "프론트엔드"],
        "QA": ["QA", "테스트 엔지니어"],
        "데이터 분석": ["데이터 분석", "BI 엔지니어", "데이터 사이언티스트"],
        "VR": ["VR/AR/3D", "VR 엔지니어"],
        "시스템": ["시스템/네트워크", "응용 프로그램", "시스템"],
        "블록체인": ["블록체인", "블록체인 플랫폼 엔지니어"],
        "ERP": ["ERP전문가"],
        "언어별 개발자": ["파이썬 개발자", "자바 개발자", "C", "C++ 개발자", ".NET 개발자", "Node.js 개발자", "PHP 개발자"]
    }

    purchases = []
    for idx, val in duty_dict.items():
        purchases.append((idx, ','.join(val)))

    try:
        cursor.executemany("INSERT INTO duty_element VALUES (?, ?)", purchases)
        return True
    except Exception as e:
        print('duty INSERT ERROR')
        print(e)
        return False

def insert_technical(cursor):
    with open(path + '/technical_categories.json', 'r') as f:
        json_data = json.load(f)

    seq = 0
    purchases = []
    for category in json_data.keys():
        for key in json_data[category].keys():
            purchases.append((seq, category, key, ','.join(json_data[category][key])))
            seq += 1
    
    try:
        cursor.execute("DELETE FROM technical_element")
        cursor.executemany("INSERT INTO technical_element VALUES (?, ?, ?, ?)", purchases)
        return True
    except Exception as e:
        print('technical_element INSERT ERROR')
        print(e)
        return False

def read_df():
    df = pd.read_csv(path + '/2025-01-24-12_categorized.csv')
    return df

def insert_original(cursor, df):
    purchases = []
    for idx, val in df.iterrows():
        purchases.append((idx, val['url'], val['text'], val['crawling_dt']))
    
    try:
        cursor.executemany("INSERT INTO original VALUES (?, ?, ?, ?)", purchases)
        return True
    except Exception as e:
        print('original INSERT ERROR')
        print(e)
        return False

def insert_processing(cursor, df):
    purchases = []
    for idx, val in df.iterrows():
        purchases.append((idx, val['url'], val['title'], val['location'], val['company_name'], val['duty'], val['degree'], val['language'], val['career'], val['morpheme'], val['pre_morpheme'], val['it_language'], val['framework'], val['library'], val['tool'], val['pre_it_language'], val['pre_framework'], val['pre_library'], val['pre_tool'], val['crawling_dt']))
    
    try:
        cursor.executemany("INSERT INTO processing VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", purchases)
        return True
    except Exception as e:
        print('processing INSERT ERROR')
        print(e)
        return False

def insert_skill_probability(cursor):
    df = pd.read_csv(path + '/skill_probability.csv')

    purchases = []
    for idx, val in df.iterrows():
        purchases.append((idx, val['duty'], val['category'], val['skill'], val['probability'], val['probability_pre']))
    
    try:
        cursor.executemany("INSERT INTO skill_probability VALUES (?, ?, ?, ?, ?, ?)", purchases)
        return True
    except Exception as e:
        print('skill_probability INSERT ERROR')
        print(e)
        return False

def main():
    connect = sqlite3.connect('asia.db')
    cursor = connect.cursor()

    if not insert_duty(cursor):
        return False
    if not insert_technical(cursor):
        return False

    df = read_df()
    if not insert_original(cursor, df):
        return False
    if not insert_processing(cursor, df):
        return False
    
    if not insert_skill_probability(cursor):
        return False

    connect.commit()
    connect.close()


if __name__ == '__main__':
    main()