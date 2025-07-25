# 🛠️ eBay Kleinanzeigen Scraper Toolkit

An async scraping toolkit for collecting, enriching, and filtering listings from Kleinanzeigen.de.

## Features
- 🔍 Search & scrape listings
- 📦 Enrich listing details (multi-tab support)
- 🧹 Filter duplicates and banned keywords
- 🧠 CLI launcher
- 💾 Caching, backups, and settings config
- 🧰 Playwright-powered

## Usage
1. Edit `settings.json`
2. Run `python launcher.py` like: & C:/Users/..../Desktop/ebaykl/.venv/Scripts/python.exe C:\Users\....\Desktop\ebaykl\launcher.py
3. Choose a task (scrape, enrich, filter, etc.)

## Requirements
- Python 3.10+
- Playwright

## Setup
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
playwright install
