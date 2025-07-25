import json
import os
from glob import glob

# Load settings
with open("settings.json", "r", encoding="utf-8") as f:
    settings = json.load(f)

CACHE_FOLDER = settings["cache_folder"]
OUTPUT_FILE = settings["output_json"]

# Make sure output folder exists
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

all_urls = set()
results = []

# Collect all cached URL files
cache_files = sorted(glob(os.path.join(CACHE_FOLDER, "urls_*.json")))

for file_path in cache_files:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            urls = json.load(f)
            for url in urls:
                if url not in all_urls:
                    results.append({"url": url})
                    all_urls.add(url)
    except Exception as e:
        print(f"⚠️ Error reading {file_path}: {e}")

# Save to results.json
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"✅ Merged {len(results)} unique URLs from {CACHE_FOLDER} into {OUTPUT_FILE}")
