import json
import os

WHITELIST_FILE = "whitelist.json"

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def format_bytes(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"
import json
import os
import datetime

SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {
            "auto_clean_enabled": False,
            "auto_clean_interval_hours": 24,
            "last_clean_time": None
        }
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def should_auto_clean(settings):
    if not settings.get("auto_clean_enabled", False):
        return False
    last = settings.get("last_clean_time")
    if not last:
        return True
    try:
        last_time = datetime.datetime.fromisoformat(last)
        interval = datetime.timedelta(hours=settings.get("auto_clean_interval_hours", 24))
        return datetime.datetime.now() - last_time >= interval
    except Exception:
        return True
