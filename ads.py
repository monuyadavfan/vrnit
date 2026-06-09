# ═══════════════════════════════════════════
#   ads.py — V16 Advertisement System
# ═══════════════════════════════════════════
import secrets
from datetime import datetime
from helpers import load_json, save_json
from config import ADS_PATH

def get_active_ads() -> list:
    return [a for a in load_json(ADS_PATH, []) if a.get("active", True)]

def get_all_ads() -> list:
    return load_json(ADS_PATH, [])

def add_ad(title: str, url: str, button_text: str) -> str:
    ads = load_json(ADS_PATH, [])
    ad_id = "AD" + secrets.token_hex(3).upper()
    ads.append({
        "id": ad_id, "title": title, "url": url,
        "button_text": button_text, "clicks": 0,
        "click_log": [], "active": True,
        "created_at": datetime.now().isoformat()
    })
    save_json(ADS_PATH, ads)
    return ad_id

def remove_ad(ad_id: str) -> bool:
    ads = load_json(ADS_PATH, [])
    new = [a for a in ads if a.get("id") != ad_id]
    if len(new) == len(ads): return False
    save_json(ADS_PATH, new); return True

def toggle_ad(ad_id: str) -> bool:
    ads = load_json(ADS_PATH, [])
    for ad in ads:
        if ad.get("id") == ad_id:
            ad["active"] = not ad.get("active", True)
            save_json(ADS_PATH, ads)
            return ad["active"]
    return False

def record_click(ad_id: str, uid: str):
    ads = load_json(ADS_PATH, [])
    for ad in ads:
        if ad.get("id") == ad_id:
            ad["clicks"] = ad.get("clicks", 0) + 1
            ad.setdefault("click_log", []).append({
                "uid": uid, "time": datetime.now().strftime("%d %b %Y %I:%M %p")
            })
            ad["click_log"] = ad["click_log"][-100:]
            save_json(ADS_PATH, ads); return

def get_ad_stats() -> list:
    return [{"id": a["id"], "title": a["title"], "clicks": a.get("clicks",0), "active": a.get("active",True)}
            for a in load_json(ADS_PATH, [])]
