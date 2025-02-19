from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# Set up Selenium WebDriver
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

# Function to get all job links from the main page
def get_job_links(driver):
    job_links = []
    try:
        job_cards = driver.find_elements(By.CLASS_NAME, "relative.w-full.md\\:flex-1.md\\:flex-grow.md\\:self-stretch")
        for card in job_cards:
            link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
            if link:
                job_links.append(link)
    except Exception as e:
        print(f"Error fetching job links: {e}")
    return job_links

# Function to extract job information from each job link
def extract_job_info(driver, job_url):
    try:
        driver.get(job_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "relative.w-full.px-4.md\\:px-6.md\\:max-w-screen-lg.overflow-visible.md\\:mx-auto"))
        )
        container = driver.find_element(By.CLASS_NAME, "relative.w-full.px-4.md\\:px-6.md\\:max-w-screen-lg.overflow-visible.md\\:mx-auto")
        img_tags = container.find_elements(By.TAG_NAME, "img")
        alt_texts = [img.get_attribute("alt") for img in img_tags if img.get_attribute("alt")]
        return alt_texts
    except Exception as e:
        print(f"Error fetching job info for {job_url}: {e}")
        return []

# Main scraper function with improved pagination handling
def scrape_jobs():
    driver = setup_driver()
    driver.get("https://zighang.com/it")
    
    all_job_data = []
    page = 1
    max_pages = 100  # Limit for testing or crawling

    try:
        while page <= max_pages:
            print(f"Fetching page {page}...")
            
            # Wait for job listings to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "relative.w-full.md\\:flex-1.md\\:flex-grow.md\\:self-stretch"))
            )
            
            # Get job links from the current page
            job_links = get_job_links(driver)
            if not job_links:
                print("No more job links found.")
                break

            # Visit each job link and extract information
            for job_link in job_links:
                print(f"Visiting job link: {job_link}")
                job_info = extract_job_info(driver, job_link)
                if job_info:
                    all_job_data.append({'URL': job_link, 'Alt Texts': job_info})

                # To avoid overloading the server
                time.sleep(1)

            # Try to find and click the next page button
            try:
                next_button = driver.find_element(By.CLASS_NAME, "pagination-next")  # Update class if necessary
                if next_button.is_enabled():  # Check if the button is clickable
                    next_button.click()
                    time.sleep(2)  # Wait for the next page to load
                else:
                    print("Next button is not enabled. Ending pagination.")
                    break
            except Exception as e:
                print(f"No next page found or navigation error: {e}")
                break

            page += 1

    finally:
        driver.quit()

    return all_job_data

# Run the scraper and save results
def main():
    job_data = scrape_jobs()
    if job_data:
        df = pd.DataFrame(job_data)
        df.to_csv('zighang_job_data_selenium2.csv', index=False)
        print("Job data saved to 'zighang_job_data_selenium2.csv'")
    else:
        print("No job data found.")

if __name__ == "__main__":
    main()
