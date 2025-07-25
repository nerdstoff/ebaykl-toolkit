import asyncio
import json
import os
import random
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Load settings
with open("settings.json", "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

CACHE_FOLDER = Path(SETTINGS["cache_folder"])
OUTPUT_FILE = Path(SETTINGS["output_json"])
CLEANED_FILE = Path(SETTINGS["output_cleaned_json"])
BACKUP_FOLDER = Path("backup")
USER_AGENTS = SETTINGS["user_agents"]
HEADLESS = SETTINGS.get("headless", True)
PARALLEL_TABS = SETTINGS.get("parallel_tabs", 4)
BAN_KEYWORDS = [x.lower() for x in SETTINGS.get("exclude_titles", [])]
NEGATIVE_KEYWORDS = [x.lower() for x in SETTINGS.get("negative_keywords", [])]

SAVE_INTERVAL = 10  # save after this many cache files
BACKUP_FOLDER.mkdir(exist_ok=True)

def load_existing_links():
    all_links = set()
    for file_path in [OUTPUT_FILE, CLEANED_FILE]:
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    for item in json.load(f):
                        all_links.add(item.get("url"))
                except Exception:
                    continue
    return all_links

def save_backup():
    if OUTPUT_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_FOLDER / f"results_backup_{timestamp}.json"
        OUTPUT_FILE.replace(backup_path)

def save_results(results):
    OUTPUT_FILE.parent.mkdir(exist_ok=True, parents=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

def contains_keywords(text, keywords):
    return any(keyword in text.lower() for keyword in keywords)

async def extract_info_from_url(page, url):
    try:
        await page.goto(url, timeout=30000)

        # Handle cookie banner
        try:
            await page.click("button[data-testid='gdpr-banner-decline-button']", timeout=3000)
        except PlaywrightTimeoutError:
            pass

        # Handle login overlay
        try:
            await page.click("a.j-overlay-close.overlay-close", timeout=3000)
        except PlaywrightTimeoutError:
            pass

        await page.wait_for_selector("h1#viewad-title", timeout=8000)

        title = await page.inner_text("h1#viewad-title")
        if contains_keywords(title, BAN_KEYWORDS):
            return None

        price = await page.inner_text("h2#viewad-price") if await page.query_selector("h2#viewad-price") else "N/A"
        location = await page.inner_text("span#viewad-locality") if await page.query_selector("span#viewad-locality") else "N/A"
        date = await page.inner_text("div > i.icon-calendar-gray-simple + span") if await page.query_selector("div > i.icon-calendar-gray-simple + span") else "N/A"
        shipping = await page.inner_text("span.boxedarticle--details--shipping") if await page.query_selector("span.boxedarticle--details--shipping") else "N/A"
        description = await page.inner_text("p#viewad-description-text") if await page.query_selector("p#viewad-description-text") else "N/A"

        if contains_keywords(description, NEGATIVE_KEYWORDS):
            return None

        return {
            "url": url,
            "title": title.strip(),
            "price": price.strip(),
            "shipping": shipping.strip(),
            "location": location.strip(),
            "date": date.strip(),
            "description": description.strip()
        }

    except Exception as e:
        print(f"[!] Fehler bei {url}: {e}")
        return None

async def process_urls_batch(context, urls, existing_links):
    results = []
    semaphore = asyncio.Semaphore(PARALLEL_TABS)

    async def task_wrapper(url):
        if url in existing_links:
            return None
        async with semaphore:
            page = await context.new_page()
            data = await extract_info_from_url(page, url)
            await page.close()
            return data

    tasks = [task_wrapper(url) for url in urls]
    enriched_data = await asyncio.gather(*tasks)
    return [r for r in enriched_data if r]

async def main():
    all_results = []
    existing_links = load_existing_links()

    save_backup()

    processed_files = 0

    async with async_playwright() as p:
        browser_type = p.chromium
        browser = await browser_type.launch(headless=HEADLESS)

        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 800}
        )

        for file in sorted(CACHE_FOLDER.glob("urls_*.json")):
            with open(file, "r", encoding="utf-8") as f:
                try:
                    urls = json.load(f)
                except Exception as e:
                    print(f"[!] Fehler beim Laden {file}: {e}")
                    continue

            print(f"[+] Verarbeite: {file.name} mit {len(urls)} URLs")

            enriched = await process_urls_batch(context, urls, existing_links)
            all_results.extend(enriched)
            existing_links.update([r["url"] for r in enriched])

            processed_files += 1
            if processed_files % SAVE_INTERVAL == 0:
                print(f"[✓] Zwischenspeichern nach {processed_files} Dateien...")
                save_results(all_results)

        # Final save
        save_results(all_results)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
