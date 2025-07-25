import os
import subprocess
import sys
import json
from pathlib import Path

SETTINGS_FILE = "settings.json"

TOOLS = {
    "1": ("🔍 Run Scraper (ebaykl_scraper.py)", "ebaykl_scraper.py"),
    "2": ("📦 Enrich Results (enrich_results.py)", "enrich_results.py"),
    "3": ("🧹 Filter & Cleanup (filter_results.py)", "filter_results.py"),
    "4": ("📊 Price Analysis (coming soon)", None),
    "5": ("⚙️ Show settings.json", "SHOW_SETTINGS"),
    "6": ("✏️ Edit settings.json", "EDIT_SETTINGS"),
    "0": ("❌ Exit", None)
}


def show_menu():
    print("\n🧠 eBayKleinanzeigen Toolkit Launcher")
    print("=" * 42)
    for key, (desc, _) in TOOLS.items():
        print(f"[{key}] {desc}")
    print("=" * 42)


def show_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
        print("\n📄 Current settings.json:\n")
        for k, v in settings.items():
            print(f"{k}: {v}")
    except Exception as e:
        print(f"⚠️ Could not load settings.json: {e}")


def edit_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return

    while True:
        print("\n🛠 Editable Settings:\n")
        keys = list(settings.keys())
        for i, key in enumerate(keys, start=1):
            print(f"[{i}] {key}: {settings[key]}")
        print("[0] Save and return")

        choice = input("🔢 Select a key to edit: ").strip()
        if choice == "0":
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(keys):
                key = keys[idx]
                current_value = settings[key]
                print(f"✏️ Editing '{key}' (current: {current_value})")
                new_value = input("Enter new value (or leave empty to skip): ").strip()
                if new_value != "":
                    try:
                        # Try to interpret as JSON (e.g., list, bool, number)
                        settings[key] = json.loads(new_value)
                    except json.JSONDecodeError:
                        settings[key] = new_value
            else:
                print("❌ Invalid selection.")
        except ValueError:
            print("❌ Enter a number.")

    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print("✅ Settings saved.")
    except Exception as e:
        print(f"❌ Failed to save: {e}")


def run_tool(script):
    if script is None:
        print("❌ Not implemented.")
        return
    if script == "SHOW_SETTINGS":
        show_settings()
        return
    if script == "EDIT_SETTINGS":
        edit_settings()
        return
    if not Path(script).exists():
        print(f"❌ Script not found: {script}")
        return
    print(f"\n▶️ Running {script} ...\n")
    try:
        subprocess.run([sys.executable, script])
    except Exception as e:
        print(f"❌ Error running {script}: {e}")


def main():
    while True:
        show_menu()
        choice = input("➡️  Your choice: ").strip()
        if choice == "0":
            print("👋 Goodbye!")
            break
        if choice in TOOLS:
            run_tool(TOOLS[choice][1])
        else:
            print("❌ Invalid choice. Try again.")


if __name__ == "__main__":
    main()
