# 채용 링크 한 번에 모두 수집(640건 중 630건 완료) 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Setup Selenium WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode (can remove for debugging)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# Scroll down the page to load more content
def scroll_down(driver):
    scroll_pause_time = 2  # Time to wait after each scroll
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        # Scroll down to the bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # If heights are the same, we've reached the bottom
            break
        last_height = new_height

# Extract job details from each job link
def extract_job_details(driver, job_link):
    driver.get(job_link)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.relative"))
    )
    
    job_data = {
        "채용 공고 링크": job_link,
        "채용 직무": None,
        "회사 이름": None,
        "채용 내용": None
    }
    
    try:
        # Extract job title
        title_element = driver.find_element(By.CSS_SELECTOR, "h1.text-2xl.font-bold")
        job_data["채용 직무"] = title_element.text.strip()

        # Extract company name
        company_element = driver.find_element(By.CSS_SELECTOR, "p.text-base")
        job_data["회사 이름"] = company_element.text.strip()

        # Extract job description or details
        details_element = driver.find_element(By.CSS_SELECTOR, "div.details-class")  # Update selector as needed
        job_data["채용 내용"] = details_element.text.strip()
    except Exception as e:
        print(f"Error extracting details from {job_link}: {e}")

    return job_data

# Main function to scrape job posts
def scrape_jobs():
    driver = setup_driver()
    driver.get("https://zighang.com/it")
    all_job_data = []

    try:
        print("Scrolling to load all job postings...")
        scroll_down(driver)  # Scroll to load all job postings

        print("Fetching job links...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.relative.w-full.md\\:flex-1.md\\:flex-grow.md\\:self-stretch")
            )
        )
        
        # Extract job links
        job_elements = driver.find_elements(
            By.CSS_SELECTOR, "div.relative.w-full.md\\:flex-1.md\\:flex-grow.md\\:self-stretch"
        )
        job_links = [
            job.find_element(By.TAG_NAME, "a").get_attribute("href") for job in job_elements
        ]

        print(f"Found {len(job_links)} job links. Extracting details...")

        # Visit each job link and extract details
        for job_link in job_links:
            print(f"Visiting job link: {job_link}")
            job_details = extract_job_details(driver, job_link)
            all_job_data.append(job_details)
            time.sleep(1)

    finally:
        driver.quit()

    return all_job_data

# Save data to a DataFrame and CSV
def main():
    job_data = scrape_jobs()
    if job_data:
        df = pd.DataFrame(job_data)
        df.to_csv("zighang_jobs.csv", index=False)
        print("Job data saved to 'zighang_jobs.csv'")
    else:
        print("No job data found.")

if __name__ == "__main__":
    main()
