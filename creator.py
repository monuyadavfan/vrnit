# ═══════════════════════════════════════════
#   creator.py — V16 Creator System
#   File Upload + Earnings + Download Tracking
# ═══════════════════════════════════════════

import secrets, time
from datetime import datetime
from helpers import load_json, save_json, get_creator_short_link
from config import *

# ═══════════════════════════════
#   CREATOR MANAGEMENT
# ═══════════════════════════════

def register_creator(uid: str, name: str):
    creators = load_json(CREATORS_PATH, {})
    if uid not in creators:
        creators[uid] = {
            "name":         name,
            "joined_at":    datetime.now().isoformat(),
            "total_dl":     0,
            "earnings":     0.0,
            "withdrawn":    0.0,
            "shortener_api": "",
            "force_channel": "",
        }
        save_json(CREATORS_PATH, creators)

def get_creator(uid: str) -> dict:
    return load_json(CREATORS_PATH, {}).get(uid)

def update_creator(uid: str, key: str, value):
    creators = load_json(CREATORS_PATH, {})
    if uid in creators:
        creators[uid][key] = value
        save_json(CREATORS_PATH, creators)

def get_creator_earnings(uid: str) -> dict:
    creator = get_creator(uid)
    if not creator: return {}
    total_dl  = creator.get("total_dl", 0)
    earned    = round(total_dl / DOWNLOADS_PER_DOLLAR, 2)
    withdrawn = creator.get("withdrawn", 0.0)
    pending   = round(earned - withdrawn, 2)
    return {
        "total_dl":  total_dl,
        "earned":    earned,
        "withdrawn": withdrawn,
        "pending":   max(0, pending),
        "can_withdraw": pending >= MIN_WITHDRAWAL
    }

def add_creator_downloads(uid: str, count: int = 1):
    creators = load_json(CREATORS_PATH, {})
    if uid in creators:
        creators[uid]["total_dl"] = creators[uid].get("total_dl", 0) + count
        total = creators[uid]["total_dl"]
        creators[uid]["earnings"] = round(total / DOWNLOADS_PER_DOLLAR, 2)
        save_json(CREATORS_PATH, creators)

def get_all_creators() -> dict:
    return load_json(CREATORS_PATH, {})

# ═══════════════════════════════
#   FILE MANAGEMENT
# ═══════════════════════════════

def add_file(creator_uid: str, file_id: str, file_name: str,
             title: str, file_type: str, size: str,
             msg_id: int, channel_id: int,
             password: str = "", expiry_days: int = 0,
             category: str = "general") -> str:
    files = load_json(FILES_DB_PATH, {})
    file_key = "F" + secrets.token_hex(4).upper()

    expiry_ts = 0
    if expiry_days > 0:
        expiry_ts = int(time.time()) + expiry_days * 86400

    files[file_key] = {
        "creator_uid":  creator_uid,
        "file_id":      file_id,
        "file_name":    file_name,
        "title":        title or file_name,
        "file_type":    file_type,
        "size":         size,
        "msg_id":       msg_id,
        "channel_id":   channel_id,
        "password":     password,
        "expiry_ts":    expiry_ts,
        "category":     category,
        "downloads":    0,
        "creator_dl":   0,
        "default_dl":   0,
        "uploaded_at":  datetime.now().isoformat(),
        "active":       True,
    }
    save_json(FILES_DB_PATH, files)
    return file_key

def get_file(file_key: str) -> dict:
    return load_json(FILES_DB_PATH, {}).get(file_key)

def search_files(query: str) -> list:
    files = load_json(FILES_DB_PATH, {})
    query = query.lower()
    result = []
    for key, info in files.items():
        if not info.get("active"): continue
        # Check expiry
        exp = info.get("expiry_ts", 0)
        if exp and int(time.time()) > exp: continue
        if query in info.get("title","").lower() or query in info.get("file_name","").lower():
            result.append({"key": key, **info})
    return result

def increment_file_download(file_key: str, is_creator_link: bool = False):
    files = load_json(FILES_DB_PATH, {})
    if file_key in files:
        files[file_key]["downloads"] = files[file_key].get("downloads", 0) + 1
        if is_creator_link:
            files[file_key]["creator_dl"] = files[file_key].get("creator_dl", 0) + 1
        else:
            files[file_key]["default_dl"] = files[file_key].get("default_dl", 0) + 1
        creator_uid = files[file_key].get("creator_uid")
        save_json(FILES_DB_PATH, files)
        if creator_uid:
            add_creator_downloads(creator_uid, 1)

def delete_file(file_key: str) -> bool:
    files = load_json(FILES_DB_PATH, {})
    if file_key in files:
        files[file_key]["active"] = False
        save_json(FILES_DB_PATH, files)
        return True
    return False

def get_creator_files(creator_uid: str) -> list:
    files = load_json(FILES_DB_PATH, {})
    return [{"key": k, **v} for k, v in files.items() if v.get("creator_uid") == creator_uid and v.get("active")]

def get_all_files() -> dict:
    return load_json(FILES_DB_PATH, {})

def build_file_link(bot_username: str, file_key: str) -> str:
    return f"https://t.me/{bot_username}?start=file_{file_key}"

def is_file_expired(file_info: dict) -> bool:
    exp = file_info.get("expiry_ts", 0)
    if not exp: return False
    return int(time.time()) > exp

def is_file_password_protected(file_info: dict) -> bool:
    return bool(file_info.get("password"))

def check_file_password(file_info: dict, entered: str) -> bool:
    return file_info.get("password", "") == entered

# ═══════════════════════════════
#   FETCH STATE (Resume)
# ═══════════════════════════════

def save_fetch_state(start: int, end: int, current: int, added: int, skipped: int, failed: int):
    save_json(FETCH_STATE_PATH, {
        "start": start, "end": end, "current": current,
        "added": added, "skipped": skipped, "failed": failed,
        "running": True, "updated_at": datetime.now().isoformat()
    })

def clear_fetch_state():
    save_json(FETCH_STATE_PATH, {"running": False})

def get_fetch_state() -> dict:
    return load_json(FETCH_STATE_PATH, {"running": False})

def is_fetch_running() -> bool:
    return load_json(FETCH_STATE_PATH, {}).get("running", False)
