# ═══════════════════════════════════════════
#   config.py — V16 Central Config
# ═══════════════════════════════════════════

# ── Bot Credentials ──
API_ID    = 27966142
API_HASH  = "d07cbcc5c89ef6e012c365ab8f1c1764"
BOT_TOKEN = "7819621467:AAE9XCZb2A7_F6ph-t_-zFUhj3sDDVgZmrQ"
ADMIN_ID  = 5409110353

# ── Channel for file storage ──
FILE_CHANNEL_ID = "@cloudxgb"   # Apna channel ID daalo

# ── URLs ──
SITE_PREFIX = "https://www.vrnit.online/page-get"
BASE_URL    = "https://www.filmyzilla0.com/server/{}/hello.html"

# ── Shorteners ──
GPLINK_API_URL = "https://shrinkme.io/api"
GPLINK_API_KEY = "e340a42a3cccab8624933046eb824f51d08937b9"
TINYURL_API    = "https://tinyurl.com/api-create.php"

# ── UPI ──
UPI_ID   = "8318158045@upi"
UPI_NAME = "Filmyzilla Bot"

# ── Web Panel ──
WEB_PANEL_PORT     = 8000
WEB_PANEL_PASSWORD = "admin123"

# ── Plans ──
PLANS = {
    "1": {"days": 30,  "price": 29,  "label": "⚡ Weekly  — ₹29  / 7 Days"},
    "2": {"days": 90, "price": 99,  "label": "🔥 Monthly — ₹99  / 30 Days"},
    "3": {"days": 365, "price": 249, "label": "💎 Premium — ₹249 / 90 Days"},
}

# ── Earning System ──
DOWNLOADS_PER_DOLLAR = 2000   # 2000 downloads = $1
MIN_WITHDRAWAL       = 5      # Minimum $5 withdrawal

# ── File Paths ──
JSON_PATH         = "links.json"
USERS_PATH        = "users.json"
BANNED_PATH       = "banned.json"
SETTINGS_PATH     = "settings.json"
ACTIVATIONS_PATH  = "activations.json"
TOKENS_PATH       = "tokens.json"
STARS_PATH        = "stars.json"
KEYS_PATH         = "keys.json"
SEARCH_HIST_PATH  = "search_history.json"
PAYMENTS_PATH     = "payments.json"
BAD_WORDS_PATH    = "bad_words.json"
BAD_WORD_LOG_PATH = "bad_word_log.json"
ADMINS_PATH       = "acting_admins.json"
REFERRAL_PATH     = "referrals.json"
ADS_PATH          = "advertisements.json"
FILES_DB_PATH     = "files_db.json"        # Creator files
CREATORS_PATH     = "creators.json"        # Creator info
WARNINGS_PATH     = "warnings.json"        # User warnings
NOTES_PATH        = "notes.json"           # Admin notes
MUTED_PATH        = "muted.json"           # Muted users
CAPTCHA_PATH      = "captcha.json"         # Captcha pending
REPORTS_PATH      = "reports.json"         # User reports
FETCH_STATE_PATH  = "fetch_state.json"     # Fetch resume state

# ── Defaults ──
DEFAULT_SETTINGS = {
    "short":              True,
    "act_short":          True,
    "creator_short":      True,
    "force_join":         False,
    "maintenance":        False,
    "auto_delete":        True,
    "delete_timer":       180,
    "force_channel":      "@YourChannelHere",
    "promote_channel":    "@YourPromoteChannel",
    "welcome_msg":        "👋 Welcome! Use /help to get started.",
    "referral_days":      3,
    "new_user_alert":     True,
    "movie_token":        True,    # Movie link token toggle
    "max_warnings":       3,       # Auto ban after X warnings
    "captcha_enabled":    False,
    "upi_id":             "yourname@upi",
    "original_link":      False,   # Toggle original vs short link
}

# ── Limits ──
TOKEN_TTL_HOURS     = 24
ACTIVATION_HOURS    = 24
PAGE_SIZE           = 10
TG_CHUNK            = 4000
SEARCH_COOLDOWN     = 5
ACTIVATION_COOLDOWN = 30

# ── Level Labels ──
LEVEL_LABELS = {
    1:  "⭐ Level 1 — Search + Fetch",
    2:  "⭐⭐ Level 2 — + Ban/Genkey",
    3:  "⭐⭐⭐ Level 3 — + Broadcast",
    4:  "🎬 Creator — File Upload",
    99: "👑 Main Admin",
}

LEVEL_PERMISSIONS = {
    1: ["search", "fetch"],
    2: ["search", "fetch", "ban", "unban", "genkey"],
    3: ["search", "fetch", "ban", "unban", "genkey", "broadcast"],
    4: ["search", "upload"],
    99: ["all"],
}
