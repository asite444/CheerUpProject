import sqlite3

# 데이터베이스 파일 경로
DATABASE_PATH = "app/database/asia.db"

def get_connection():
    """
    SQLite 데이터베이스 연결 생성.
    """
    try:
        connection = sqlite3.connect(DATABASE_PATH)
        return connection
    except sqlite3.Error as e:
        print(f"SQLite 연결 오류: {e}")
        return None
