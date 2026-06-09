# ═══════════════════════════════════════════
#   admin_system.py — V16
#   Admin Levels + Creator + Bad Words
# ═══════════════════════════════════════════

from helpers import load_json, save_json
from config import *
from datetime import datetime

# ═══════════════════════════════
#   ADMIN / CREATOR SYSTEM
# ═══════════════════════════════

def add_admin(uid: str, level: int) -> bool:
    admins = load_json(ADMINS_PATH, {})
    admins[str(uid)] = {"level": level, "added_at": datetime.now().isoformat()}
    save_json(ADMINS_PATH, admins)
    return True

def remove_admin(uid: str) -> bool:
    admins = load_json(ADMINS_PATH, {})
    if str(uid) in admins:
        admins.pop(str(uid)); save_json(ADMINS_PATH, admins); return True
    return False

def get_admin_level(uid: int) -> int:
    if int(uid) == int(ADMIN_ID): return 99
    admins = load_json(ADMINS_PATH, {})
    rec = admins.get(str(uid))
    if rec: return int(rec.get("level", 1))
    return 0

def has_permission(uid: int, perm: str) -> bool:
    level = get_admin_level(uid)
    if level == 99: return True
    if level == 0: return False
    perms = LEVEL_PERMISSIONS.get(level, [])
    return "all" in perms or perm in perms

def is_any_admin(uid: int) -> bool:
    return get_admin_level(uid) > 0

def is_creator(uid: int) -> bool:
    return get_admin_level(uid) == 4 or get_admin_level(uid) == 99

def get_all_admins() -> dict:
    return load_json(ADMINS_PATH, {})

# ═══════════════════════════════
#   BAD WORDS
# ═══════════════════════════════

def get_bad_words() -> list:
    return [w.lower() for w in load_json(BAD_WORDS_PATH, [])]

def add_bad_word(word: str) -> bool:
    words = load_json(BAD_WORDS_PATH, [])
    word = word.lower().strip()
    if word not in words:
        words.append(word); save_json(BAD_WORDS_PATH, words); return True
    return False

def remove_bad_word(word: str) -> bool:
    words = load_json(BAD_WORDS_PATH, [])
    word = word.lower().strip()
    if word in words:
        words.remove(word); save_json(BAD_WORDS_PATH, words); return True
    return False

def contains_bad_word(text: str) -> str:
    text_lower = text.lower()
    for word in get_bad_words():
        if word in text_lower: return word
    return ""

def log_bad_word(uid: str, word: str, message: str):
    logs = load_json(BAD_WORD_LOG_PATH, [])
    logs.append({"uid": uid, "word_used": word, "message": message[:100], "time": datetime.now().strftime("%d %b %Y %I:%M %p")})
    save_json(BAD_WORD_LOG_PATH, logs)

def get_bad_word_logs(limit: int = 20) -> list:
    return load_json(BAD_WORD_LOG_PATH, [])[-limit:][::-1]

# ═══════════════════════════════
#   WARNINGS SYSTEM
# ═══════════════════════════════

def add_warning(uid: str, reason: str) -> int:
    warnings = load_json(WARNINGS_PATH, {})
    if uid not in warnings: warnings[uid] = []
    warnings[uid].append({"reason": reason, "time": datetime.now().strftime("%d %b %Y %I:%M %p")})
    save_json(WARNINGS_PATH, warnings)
    return len(warnings[uid])

def get_warnings(uid: str) -> list:
    return load_json(WARNINGS_PATH, {}).get(uid, [])

def clear_warnings(uid: str):
    warnings = load_json(WARNINGS_PATH, {})
    warnings.pop(uid, None)
    save_json(WARNINGS_PATH, warnings)

# ═══════════════════════════════
#   MUTE SYSTEM
# ═══════════════════════════════

def mute_user(uid: str, minutes: int = 60):
    muted = load_json(MUTED_PATH, {})
    import time
    muted[uid] = {"until": int(time.time()) + minutes * 60, "minutes": minutes}
    save_json(MUTED_PATH, muted)

def unmute_user(uid: str):
    muted = load_json(MUTED_PATH, {})
    muted.pop(uid, None)
    save_json(MUTED_PATH, muted)

def is_muted(uid: str) -> bool:
    import time
    muted = load_json(MUTED_PATH, {})
    rec = muted.get(uid)
    if not rec: return False
    if int(rec.get("until", 0)) > int(time.time()): return True
    muted.pop(uid, None); save_json(MUTED_PATH, muted)
    return False

# ═══════════════════════════════
#   NOTES SYSTEM
# ═══════════════════════════════

def save_note(key: str, value: str, uid: str):
    notes = load_json(NOTES_PATH, {})
    notes[key.lower()] = {"text": value, "by": uid, "time": datetime.now().strftime("%d %b %Y")}
    save_json(NOTES_PATH, notes)

def get_note(key: str) -> dict:
    return load_json(NOTES_PATH, {}).get(key.lower())

def delete_note(key: str) -> bool:
    notes = load_json(NOTES_PATH, {})
    if key.lower() in notes:
        notes.pop(key.lower()); save_json(NOTES_PATH, notes); return True
    return False

def get_all_notes() -> dict:
    return load_json(NOTES_PATH, {})

# ═══════════════════════════════
#   REPORTS SYSTEM
# ═══════════════════════════════

def add_report(reporter_uid: str, reported_uid: str, reason: str, msg_text: str = ""):
    reports = load_json(REPORTS_PATH, [])
    reports.append({
        "reporter": reporter_uid,
        "reported": reported_uid,
        "reason":   reason,
        "message":  msg_text[:200],
        "time":     datetime.now().strftime("%d %b %Y %I:%M %p"),
        "status":   "pending"
    })
    save_json(REPORTS_PATH, reports)

def get_reports(status: str = "pending") -> list:
    reports = load_json(REPORTS_PATH, [])
    return [r for r in reports if r.get("status") == status]
