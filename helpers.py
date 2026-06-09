# ═══════════════════════════════════════════
#   helpers.py — V16 Common Functions
# ═══════════════════════════════════════════

import json, os, time, random, string, secrets, requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import *

# ─────────────── JSON ───────────────
def ensure_file(path, default):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)

def load_json(path, default):
    ensure_file(path, default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[save_json error] {path}: {e}")

# ─────────────── SETTINGS ───────────────
def get_settings() -> dict:
    s = load_json(SETTINGS_PATH, {})
    merged = DEFAULT_SETTINGS.copy()
    merged.update(s)
    return merged

def update_setting(key: str, value):
    s = load_json(SETTINGS_PATH, {})
    s[key] = value
    save_json(SETTINGS_PATH, s)

# ─────────────── SHORTENER ───────────────
def shorten_with_gplink(url: str, api_key: str = None):
    try:
        key = api_key or GPLINK_API_KEY
        r = requests.get(GPLINK_API_URL, params={"api": key, "url": url}, timeout=10)
        r.raise_for_status()
        d = r.json()
        return d.get("shortenedUrl") or d.get("shortUrl") or d.get("short")
    except:
        return None

def shorten_with_tinyurl(url: str):
    try:
        r = requests.get(TINYURL_API, params={"url": url}, timeout=10)
        r.raise_for_status()
        return r.text.strip()
    except:
        return None

def get_short_link(url: str, creator_api: str = None) -> str:
    s = get_settings()
    if s.get("original_link"): return url
    if not s.get("short"): return url
    if creator_api:
        return shorten_with_gplink(url, creator_api) or url
    return shorten_with_gplink(url) or shorten_with_tinyurl(url) or url

def get_short_link_activation(url: str) -> str:
    s = get_settings()
    if not s.get("act_short"): return url
    return shorten_with_gplink(url) or shorten_with_tinyurl(url) or url

def get_creator_short_link(url: str, creator_api: str = None) -> str:
    s = get_settings()
    if not s.get("creator_short"): return url
    if creator_api:
        return shorten_with_gplink(url, creator_api) or url
    return shorten_with_gplink(url) or shorten_with_tinyurl(url) or url

# ─────────────── TOKEN ───────────────
def make_token(uid: int) -> str:
    token = secrets.token_urlsafe(8)
    tokens = load_json(TOKENS_PATH, {})
    tokens[token] = {
        "uid": int(uid),
        "created_at": int(time.time()),
        "expires_at_ts": int(time.time()) + TOKEN_TTL_HOURS * 3600
    }
    save_json(TOKENS_PATH, tokens)
    return token

def verify_token(token: str, uid: int) -> bool:
    tokens = load_json(TOKENS_PATH, {})
    rec = tokens.get(token)
    if not rec or int(rec.get("uid")) != int(uid): return False
    if int(rec.get("expires_at_ts", 0)) < int(time.time()):
        tokens.pop(token, None); save_json(TOKENS_PATH, tokens); return False
    tokens.pop(token, None); save_json(TOKENS_PATH, tokens)
    return True

# ─────────────── KEY ───────────────
def generate_key() -> str:
    parts = ["".join(random.choices(string.ascii_uppercase + string.digits, k=4)) for _ in range(3)]
    return "FILM-" + "-".join(parts)

def create_keys(count: int, days: int) -> list:
    keys_db = load_json(KEYS_PATH, {})
    new_keys = []
    for _ in range(count):
        k = generate_key()
        while k in keys_db: k = generate_key()
        keys_db[k] = {"days": days, "used": False, "created_at": datetime.now().isoformat()}
        new_keys.append(k)
    save_json(KEYS_PATH, keys_db)
    return new_keys

def use_key(key: str, uid: int) -> tuple:
    keys_db = load_json(KEYS_PATH, {})
    key = key.upper().strip()
    if key not in keys_db: return False, "❌ Invalid key!"
    info = keys_db[key]
    if info.get("used"): return False, "❌ Key already used!"
    days = info.get("days", 30)
    activate_user(uid, days * 24, method="key", key=key)
    keys_db[key].update({"used": True, "used_by": str(uid), "used_at": datetime.now().isoformat()})
    save_json(KEYS_PATH, keys_db)
    return True, f"✅ Activated for {days} days!"

# ─────────────── ACTIVATION ───────────────
def activate_user(uid: int, hours: int = ACTIVATION_HOURS, method: str = "token", key: str = ""):
    activ = load_json(ACTIVATIONS_PATH, {})
    activ[str(uid)] = {
        "activated_at": int(time.time()),
        "expires_at_ts": int(time.time()) + hours * 3600,
        "hours": hours, "method": method, "key": key
    }
    save_json(ACTIVATIONS_PATH, activ)

def deactivate_user(uid: int):
    activ = load_json(ACTIVATIONS_PATH, {})
    activ.pop(str(uid), None)
    save_json(ACTIVATIONS_PATH, activ)

def extend_user(uid: int, extra_days: int) -> str:
    activ = load_json(ACTIVATIONS_PATH, {})
    uid_str = str(uid)
    now = int(time.time())
    if uid_str in activ:
        cur = int(activ[uid_str].get("expires_at_ts", now))
        new_exp = max(cur, now) + extra_days * 86400
        activ[uid_str]["expires_at_ts"] = new_exp
        save_json(ACTIVATIONS_PATH, activ)
        return datetime.fromtimestamp(new_exp).strftime("%d %b %Y")
    else:
        activate_user(uid, extra_days * 24, method="admin")
        return (datetime.now() + timedelta(days=extra_days)).strftime("%d %b %Y")

def is_user_active(uid: int) -> bool:
    if int(uid) == ADMIN_ID: return True
    activ = load_json(ACTIVATIONS_PATH, {})
    rec = activ.get(str(uid))
    if not rec: return False
    if int(rec.get("expires_at_ts", 0)) > int(time.time()): return True
    activ.pop(str(uid), None); save_json(ACTIVATIONS_PATH, activ)
    return False

def get_activation_info(uid: int) -> str:
    if int(uid) == ADMIN_ID: return "♾️ Lifetime (Admin)"
    activ = load_json(ACTIVATIONS_PATH, {})
    rec = activ.get(str(uid))
    if not rec: return "❌ Not activated"
    exp = datetime.fromtimestamp(int(rec["expires_at_ts"]))
    remaining = exp - datetime.now()
    d, h = remaining.days, remaining.seconds // 3600
    method = "🔑 Key" if rec.get("method") == "key" else "🔗 Link"
    return f"✅ Active [{method}] — {d}d {h}h left\n📅 Expires: {exp.strftime('%d %b %Y, %I:%M %p')}"

# ─────────────── STAR ───────────────
def star_movie(uid: str, item: dict) -> bool:
    stars = load_json(STARS_PATH, {})
    if uid not in stars: stars[uid] = []
    if not any(s.get("server") == item.get("server") for s in stars[uid]):
        stars[uid].append({"server": item["server"], "title": item["title"], "size": item.get("size","?")})
        save_json(STARS_PATH, stars)
        return True
    return False

def get_stars(uid: str) -> list:
    return load_json(STARS_PATH, {}).get(uid, [])

# ─────────────── DOWNLOAD COUNTER ───────────────
def increment_download(server_id: int):
    data = load_json(JSON_PATH, [])
    for item in data:
        if int(item.get("server", -1)) == server_id:
            item["downloads"] = item.get("downloads", 0) + 1
            save_json(JSON_PATH, data)
            return item.get("downloads", 1)
    return 0

def get_user_download_count(uid: str) -> int:
    history = load_json(SEARCH_HIST_PATH, {})
    return len(history.get(uid, []))

# ─────────────── SEARCH HISTORY ───────────────
def save_search(uid: str, query: str):
    history = load_json(SEARCH_HIST_PATH, {})
    if uid not in history: history[uid] = []
    history[uid].insert(0, {"query": query, "time": datetime.now().strftime("%d %b %Y %I:%M %p")})
    history[uid] = history[uid][:50]
    save_json(SEARCH_HIST_PATH, history)

def get_search_history(uid: str) -> list:
    return load_json(SEARCH_HIST_PATH, {}).get(uid, [])

# ─────────────── SCRAPER ───────────────
def extract_path(href: str) -> str:
    if not href: return ""
    if href.startswith("http"): return "/" + "/".join(href.split("/")[3:])
    return href if href.startswith("/") else "/" + href

async def scrape_server(i: int):
    try:
        r = requests.get(
            BASE_URL.format(i), timeout=15,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
                "Connection": "keep-alive",
            }
        )
        if r.status_code != 200:
            print(f"[Fetch {i}] HTTP {r.status_code}")
            return None
        soup  = BeautifulSoup(r.text, "html.parser")
        title = soup.find("div", class_="head")
        size  = soup.find("span", class_="bld")
        links = [extract_path(a.get("href")) for a in soup.find_all("a", class_="newdl") if a.get("href")]
        if not links:
            print(f"[Fetch {i}] No links found")
            return None
        return {
            "server":     i,
            "title":      title.text.strip() if title else f"No Title {i}",
            "size":       size.text.strip() if size else "Unknown",
            "links":      links,
            "downloads":  0,
            "fetched_at": datetime.now().isoformat()
        }
    except requests.exceptions.Timeout:
        print(f"[Fetch {i}] Timeout"); return None
    except Exception as e:
        print(f"[Fetch {i}] Error: {type(e).__name__}: {e}"); return None

