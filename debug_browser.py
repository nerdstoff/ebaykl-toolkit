import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://www.kleinanzeigen.de/"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900}
        )
        page = await context.new_page()
        await page.goto(url)
        print("🔍 Browser opened. Inspect manually. Press CTRL+C to exit.")
        await asyncio.sleep(600)  # Keeps the browser open 10 minutes

if __name__ == "__main__":
    asyncio.run(main())
