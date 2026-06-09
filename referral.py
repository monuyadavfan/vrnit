# ═══════════════════════════════════════════
#   referral.py — V16
# ═══════════════════════════════════════════
import secrets, time
from datetime import datetime
from helpers import load_json, save_json, get_settings
from config import REFERRAL_PATH

def get_referral_days() -> int:
    return int(get_settings().get("referral_days", 3))

def get_or_create_referral(uid: int) -> str:
    refs = load_json(REFERRAL_PATH, {})
    uid_str = str(uid)
    for code, info in refs.items():
        if info.get("owner") == uid_str: return code
    code = "REF" + secrets.token_hex(3).upper()
    while code in refs: code = "REF" + secrets.token_hex(3).upper()
    refs[code] = {"owner": uid_str, "uses": 0, "referred_users": [], "created_at": datetime.now().isoformat()}
    save_json(REFERRAL_PATH, refs)
    return code

def use_referral(code: str, new_uid: int) -> tuple:
    refs = load_json(REFERRAL_PATH, {})
    code = code.upper().strip()
    if code not in refs: return False, None, 0
    info = refs[code]
    owner = info.get("owner")
    if owner == str(new_uid): return False, None, 0
    if str(new_uid) in info.get("referred_users", []): return False, None, 0
    days = get_referral_days()
    refs[code]["uses"] = info.get("uses", 0) + 1
    refs[code]["referred_users"].append(str(new_uid))
    refs[code].setdefault("history", []).append({
        "uid": str(new_uid), "time": datetime.now().strftime("%d %b %Y"), "days": days
    })
    save_json(REFERRAL_PATH, refs)
    return True, owner, days

def get_referral_stats(uid: int) -> dict:
    refs = load_json(REFERRAL_PATH, {})
    for code, info in refs.items():
        if info.get("owner") == str(uid):
            return {"code": code, "uses": info.get("uses",0), "history": info.get("history",[])}
    return {"code": None, "uses": 0, "history": []}

def get_all_referrals() -> dict:
    return load_json(REFERRAL_PATH, {})
