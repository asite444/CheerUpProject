import pandas as pd
from kiwipiepy import Kiwi
from kiwipiepy.utils import Stopwords
import re
import sqlite3

# CSV 파일 불러오기
df = pd.read_csv(f'./csv/2025-01-24-12_final.csv')

# 'description'과 'requirement' 열 합치기 및 문자열로 변환
df['combined_text'] = df[['technicalTags', 'description', 'requirement']].fillna('').astype(str).agg(' '.join, axis=1)
df['preferredExperience'] = df['preferredExperience'].fillna('')

df['combined_text'] = df['combined_text'].apply(lambda cell: cell.replace(".", "").replace('/', ', ').lower() if isinstance(cell, str) else cell)
df['preferredExperience'] = df['preferredExperience'].apply(lambda cell: cell.replace(".", "").replace('/', ', ').lower() if isinstance(cell, str) else cell)

kiwi = Kiwi(typos='basic_with_continual_and_lengthening')

# 불용어 설정
stop_words = Stopwords()

# 파일 경로 설정
file_path = "./csv/technicalTags.txt"

# 파일에서 단어 읽기
with open(file_path, "r", encoding="utf-8") as f:
    words = f.read().splitlines()

words_remove = [word.replace('.', '').lower() for word in words]

# 사용자 사전에 단어 추가
for word in words_remove:
    kiwi.add_user_word(word, "NNG")

# SQLite 데이터베이스에서 기술 카테고리 데이터 로드
conn = sqlite3.connect("./asia.db")
cursor = conn.cursor()
cursor.execute("SELECT category, name, synonym FROM technical_element")
rows = cursor.fetchall()
conn.close()

# 데이터 정리
categories = {}
all_incorrect_list = []
replacement_map = {}

for category, name, synonym in rows:
    # category가 "language"이면 "it_language"로 변경
    if category.lower().strip() == "language":
        category = "it_language"

    synonyms = synonym.split(",")  # ','로 분리하여 리스트로 저장
    all_incorrect_list.extend(synonyms)  # 모든 동의어 리스트 저장
    
    if category not in categories:
        categories[category] = {}

    # name 자체도 정규화된 이름으로 포함
    categories[category][name] = name

    for syn in synonyms:
        replacement_map[syn.lower()] = name.lower().strip()  # 동의어 -> 올바른 명칭 매핑
        categories[category][syn] = name

# 사용자 사전에 단어 추가
for incorrec in all_incorrect_list:
    kiwi.add_user_word(incorrec, "NNG")

# 영어 여부 확인 함수
def is_english(word):
    return re.match(r'^[a-zA-Z0-9#+\-\s]+$', word) is not None

# 형태소 분석 함수
def analyze_text(text):
    if not isinstance(text, str):
        return []
    morphemes_kiwi = kiwi.tokenize(text, normalize_coda=True, stopwords=stop_words, split_complex=True)
    return [morph for morph, pos, _, _ in morphemes_kiwi if pos.startswith('N') or pos == 'SL']

# 형태소 리스트에서 영어 단어만 필터링
def filter_english_words(morphemes):
    if not isinstance(morphemes, list):
        return []
    return [word for word in morphemes if is_english(word)]

# 오탈자 수정 함수
def replace_typos(tokens, replacement_map):
    if not isinstance(tokens, list):
        return []
    return [replacement_map.get(token.lower(), token) for token in tokens]

# 형태소 분석 및 영어 필터링
df['morpheme'] = df['combined_text'].apply(analyze_text)
df['pre_morpheme'] = df['preferredExperience'].apply(analyze_text)

df['morpheme_eng'] = df['morpheme'].apply(filter_english_words)
df['pre_morpheme_eng'] = df['pre_morpheme'].apply(filter_english_words)

df['morpheme_eng'] = df['morpheme_eng'].apply(lambda x: replace_typos(x, replacement_map))
df['pre_morpheme_eng'] = df['pre_morpheme_eng'].apply(lambda x: replace_typos(x, replacement_map))

# 데이터 전처리: 소문자로 변환, 공백 및 '.' 제거
def preprocess(word):
    return word.lower().replace(".", "").replace(" ", "")

# 치환 및 분류 함수
def classify_and_replace(tokens, categories):
    if not isinstance(tokens, list):
        return []
    result = {key: set() for key in categories.keys()}
    for token in tokens:
        normalized_token = preprocess(token)
        for category, mapping in categories.items():
            if normalized_token in mapping:
                result[category].add(mapping[normalized_token])
    return result

# 각 카테고리에 대해 열 생성
for category in categories.keys():
    df[f'{category}'] = df['morpheme_eng'].apply(
        lambda x: ", ".join(sorted(classify_and_replace(x, categories)[category]))
    )
    df[f'pre_{category}'] = df['pre_morpheme_eng'].apply(
        lambda x: ", ".join(sorted(classify_and_replace(x, categories)[category]))
    )

# 학력 결정 함수
def determine_degree(tokens):
    if not isinstance(tokens, list):
        tokens = []
    if '학사' in tokens or '대졸' in tokens:
        return 1
    for i, token in enumerate(tokens):
        if token in ['대학교', '대학']:
            if any(next_token in ['졸업자', '졸업'] for next_token in tokens[i + 1:i + 11]):
                return 1
    if '석사' in tokens:
        return 2
    elif '석' in tokens:
        for i, token in enumerate(tokens[:-1]):
            if token == '석' and tokens[i + 1] == '박사':
                return 2
    if '박사' in tokens:
        return 2
    return 0

# 어학 조건 결정 함수
def determine_language(tokens):
    if not isinstance(tokens, list):
        tokens = []
    language_map = {'어학': 1, '외국어': 1, '영어': 1, '일본어': 2, '일어': 2, '중국어': 3, '중어': 3}
    for token in tokens:
        if token in language_map:
            return language_map[token]
    return None

# 학력 열 생성
df['degree'] = df['morpheme'].apply(determine_degree)

# 어학 열 생성
df['language'] = df['morpheme'].apply(determine_language)

# 필요한 열 정리 및 저장
col = ['text', 'id', 'url', 'title', 'location', 'duty', 'degree', 'language',
       'countryCode', 'company_name', 'crawling_dt', 'career',
       'combined_text','morpheme', 'morpheme_eng',
       'it_language', 'framework', 'library', 'tool',
       'preferredExperience', 'pre_morpheme', 'pre_morpheme_eng',
       'pre_it_language', 'pre_framework', 'pre_library', 'pre_tool',
       ]

df[col].to_csv(f'./csv/2025-01-24-12_categorized.csv', index=False, encoding='utf-8-sig')
