import asyncio
import json
import os
import random
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Load settings
with open("settings.json", "r", encoding="utf-8") as f:
    SETTINGS = json.load(f)

SEARCH_QUERY = SETTINGS["search_query"]
CATEGORY_CODE = SETTINGS["category_code"]
PRICE_MIN = SETTINGS["price_min"]
PRICE_MAX = SETTINGS["price_max"]
USE_PRICE_STEPPING = SETTINGS["use_price_stepping"]
PAGES = SETTINGS["pages"]
PAGES_PER_STEP = SETTINGS.get("pages_per_price_step", 2)
OUTPUT_JSON = SETTINGS["output_json"]
CACHE_FOLDER = SETTINGS["cache_folder"]
HEADLESS = SETTINGS.get("headless", True)
FILTER_KEYWORDS = [k.lower() for k in SETTINGS["filter_keywords"]]
NEGATIVE_KEYWORDS = [k.lower() for k in SETTINGS.get("negative_keywords", [])]
BAN_KEYWORDS = [k.lower() for k in SETTINGS["exclude_titles"]]
USER_AGENTS = SETTINGS["user_agents"]
ENABLE_PARALLEL = SETTINGS.get("enable_parallel", False)
PARALLEL_TABS = SETTINGS.get("parallel_tabs", 4)

# Create folders
os.makedirs(CACHE_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

def build_url(price: int, page: int) -> str:
    return (
        f"https://www.kleinanzeigen.de/s-{SEARCH_QUERY}/"
        f"sortierung:preis/preis:{price}:/seite:{page}/{CATEGORY_CODE}"
    )

def get_cache_path(price: int, page: int) -> str:
    return f"{CACHE_FOLDER}/urls_{price}_page_{page}.json"

async def accept_cookies(page):
    try:
        await page.click("button[data-testid='gdpr-banner-decline-button']", timeout=3000)
    except:
        try:
            await page.click("button[data-testid='uc-accept-all-button']", timeout=3000)
        except:
            pass

async def dismiss_login_overlay(page):
    try:
        await page.wait_for_selector("a.j-overlay-close", timeout=3000)
        await page.click("a.j-overlay-close")
        print("🔐 Dismissed login overlay.")
    except:
        pass

async def extract_urls_from_page(context, price: int, page_num: int) -> list:
    cache_path = get_cache_path(price, page_num)
    if Path(cache_path).exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)

    page = await context.new_page()
    url = build_url(price, page_num)
    try:
        await page.goto(url, timeout=60000)
        await accept_cookies(page)
        await dismiss_login_overlay(page)
        await page.wait_for_selector("a.ellipsis", timeout=10000)
        urls = await page.eval_on_selector_all(
            "a.ellipsis",
            "els => els.map(el => el.href).filter(h => h.includes('/s-anzeige/'))"
        )
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(urls, f, indent=2, ensure_ascii=False)
        return urls
    except Exception as e:
        print(f"❌ Failed page {page_num} at price {price}: {e}")
        return []
    finally:
        await page.close()

async def parse_listing(context, url: str, semaphore) -> dict:
    async with semaphore:
        page = await context.new_page()
        try:
            await page.goto(url, timeout=60000)
            await accept_cookies(page)
            await dismiss_login_overlay(page)

            title = await page.title()
            if any(bad in title.lower() for bad in BAN_KEYWORDS):
                return None

            desc = await page.locator("p#viewad-description-text").inner_text(timeout=5000)
            if any(term in desc.lower() for term in NEGATIVE_KEYWORDS):
                return None

            matches = [cpu for cpu in FILTER_KEYWORDS if cpu in desc.lower()]
            if matches:
                return {
                    "url": url,
                    "title": title.strip(),
                    "matches": matches,
                    "snippet": desc.strip()[:300]
                }
        except Exception as e:
            print(f"⚠️ Error parsing {url}: {e}")
        finally:
            await page.close()
    return None

async def main():
    async with async_playwright() as p:
        browser, context = await p.chromium.launch(headless=HEADLESS), None
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1280, "height": 900}
        )

        all_urls = set()

        if USE_PRICE_STEPPING:
            for price in range(PRICE_MIN, PRICE_MAX + 1):
                for page_num in range(1, PAGES_PER_STEP + 1):
                    print(f"🔍 Crawling preis:{price} / Seite:{page_num}")
                    urls = await extract_urls_from_page(context, price, page_num)
                    all_urls.update(urls)
        else:
            for page_num in range(1, PAGES + 1):
                print(f"🔍 Crawling Seite:{page_num}")
                urls = await extract_urls_from_page(context, PRICE_MIN, page_num)
                all_urls.update(urls)

        print(f"🔗 Found {len(all_urls)} unique URLs")

        semaphore = asyncio.Semaphore(PARALLEL_TABS) if ENABLE_PARALLEL else asyncio.Semaphore(1)
        tasks = [parse_listing(context, url, semaphore) for url in all_urls]
        results = await asyncio.gather(*tasks)

        filtered = [r for r in results if r]
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(filtered)} filtered listings to {OUTPUT_JSON}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())