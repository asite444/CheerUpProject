import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 기본 URL 설정
base_url = "https://zighang.com/it"

# 페이지의 HTML을 가져오는 함수
def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, "html.parser")
    else:
        print(f"Failed to fetch {url}: {response.status_code}")
        return None

# 메인 페이지에서 채용 공고 링크를 추출하는 함수
def get_job_links(soup):
    job_links = []
    job_cards = soup.find_all('a', class_='flex w-full flex-col justify-center gap-4 truncate rounded-2xl border border-gray-200 p-4 hover:shadow-md active:shadow-lg active:ring-2 active:ring-primary md:h-full md:gap-4 md:px-6 md:py-5 border-primary')
    for card in job_cards:
        link = card.get('href')
        if link:
            job_links.append("https://zighang.com" + link)
    return job_links

# 각 채용 공고 페이지에서 정보를 추출하는 함수
def extract_job_info(job_url):
    soup = fetch_page(job_url)
    if not soup:
        return None

    # 채용 직무
    job_title = soup.find('h1', class_='text-2xl font-bold').get_text(strip=True) if soup.find('h1', class_='text-2xl font-bold') else None

    # 회사 이름
    company_name = soup.find('p', class_='text-base').get_text(strip=True) if soup.find('p', class_='text-base') else None

    # 위치
    location = None
    location_tag = soup.find('div', class_='flex w-full items-center justify-start gap-1 text-sm')
    if location_tag:
        location = location_tag.find('span', class_='mt-0.5 break-keep text-[#9DA3AE]').get_text(strip=True) if location_tag.find('span', class_='mt-0.5 break-keep text-[#9DA3AE]') else None

    # 채용 내용
    job_content = ""
    content_sections = soup.find_all('section', class_='flex flex-col gap-4')
    for section in content_sections:
        headers = section.find_all('h2', class_='text-xl font-semibold')
        paragraphs = section.find_all('p', class_='text-base leading-relaxed')
        for header in headers:
            job_content += header.get_text(strip=True) + "\n"
        for paragraph in paragraphs:
            job_content += paragraph.get_text(strip=True) + "\n"

    return {
        '채용 공고 링크': job_url,
        '채용 직무': job_title,
        '회사 이름': company_name,
        '위치': location,
        '채용 내용': job_content
    }

# 전체 채용 공고를 수집하는 함수
def scrape_jobs():
    all_job_data = []
    page = 1
    max_pages = 5  # 테스트를 위해 페이지 수를 제한

    while page <= max_pages:
        print(f"Fetching page {page}...")
        url = f"{base_url}?page={page}"
        soup = fetch_page(url)
        if not soup:
            break

        # 현재 페이지에서 채용 공고 링크 추출
        job_links = get_job_links(soup)
        if not job_links:
            print("No more job links found.")
            break

        # 각 채용 공고 페이지 방문 및 정보 추출
        for job_link in job_links:
            print(f"Visiting job link: {job_link}")
            job_info = extract_job_info(job_link)
            if job_info:
                all_job_data.append(job_info)

            # 서버에 과부하를 주지 않기 위해 잠시 대기
            time.sleep(1)

        page += 1

    return all_job_data

# 수집한 데이터를 CSV 파일로 저장하는 함수
def main():
    job_data = scrape_jobs()
    if job_data:
        df = pd.DataFrame(job_data)
        df.to_csv('zighang_job_data.csv', index=False)
        print("Job data saved to 'zighang_job_data.csv'")
    else:
        print("No job data found.")

if __name__ == "__main__":
    main()
