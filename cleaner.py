import os
import shutil
from config import TARGET_DIRS, WHITELIST
from datetime import datetime

LOG_FILE = "logs/cleanup.log"

def log_action(action, path):
    os.makedirs("logs", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {action}: {path}\n")

def is_whitelisted(file_path):
    return any(name in file_path for name in WHITELIST)

def get_temp_files_sorted():
    files = []
    for base_dir in TARGET_DIRS:
        for root, dirs, file_list in os.walk(base_dir):
            for name in file_list:
                try:
                    full_path = os.path.join(root, name)
                    if is_whitelisted(full_path):
                        continue
                    size = os.path.getsize(full_path)
                    files.append({
                        'path': full_path,
                        'size': size
                    })
                except Exception as e:
                    continue
    files.sort(key=lambda x: x['size'], reverse=True)
    return files

def delete_files(file_paths):
    total_freed = 0
    for file in file_paths:
        try:
            size = os.path.getsize(file)
            os.remove(file)
            total_freed += size
            log_action("Deleted", file)
        except Exception as e:
            log_action("Failed", f"{file} - {str(e)}")
    return total_freed
