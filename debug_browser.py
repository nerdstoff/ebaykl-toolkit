import asyncio
from playwright.async_api import async_playwright

async def main():
    url = "https://www.kleinanzeigen.de/s-anzeige/lenovo-thinkpad-t580-intel-i7-8550u-15-6-fhd-ips-32gb-ram-512gb-ssd/2810893468-278-9424"

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
