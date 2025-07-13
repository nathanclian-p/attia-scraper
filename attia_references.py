from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json
import os
import time

BASE_URL = "https://peterattiamd.com/topics/"
BASE_DOMAIN = "https://peterattiamd.com"

OUTDIR = "attia_articles"
TEXT_OUTDIR = os.path.join(OUTDIR, "article_texts")
os.makedirs(TEXT_OUTDIR, exist_ok=True)

def collect_category_links(driver):
    driver.get(BASE_URL)
    time.sleep(3)

    links = driver.find_elements(By.CSS_SELECTOR, "a.wp-block-button__link")
    category_urls = []
    for link in links:
        href = link.get_attribute("href")
        if href:
            full_url = href if href.startswith("http") else BASE_DOMAIN + href
            category_urls.append(full_url)

    print(f"Found {len(category_urls)} topic category pages.")
    return category_urls

def collect_article_links(driver, category_url):
    driver.get(category_url)
    time.sleep(3)

    article_links = []
    entries = driver.find_elements(By.CSS_SELECTOR, "h2.post-summary__title a")
    for entry in entries:
        href = entry.get_attribute("href")
        title = entry.text.strip()
        if href and title:
            article_links.append({
                "title": title,
                "url": href
            })

    print(f"Category {category_url} → found {len(article_links)} articles.")
    return article_links

def scrape_article_content(driver, article):
    driver.get(article["url"])
    time.sleep(5)

    page_html = driver.page_source
    soup = BeautifulSoup(page_html, "html.parser")

    content_div = soup.select_one("div.entry-content")
    if content_div:
        all_text = content_div.get_text(separator="\n", strip=True)
    else:
        all_text = ""

    safe_title = "".join(c if c.isalnum() else "_" for c in article["title"])[:80]
    file_path = os.path.join(TEXT_OUTDIR, f"{safe_title}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(all_text)

    print(f"✅ Saved article: {article['title']}")
    return file_path

def main():
    options = Options()
    # Remove the comment below to run headless
    # options.add_argument("--headless=new")

    driver = webdriver.Chrome(options=options)

    all_articles = []

    category_urls = collect_category_links(driver)

    for category_url in category_urls:
        articles = collect_article_links(driver, category_url)

        for article in articles:
            text_file = scrape_article_content(driver, article)
            all_articles.append({
                "article_title": article["title"],
                "article_url": article["url"],
                "text_file": text_file
            })

    driver.quit()

    output_path = os.path.join(OUTDIR, "attia_articles_data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, indent=2)

    print(f"Scraping complete. Data saved to {output_path}")

if __name__ == "__main__":
    main()