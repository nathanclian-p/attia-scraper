import os
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ------------------ CONFIG ------------------

BASE_URL = "https://podscripts.co"
SEARCH_URL_TEMPLATE = (
    "https://podscripts.co/podkeywordsearch/"
    "?search_type=basic&keywordsToSearch=drive&exact_match=false"
    "&slv=single&podSelectedId=75&page={page}"
)

Path("out").mkdir(exist_ok=True)

# ------------------ SETUP SELENIUM ------------------

service = Service()  # auto-detects chromedriver on PATH

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=service, options=options)

# ------------------ COLLECT LINKS ------------------

episode_urls = set()

for page_num in range(1, 20):
    url = SEARCH_URL_TEMPLATE.format(page=page_num)
    print(f"\n=== Fetching page {page_num} === {url}")
    driver.get(url)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Transcript"))
        )
    except:
        print("No transcripts found. Stopping pagination.")
        break

    links = driver.find_elements(By.PARTIAL_LINK_TEXT, "View Full Transcript")
    print(f"Found {len(links)} transcript links on page {page_num}")

    if not links:
        break

    for link in links:
        href = link.get_attribute("href")
        if href:
            full_url = BASE_URL + href if href.startswith("/") else href
            episode_urls.add(full_url)

print(f"\nTotal episodes found: {len(episode_urls)}")

# ------------------ DOWNLOAD TRANSCRIPTS ------------------

for url in sorted(episode_urls):
    slug = url.rstrip("/").split("/")[-1].split("?")[0]
    fname = Path("out", f"{slug}.txt")

    if fname.exists():
        continue

    driver.get(url)

    try:
        # Click Transcript tab if present
        try:
            transcript_tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//li[normalize-space()='Transcript']")
                )
            )
            transcript_tab.click()
            time.sleep(1)

        except:
            print(f"No transcript tab for {url}. Trying fallback scrape...")

        # Try to locate the podcast-transcript div
        try:
            transcript_div = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class, 'podcast-transcript')]")
                )
            )
            text = transcript_div.text.strip()

            if len(text) < 500:
                print(f"Transcript for {slug} is suspiciously short. Skipping.")
                continue

            fname.write_text(text, encoding="utf-8")
            print(f"Saved transcript: {fname}")
            continue

        except:
            print(f"No podcast-transcript div found on {url}. Trying to scrape page body.")

        # Fallback: scrape entire page body
        page_text = driver.find_element(By.TAG_NAME, "body").text

        if "premium subscribers only" in page_text.lower():
            print(f"Episode {slug} is premium-only. Skipping.")
            continue

        if len(page_text) < 500:
            print(f"Teaser for {slug} too short. Skipping.")
            continue

        fname.write_text(page_text.strip(), encoding="utf-8")
        print(f"Saved fallback page text for: {fname}")

    except Exception as e:
        print(f"Skipping {url} — {e}")

driver.quit()

print(f"\nSaved {len(list(Path('out').glob('*.txt')))} transcripts.")