import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# Base URL
base_url = "https://zighang.com/it"

# Function to fetch a page's soup
def fetch_page(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return BeautifulSoup(response.content, "html.parser")
    else:
        print(f"Failed to fetch {url}: {response.status_code}")
        return None

# Function to get all job links from the main page
def get_job_links(soup):
    job_links = []
    job_cards = soup.find_all('div', class_='relative w-full md:flex-1 md:flex-grow md:self-stretch')
    for card in job_cards:
        link = card.find('a', href=True)
        if link:
            job_links.append(link['href'])
    return job_links

# Function to extract job information from each job link
def extract_job_info(job_url):
    soup = fetch_page(job_url)
    if not soup:
        return None
    # Find the specific div containing the img tag
    container = soup.find('div', class_='relative w-full px-4 md:px-6 md:max-w-screen-lg overflow-visible md:mx-auto')
    if not container:
        print(f"No container found for {job_url}")
        return None
    img_tags = container.find_all('img')
    alt_texts = []
    for img in img_tags:
        alt_text = img.get('alt')
        if alt_text:
            alt_texts.append(alt_text)
    return alt_texts

# Main scraper function
def scrape_jobs():
    all_job_data = []
    page = 1
    max_pages = 5  # Limit the number of pages to crawl for testing
    
    while page <= max_pages:
        print(f"Fetching page {page}...")
        url = f"{base_url}?page={page}"
        soup = fetch_page(url)
        if not soup:
            break

        # Get job links from the current page
        job_links = get_job_links(soup)
        if not job_links:
            print("No more job links found.")
            break

        # Visit each job link and extract information
        for job_link in job_links:
            full_url = f"https://zighang.com{job_link}"
            print(f"Visiting job link: {full_url}")
            job_info = extract_job_info(full_url)
            if job_info:
                all_job_data.append({'URL': full_url, 'Alt Texts': job_info})

            # To avoid overloading the server
            time.sleep(1)

        page += 1

    return all_job_data

# Run the scraper and save results
def main():
    job_data = scrape_jobs()
    if job_data:
        df = pd.DataFrame(job_data)
        df.to_csv('zighang_job_data1.csv', index=False)
        print("Job data saved to 'zighang_job_data1.csv'")
    else:
        print("No job data found.")

if __name__ == "__main__":
    main()