def chunk_text(text: str, size: int = TG_CHUNK):
    for i in range(0, len(text), size): yield text[i:i+size]

# ─────────────── QR CODE ───────────────
def generate_upi_qr(amount: float, upi_id: str, name: str) -> str:
    """Returns QR code image URL"""
    upi_string = f"upi://pay?pa={upi_id}&pn={name}&am={amount}&cu=INR"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(upi_string)}"
    return qr_url

# ─────────────── INIT FILES ───────────────
def init_files():
    for p, d in [
        (JSON_PATH, []), (USERS_PATH, []), (BANNED_PATH, []),
        (SETTINGS_PATH, {}), (ACTIVATIONS_PATH, {}), (TOKENS_PATH, {}),
        (STARS_PATH, {}), (KEYS_PATH, {}), (SEARCH_HIST_PATH, {}),
        (PAYMENTS_PATH, {}), (BAD_WORDS_PATH, []), (BAD_WORD_LOG_PATH, []),
        (ADMINS_PATH, {}), (REFERRAL_PATH, {}), (ADS_PATH, []),
        (FILES_DB_PATH, {}), (CREATORS_PATH, {}), (WARNINGS_PATH, {}),
        (NOTES_PATH, {}), (MUTED_PATH, {}), (CAPTCHA_PATH, {}),
        (REPORTS_PATH, []), (FETCH_STATE_PATH, {}),
    ]:
        ensure_file(p, d)
