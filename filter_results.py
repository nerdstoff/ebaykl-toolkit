import json
import os
from datetime import datetime
from pathlib import Path

# Load settings
with open("settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

OUTPUT_JSON = Path(settings["output_json"])
CLEANED_JSON = Path(settings["output_cleaned_json"])
BACKUP_FOLDER = Path("backup")
EXCLUDE_TITLES = [k.lower() for k in settings.get("exclude_titles", [])]
NEGATIVE_KEYWORDS = [k.lower() for k in settings.get("negative_keywords", [])]

# Ensure backup folder exists
BACKUP_FOLDER.mkdir(exist_ok=True)

# Load existing cleaned results if any
existing_urls = set()
if CLEANED_JSON.exists():
    with open(CLEANED_JSON, "r", encoding="utf-8") as f:
        cleaned_results = json.load(f)
        existing_urls = {entry.get("url") for entry in cleaned_results}
else:
    cleaned_results = []

# Load current raw results
if not OUTPUT_JSON.exists():
    print(f"❌ Datei nicht gefunden: {OUTPUT_JSON}")
    exit(1)

with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
    all_results = json.load(f)

# Filtering
new_cleaned = []
excluded_links = []

for entry in all_results:
    url = entry.get("url", "")
    title = entry.get("title", "").lower()
    desc = entry.get("description", "").lower()

    if url in existing_urls:
        continue  # already in cleaned

    if any(bad in title for bad in EXCLUDE_TITLES):
        excluded_links.append(url)
        continue

    if any(neg in desc for neg in NEGATIVE_KEYWORDS):
        excluded_links.append(url)
        continue

    new_cleaned.append(entry)
    existing_urls.add(url)

# Save merged cleaned results
with open(CLEANED_JSON, "w", encoding="utf-8") as f:
    json.dump(cleaned_results + new_cleaned, f, indent=2, ensure_ascii=False)

print(f"✅ Bereinigt und gespeichert: {len(cleaned_results) + len(new_cleaned)} → {CLEANED_JSON.name}")

# Save excluded links separately
if excluded_links:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_FOLDER / f"excluded_links_{timestamp}.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(excluded_links, f, indent=2, ensure_ascii=False)
    print(f"⚠️ {len(excluded_links)} ausgeschlossene Links gespeichert in: {backup_file.name}")
