import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64


def __init__(self, file_path):
        self.file_path = file_path
        self.data = None

def load_csv(self):
        try:
            self.data = pd.read_csv(self.file_path)
        except Exception as e:
            raise ValueError(f"CSV 파일 로드 실패: {e}")

def analyze_and_plot(self, column_name):
        """
        특정 열(column_name)의 그래프를 생성하여 base64 인코딩된 이미지로 반환
        """
        if self.data is None:
            raise ValueError("데이터가 로드되지 않았습니다. 먼저 load_csv()를 호출하세요.")

        if column_name not in self.data.columns:
            raise ValueError(f"'{column_name}' 열이 데이터에 존재하지 않습니다.")

        # 데이터 분석
        value_counts = self.data[column_name].value_counts()

        # 그래프 생성
        plt.figure(figsize=(10, 6))
        value_counts.plot(kind='bar', color='skyblue', edgecolor='black')
        plt.title(f"'{column_name}' 열의 데이터 분석 결과", fontsize=16)
        plt.xlabel(column_name, fontsize=14)
        plt.ylabel("빈도수", fontsize=14)
        plt.xticks(rotation=45, fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()

        # 그래프를 메모리에 저장하고 base64 인코딩
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        encoded_image = base64.b64encode(buffer.read()).decode('utf-8')
        buffer.close()
        plt.close()

        return encoded_image
@staticmethod
def generate_pie_chart(data):
        """
        원형 그래프를 생성하고 이미지 데이터를 반환.
        :param data: dict (예: {0: 81, 1: 60, ...})
        :return: 바이트 데이터 (PNG 이미지)
        """
        labels = [f"{key}년" for key in data.keys()]  # 레이블 생성
        values = list(data.values())  # 값 추출

        # 그래프 생성
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title("경력 분석")

        # 이미지를 메모리에 저장
        buffer = BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close()

        return buffer.getvalue()  # 바이트 데이터 반환


