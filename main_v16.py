"""
Filmyzilla Bot — V16
All 49 features included
"""

import asyncio, time, logging, threading, random
from datetime import datetime, timedelta
from difflib import get_close_matches

from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                             Message, CallbackQuery)
from pyrogram.errors import FloodWait

from config import *
from helpers import *
from admin_system import *
from creator import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ─────────────── RATE LIMITERS ───────────────
_last_search:     dict = {}
_last_act_prompt: dict = {}
_spam_count:      dict = {}
_fetch_stop_flag: bool = False
_pending_file_password: dict = {}  # uid → file_key

def is_rate_limited(uid: int) -> bool:
    now = time.time()
    if now - _last_search.get(uid, 0) < SEARCH_COOLDOWN: return True
    _last_search[uid] = now; return False

def is_prompt_cooldown(uid: int) -> bool:
    now = time.time()
    if now - _last_act_prompt.get(uid, 0) < ACTIVATION_COOLDOWN: return True
    _last_act_prompt[uid] = now; return False

def check_spam(uid: int) -> bool:
    now = time.time()
    times = [t for t in _spam_count.get(uid, []) if now - t < 3]
    times.append(now); _spam_count[uid] = times
    return len(times) >= 5

# ─────────────── BOT ───────────────
app = Client("filmyzilla_bot_v16", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def safe_reply(m: Message, text: str, **kwargs):
    try: return await m.reply_text(text, **kwargs)
    except FloodWait as e: await asyncio.sleep(e.value); return await m.reply_text(text, **kwargs)
    except Exception as e: logger.exception("safe_reply: %s", e)

# ─────────────── AUTO DELETE ───────────────
async def schedule_delete(*msgs):
    s = get_settings()
    if not s.get("auto_delete"): return
    mins = int(s.get("delete_timer", 180))
    await asyncio.sleep(mins * 60)
    for msg in msgs:
        if msg:
            try: await msg.delete()
            except: pass

# ─────────────── FORCE JOIN ───────────────
async def check_force_join(uid: int) -> bool:
    s = get_settings()
    if not s.get("force_join"): return True
    if int(uid) == ADMIN_ID: return True
    channel = s.get("force_channel", "")
    if not channel or channel == "@YourChannelHere": return True
    try:
        member = await app.get_chat_member(channel, uid)
        return member.status.value not in ("left", "banned", "kicked")
    except: return True

async def send_force_join_msg(m: Message):
    s = get_settings()
    ch = s.get("force_channel", "@YourChannelHere")
    await safe_reply(m, f"⚠️ **Join Required!**\n\nPehle join karo: {ch}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.lstrip('@')}"),
            InlineKeyboardButton("✅ Joined!", callback_data="check_join")
        ]]))

# ─────────────── ACTIVATION PROMPT ───────────────
async def send_activation_prompt(m: Message):
    uid = m.from_user.id
    if is_prompt_cooldown(uid): return
    token = make_token(uid)
    me = await app.get_me()
    link = get_short_link_activation(f"https://t.me/{me.username}?start={token}")
    await safe_reply(m,
        "🔐 **Activation Required**\n\n"
        "• 24H free: Click button\n"
        "• Key: `/activate FILM-XXXX-XXXX-XXXX`\n"
        "• Premium: 💰 /buy",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Get 24H Free", url=link)],
            [InlineKeyboardButton("💰 Buy Premium", callback_data="show_plans")]
        ])
    )

# ══════════════════════════════════════════
#   /start
# ══════════════════════════════════════════
@app.on_message(filters.command("start"))
async def start_handler(_, m: Message):
    uid = m.from_user.id
    users = load_json(USERS_PATH, [])
    is_new = str(uid) not in users
    if is_new:
        users.append(str(uid)); save_json(USERS_PATH, users)
        s = get_settings()
        if s.get("new_user_alert"):
            try:
                await app.send_message(ADMIN_ID,
                    f"🆕 **New User!**\n👤 {m.from_user.first_name}\n🆔 `{uid}`")
            except: pass

    parts = (m.text or "").split(maxsplit=1)
    token = parts[1].strip() if len(parts) > 1 else None

    # File download via start link
    if token and token.startswith("file_"):
        file_key = token[5:]
        await handle_file_request(m, file_key)
        return

    # Token activation
    if token and not token.startswith("FILM-"):
        if not verify_token(token, uid):
            return await safe_reply(m, "❌ Invalid or expired link.")
        activate_user(uid, ACTIVATION_HOURS, method="token")
        exp = (datetime.now() + timedelta(hours=ACTIVATION_HOURS)).strftime("%d %b %Y, %I:%M %p")
        return await safe_reply(m,
            f"🎉 **Activated!**\n⏰ {ACTIVATION_HOURS}H\n📅 Expires: {exp}\n\n🎬 Search movie now!")

    s = get_settings()
    if is_user_active(uid):
        welcome = s.get("welcome_msg", "👋 Welcome back!")
        lvl = get_admin_level(uid)
        badge = f"\n{LEVEL_LABELS.get(lvl,'')}" if lvl > 0 else ""
        return await safe_reply(m,
            f"{welcome}\n\n{get_activation_info(uid)}{badge}\n\n"
            f"🎬 Movie name type karo | /help | /cmd"
        )
    await send_activation_prompt(m)

# ══════════════════════════════════════════
#   FILE REQUEST HANDLER
# ══════════════════════════════════════════
async def handle_file_request(m: Message, file_key: str):
    uid = m.from_user.id
    file_info = get_file(file_key)
    if not file_info or not file_info.get("active"):
        return await safe_reply(m, "❌ File not found or deleted.")
    if is_file_expired(file_info):
        return await safe_reply(m, "⏰ File link expired!")
    if is_file_password_protected(file_info):
        _pending_file_password[str(uid)] = file_key
        return await safe_reply(m,
            f"🔒 **Password Protected File**\n\n"
            f"📁 {file_info.get('title')}\n\n"
            f"Password daalo:"
        )
    await send_file_to_user(m, file_key, file_info)

async def send_file_to_user(m: Message, file_key: str, file_info: dict):
    try:
        msg = await app.copy_message(
            m.chat.id,
            file_info["channel_id"],
            file_info["msg_id"]
        )
        increment_file_download(file_key)
        await safe_reply(m,
            f"📁 **{file_info.get('title')}**\n"
            f"📦 Size: {file_info.get('size','?')}\n"
            f"📥 Downloads: {file_info.get('downloads',0)+1}"
        )
    except Exception as e:
        await safe_reply(m, f"❌ File send failed: {e}")

# ══════════════════════════════════════════
#   /settings INLINE
# ══════════════════════════════════════════
def build_settings_keyboard():
    s = get_settings()
    def tog(k): return "✅ ON" if s.get(k) else "❌ OFF"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔗 DL Shortener: {tog('short')}", callback_data="set:short")],
        [InlineKeyboardButton(f"🔑 Act Shortener: {tog('act_short')}", callback_data="set:act_short")],
        [InlineKeyboardButton(f"🎬 Creator Shortener: {tog('creator_short')}", callback_data="set:creator_short")],
        [InlineKeyboardButton(f"🔗 Original Link: {tog('original_link')}", callback_data="set:original_link")],
        [InlineKeyboardButton(f"🎟️ Movie Token: {tog('movie_token')}", callback_data="set:movie_token")],
        [InlineKeyboardButton(f"📢 Force Join: {tog('force_join')}", callback_data="set:force_join")],
        [InlineKeyboardButton(f"🌙 Maintenance: {tog('maintenance')}", callback_data="set:maintenance")],
        [InlineKeyboardButton(f"🗑️ Auto Delete: {tog('auto_delete')}", callback_data="set:auto_delete")],
        [InlineKeyboardButton(f"🔔 New User Alert: {tog('new_user_alert')}", callback_data="set:new_user_alert")],
        [InlineKeyboardButton(f"🤖 CAPTCHA: {tog('captcha_enabled')}", callback_data="set:captcha_enabled")],
        [InlineKeyboardButton(f"⏰ Timer: {s.get('delete_timer',180)}min", callback_data="set:delete_timer"),
         InlineKeyboardButton(f"⚠️ Max Warn: {s.get('max_warnings',3)}", callback_data="set:max_warnings")],
        [InlineKeyboardButton("❌ Close", callback_data="set:close")]
    ])

@app.on_message(filters.command("settings") & filters.user(ADMIN_ID))
async def settings_cmd(_, m: Message):
    await safe_reply(m, "⚙️ **Bot Settings V16**", reply_markup=build_settings_keyboard())

@app.on_callback_query(filters.regex(r"^set:"))
async def settings_cb(_, q: CallbackQuery):
    if q.from_user.id != ADMIN_ID: return await q.answer("Admin only!", show_alert=True)
    key = q.data.split(":")[1]
    if key == "close": return await q.message.delete()
    if key in ["delete_timer", "max_warnings"]:
        return await q.answer(f"Use /settimer or /setwarn to change", show_alert=True)
    s = get_settings()
    update_setting(key, not s.get(key, False))
    await q.answer(f"{'✅ ON' if not s.get(key) else '❌ OFF'}", show_alert=False)
    await q.message.edit_reply_markup(reply_markup=build_settings_keyboard())

@app.on_message(filters.command("settimer") & filters.user(ADMIN_ID))
async def settimer_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/settimer <minutes>`")
    try: update_setting("delete_timer", int(m.command[1])); await safe_reply(m, f"✅ Timer: {m.command[1]} min")
    except: await safe_reply(m, "❌ Invalid")

@app.on_message(filters.command("setwarn") & filters.user(ADMIN_ID))
async def setwarn_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/setwarn <count>`")
    try: update_setting("max_warnings", int(m.command[1])); await safe_reply(m, f"✅ Max warnings: {m.command[1]}")
    except: await safe_reply(m, "❌ Invalid")

# ══════════════════════════════════════════
#   FETCH WITH STOP/RESUME
# ══════════════════════════════════════════
@app.on_message(filters.command("fetch"))
async def fetch_handler(_, m: Message):
    global _fetch_stop_flag
    if not has_permission(m.from_user.id, "fetch"):
        return await safe_reply(m, "❌ Permission denied.")
    if len(m.command) < 3: return await safe_reply(m, "Usage: `/fetch <from> <to>`")

    try: start, end = int(m.command[1]), int(m.command[2])
    except: return await safe_reply(m, "❌ Invalid range.")

    # Check resume
    state = get_fetch_state()
    if state.get("running") and state.get(
    "start") == start and state.get("end") == end:
        resume_from = state.get("current", start)
        added   = state.get("added", 0)
        skipped = state.get("skipped", 0)
        failed  = state.get("failed", 0)
        await safe_reply(m, f"🔄 Resuming from server {resume_from}...")
    else:
        resume_from = start
        added = skipped = failed = 0

    _fetch_stop_flag = False
    stop_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Fetch", callback_data="stop_fetch")]])
    progress_msg = await safe_reply(m,
        f"🚀 Fetching {start} → {end} (starting from {resume_from})...",
        reply_markup=stop_kb
    )

    existing = load_json(JSON_PATH, [])
    log_lines = []

    for i in range(resume_from, end + 1):
        if _fetch_stop_flag:
            save_fetch_state(start, end, i, added, skipped, failed)
            await progress_msg.edit_text(
                f"🛑 **Fetch Stopped at Server {i}**\n\n"
                f"✅ Added: {added} | ⏭️ Skip: {skipped} | ❌ Failed: {failed}\n\n"
                f"_Use `/fetch {start} {end}` to resume_"
            )
            return

        d = await scrape_server(i)
        if d:
            if not any(int(x.get("server",-1)) == i for x in existing):
                d.setdefault("downloads", 0); existing.append(d); added += 1
                log_lines.append(f"✅ [{i}] {d['title'][:30]}")
            else:
                skipped += 1; log_lines.append(f"⏭️ [{i}] Exists")
        else:
            failed += 1; log_lines.append(f"❌ [{i}] Failed")

        save_fetch_state(start, end, i, added, skipped, failed)

        if (i - resume_from + 1) % 5 == 0 or i == end:
            recent = "\n".join(log_lines[-5:])
            try:
                await progress_msg.edit_text(
                    f"📡 **Fetching... {i-start+1}/{end-start+1}**\n\n"
                    f"{recent}\n\n"
                    f"✅ {added} | ⏭️ {skipped} | ❌ {failed}",
                    reply_markup=stop_kb
                )
            except: pass
        await asyncio.sleep(1.2)

    save_json(JSON_PATH, existing)
    clear_fetch_state()
    await progress_msg.edit_text(
        f"🎉 **Fetch Complete!**\n\n"
        f"✅ Added: **{added}**\n"
        f"⏭️ Skipped: {skipped}\n"
        f"❌ Failed: {failed}\n"
        f"📊 Total: {len(existing)}"
    )

@app.on_callback_query(filters.regex(r"^stop_fetch$"))
async def stop_fetch_cb(_, q: CallbackQuery):
    global _fetch_stop_flag
    if not has_permission(q.from_user.id, "fetch"):
        return await q.answer("Permission denied!", show_alert=True)
    _fetch_stop_flag = True
    await q.answer("🛑 Stopping fetch...", show_alert=True)

# ══════════════════════════════════════════
#   CREATOR COMMANDS
# ══════════════════════════════════════════
@app.on_message(filters.command("addcreator") & filters.user(ADMIN_ID))
async def addcreator_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/addcreator <uid>`")
    uid = m.command[1]
    add_admin(uid, 4)
    register_creator(uid, "Creator")
    await safe_reply(m, f"✅ `{uid}` is now a Creator!")
    try: await app.send_message(int(uid), "🎬 You are now a Creator! Upload files with /upload")
    except: pass

@app.on_message(filters.command("myearnings"))
async def myearnings_cmd(_, m: Message):
    uid = str(m.from_user.id)
    if not is_creator(m.from_user.id): return await safe_reply(m, "❌ Creators only!")
    stats = get_creator_earnings(uid)
    total_dl = stats.get('total_dl', 0)
    need_more = DOWNLOADS_PER_DOLLAR - (total_dl % DOWNLOADS_PER_DOLLAR)
    withdraw_msg = "✅ You can withdraw!" if stats.get('can_withdraw') else f"Need {need_more} more downloads"
    await safe_reply(m,
        f"💰 **Your Earnings**\n\n"
        f"📥 Total Downloads: `{total_dl}`\n"
        f"💵 Total Earned: `${stats.get('earned',0)}`\n"
        f"✅ Withdrawn: `${stats.get('withdrawn',0)}`\n"
        f"⏳ Pending: `${stats.get('pending',0)}`\n\n"
        f"💡 {DOWNLOADS_PER_DOLLAR} downloads = $1\n"
        f"💳 Min withdrawal: ${MIN_WITHDRAWAL}\n\n"
        f"{withdraw_msg}"
    )

@app.on_message(filters.command("myfiles"))
async def myfiles_cmd(_, m: Message):
    uid = str(m.from_user.id)
    if not is_creator(m.from_user.id): return await safe_reply(m, "❌ Creators only!")
    files = get_creator_files(uid)
    if not files: return await safe_reply(m, "📭 No files uploaded yet.")
    text = f"📁 **Your Files ({len(files)}):**\n\n"
    for f in files[:20]:
        exp = "⏰ Expired" if is_file_expired(f) else ""
        pwd = "🔒" if f.get("password") else ""
        text += f"• `{f['key']}` {pwd} — {f['title'][:30]} | 📥 {f.get('downloads',0)} {exp}\n"
    await safe_reply(m, text)

@app.on_message(filters.command("setshortener"))
async def setshortener_cmd(_, m: Message):
    if not is_creator(m.from_user.id): return await safe_reply(m, "❌ Creators only!")
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/setshortener <api_key>`")
    update_creator(str(m.from_user.id), "shortener_api", m.command[1])
    await safe_reply(m, "✅ Your shortener API key saved!")


@app.on_message(filters.command(["deletefile", "delete", "myfiles"]))
async def deletefile_cmd(_, m: Message):
    uid = str(m.from_user.id)
    if not is_creator(m.from_user.id) and not has_permission(m.from_user.id, "all"):
        return await safe_reply(m, "❌ Creators only!")
    
    files = get_creator_files(uid)
    if not files:
        return await safe_reply(m, "📭 No files uploaded yet.")
    
    await show_files_page(m, uid, 0)

async def show_files_page(m, uid, page, is_callback=False):
    files = get_creator_files(uid)
    total = len(files)
    per_page = 8
    start = page * per_page
    chunk = files[start:start + per_page]

    buttons = []
    for f in chunk:
        pwd = "🔒 " if f.get("password") else ""
        exp = "⏰" if is_file_expired(f) else ""
        label = f"{pwd}{exp}{f['title'][:30]} | 📥{f.get('downloads',0)}"
        buttons.append([InlineKeyboardButton(
            label,
            callback_data=f"fdetail:{uid}:{f['key']}"
        )])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀️ Prev", callback_data=f"fpage:{uid}:{page-1}"))
    if start + per_page < total:
        nav.append(InlineKeyboardButton("Next ▶️", callback_data=f"fpage:{uid}:{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="close_page")])

    text = (
        f"📁 Your Files ({total})\n"
        f"Page {page+1}/{max(1,(total+per_page-1)//per_page)}"
    )

    markup = InlineKeyboardMarkup(buttons)
    if is_callback:
        try:
            await m.edit_text(text, reply_markup=markup)
        except:
            await m.reply_text(text, reply_markup=markup)
    else:
        await m.reply_text(text, reply_markup=markup)

@app.on_callback_query(filters.regex(r"^fpage:"))
async def fpage_cb(_, q: CallbackQuery):
    parts = q.data.split(":")
    uid = parts[1]
    page = int(parts[2])
    if str(q.from_user.id) != uid:
        return await q.answer("❌ Not yours!", show_alert=True)
    await q.answer()
    await show_files_page(q.message, uid, page)

@app.on_callback_query(filters.regex(r"^fdetail:"))
async def fdetail_cb(_, q: CallbackQuery):
    parts = q.data.split(":")
    uid = parts[1]
    file_key = parts[2]
    
    if str(q.from_user.id) != uid:
        return await q.answer("❌ Not yours!", show_alert=True)
    
    file_info = get_file(file_key)
    if not file_info:
        return await q.answer("❌ File not found!", show_alert=True)
    
    exp_str = "Never" if not file_info.get("expiry_ts") else datetime.fromtimestamp(file_info["expiry_ts"]).strftime("%d %b %Y")
    pwd_str = "🔒 Yes" if file_info.get("password") else "🔓 No"
    
    text = (
        f"📁 File Details\n\n"
        f"Title: {file_info.get('title')}\n"
        f"Type: {file_info.get('file_type','?')}\n"
        f"Size: {file_info.get('size','?')}\n"
        f"Key: {file_key}\n"
        f"Downloads: {file_info.get('downloads',0)}\n"
        f"Password: {pwd_str}\n"
        f"Expires: {exp_str}\n"
        f"Uploaded: {file_info.get('uploaded_at','')[:10]}"
    )
    
    buttons = [
        [InlineKeyboardButton("🗑️ Delete", callback_data=f"fdel:{uid}:{file_key}"),
         InlineKeyboardButton("✏️ Rename", callback_data=f"frename:{uid}:{file_key}")],
        [InlineKeyboardButton("🔙 Back", callback_data=f"fpage:{uid}:0")]
    ]
    
    await q.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^fdel:"))
async def fdel_cb(_, q: CallbackQuery):
    parts = q.data.split(":")
    uid = parts[1]
    file_key = parts[2]
    
    if str(q.from_user.id) != uid:
        return await q.answer("❌ Not yours!", show_alert=True)
    
    delete_file(file_key)
    await q.answer("✅ File deleted!", show_alert=True)
    await show_files_page(q.message, uid, 0)

_rename_pending = {}

@app.on_callback_query(filters.regex(r"^frename:"))
async def frename_cb(_, q: CallbackQuery):
    parts = q.data.split(":")
    uid = parts[1]
    file_key = parts[2]
    
    if str(q.from_user.id) != uid:
        return await q.answer("❌ Not yours!", show_alert=True)
    
    _rename_pending[str(q.from_user.id)] = file_key
    await q.answer()
    await q.message.edit_text(
        f"✏️ Rename File\n\nFile: {file_key}\n\nNaya title type karo:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data=f"fdetail:{uid}:{file_key}")]
        ])
    )

@app.on_message(filters.text & filters.private, group=-2)
async def rename_handler(_, m: Message):
    uid = str(m.from_user.id)
    if uid not in _rename_pending: return
    
    file_key = _rename_pending.pop(uid)
    new_title = m.text.strip()
    
    files = load_json(FILES_DB_PATH, {})
    if file_key in files:
        files[file_key]["title"] = new_title
        save_json(FILES_DB_PATH, files)
        await safe_reply(m, f"✅ Renamed to: {new_title}")
    else:
        await safe_reply(m, "❌ File not found!")
#@app.on_message(filters.command("deletefile"))
#async def deletefile_cmd(_, m: Message):
#    uid = str(m.from_user.id)
#    if not is_creator(m.from_user.id) and not has_permission(m.from_user.id, "all"):
#        return await safe_reply(m, "❌ Creators only!")
#    if len(m.command) < 2: return await safe_reply(m, "Usage: `/deletefile <file_key>`")
#    key = m.command[1].upper()
#    file_info = get_file(key)
#    if not file_info: return await safe_reply(m, "❌ File not found.")
#    if str(file_info.get("creator_uid")) != uid and not has_permission(m.from_user.id, "all"):
#        return await safe_reply(m, "❌ Not your file!")
#    delete_file(key)
#    await safe_reply(m, f"✅ File `{key}` deleted.")

# File upload handler
#@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo))
#async def file_upload_handler(_, m: Message):
#    uid = m.from_user.id
#    if not is_creator(uid): return

#    # Get file info
#    if m.document:
#        file_obj  = m.document
#        file_type = "document"
#        size_bytes = file_obj.file_size
#    elif m.video:
#        file_obj  = m.video
#        file_type = "video"
#        size_bytes = file_obj.file_size
#    elif m.audio:
#        file_obj  = m.audio
#        file_type = "audio"
#        size_bytes = file_obj.file_size
#    elif m.photo:
#        file_obj  = m.photo
#        file_type = "photo"
#        size_bytes = 0
#    else:
#        return

#    # Get title from caption or file name
#    caption   = m.caption or ""
#    file_name = getattr(file_obj, "file_name", "file") or "file"
#    title     = caption.strip() if caption.strip() else file_name

#    # Size string
#    if size_bytes:
#        if size_bytes > 1073741824: size_str = f"{size_bytes/1073741824:.1f} GB"
#        elif size_bytes > 1048576:  size_str = f"{size_bytes/1048576:.1f} MB"
#        else:                       size_str = f"{size_bytes/1024:.1f} KB"
#    else:
#        size_str = "Unknown"

#    try:
#        forwarded = await app.copy_message(
#    chat_id=FILE_CHANNEL_ID,
#    from_chat_id=m.chat.id,
#    message_id=m.id
#)
#        # Forward to channel
#        #forwarded = await m.forward(FILE_CHANNEL_ID)
#        msg_id    = forwarded.id
#  

#        # Get creator info
#        creator = get_creator(str(uid)) or {}
#        creator_api = creator.get("shortener_api", "")

#        # Add to DB
#        file_key = add_file(
#            creator_uid=str(uid),
#            file_id=getattr(file_obj, "file_id", ""),
#            file_name=file_name,
#            title=title,
#            file_type=file_type,
#            size=size_str,
#            msg_id=msg_id,
#            channel_id=FILE_CHANNEL_ID,
#        )

#        # Build download link
#        me = await app.get_me()
#        dl_link = build_file_link(me.username, file_key)

#        # Short link
#        s = get_settings()
#        if s.get("creator_short"):
#            short = get_creator_short_link(dl_link, creator_api)
#        else:
#            short = dl_link

#        await safe_reply(m,
#            f"✅ **File Uploaded!**\n\n"
#            f"📁 Title: {title}\n"
#            f"📦 Size: {size_str}\n"
#            f"🔑 Key: `{file_key}`\n\n"
#            f"🔗 **Download Link:**\n`{short}`\n\n"
#            f"Share this link with users!"
#        )
#    except Exception as e:
#        await safe_reply(m, f"❌ Upload failed: {e}")

# File upload handler v2
@app.on_message(filters.private & (filters.document | filters.video | filters.audio | filters.photo), group=-1)
async def file_upload_handler(_, m: Message):
    uid = m.from_user.id
    if not is_creator(uid): return

    if m.document:
        file_obj = m.document
        file_type = "document"
        size_bytes = file_obj.file_size or 0
    elif m.video:
        file_obj = m.video
        file_type = "video"
        size_bytes = file_obj.file_size or 0
    elif m.audio:
        file_obj = m.audio
        file_type = "audio"
        size_bytes = file_obj.file_size or 0
    elif m.photo:
        file_obj = m.photo
        file_type = "photo"
        size_bytes = 0
    else:
        return

    caption = m.caption or ""
    file_name = getattr(file_obj, "file_name", "file") or "file"
    title = caption.strip() if caption.strip() else file_name

    if size_bytes > 1073741824:
        size_str = f"{size_bytes/1073741824:.1f} GB"
    elif size_bytes > 1048576:
        size_str = f"{size_bytes/1048576:.1f} MB"
    elif size_bytes > 0:
        size_str = f"{size_bytes/1024:.1f} KB"
    else:
        size_str = "Unknown"

    try:
        forwarded = await app.copy_message(
            chat_id=FILE_CHANNEL_ID,
            from_chat_id=m.chat.id,
            message_id=m.id
        )
        msg_id = forwarded.id

        creator = get_creator(str(uid)) or {}
        creator_api = creator.get("shortener_api", "")

        file_key = add_file(
            creator_uid=str(uid),
            file_id=getattr(file_obj, "file_id", ""),
            file_name=file_name,
            title=title,
            file_type=file_type,
            size=size_str,
            msg_id=msg_id,
            channel_id=FILE_CHANNEL_ID,
        )

        me = await app.get_me()
        dl_link = build_file_link(me.username, file_key)

        s = get_settings()
        if s.get("creator_short"):
            short = get_creator_short_link(dl_link, creator_api)
        else:
            short = dl_link

        await safe_reply(m,
            f"✅ **File Uploaded!**\n\n"
            f"📁 Title: {title}\n"
            f"📦 Size: {size_str}\n"
            f"🔑 Key: `{file_key}`\n\n"
            f"🔗 **Download Link:**\n`{short}`\n\n"
            f"Share this link with users!"
        )
    except Exception as e:
        print(f"[Upload Error] {type(e).__name__}: {e}")
        await safe_reply(m, f"❌ Upload failed: {type(e).__name__}: {e}")
# ══════════════════════════════════════════
#   SEARCH — MOVIES + FILES
# ══════════════════════════════════════════
@app.on_message(filters.command(["filter", "search"]) & (filters.private | filters.group))
async def filter_cmd(_, m: Message):
    uid = m.from_user.id
    if str(uid) in load_json(BANNED_PATH, []): return
    s = get_settings()
    if s.get("maintenance") and int(uid) != ADMIN_ID:
        return await safe_reply(m, "🌙 Bot maintenance mein hai.")
    if not await check_force_join(uid): return await send_force_join_msg(m)
    if not is_user_active(uid): return await send_activation_prompt(m)
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/filter <movie>`")
    await handle_search(m, m.text.split(None, 1)[1].strip().lower())

@app.on_message(filters.command("searchall"))
async def searchall_cmd(_, m: Message):
    if not is_user_active(m.from_user.id): return await send_activation_prompt(m)
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/searchall <word1> <word2>`")
    keywords = m.text.split(None, 1)[1].strip().lower().split()
    data = load_json(JSON_PATH, [])
    found = [d for d in data if all(k in d.get("title","").lower() for k in keywords)]
    if not found: return await safe_reply(m, "❌ No results.")
    text = f"🔍 **Results for:** `{' + '.join(keywords)}`\n\n"
    for i, item in enumerate(found[:10], 1):
        text += f"{i}. {item['title']} ({item.get('size','?')})\n"
    await safe_reply(m, text)

@app.on_message(filters.command("random"))
async def random_cmd(_, m: Message):
    if not is_user_active(m.from_user.id): return await send_activation_prompt(m)
    data = load_json(JSON_PATH, [])
    if not data: return await safe_reply(m, "❌ No movies in database.")
    item = random.choice(data)
    rows, row = [], []
    s = get_settings()
    for i, l in enumerate(item.get("links",[])):
        url = SITE_PREFIX + l
        if s.get("movie_token"): url = get_short_link(url)
        row.append(InlineKeyboardButton(f"DL {i+1}", url=url))
        if (i+1) % 3 == 0: rows.append(row); row=[]
    if row: rows.append(row)
    await safe_reply(m,
        f"🎲 **Random Movie:**\n\n"
        f"🎬 **{item.get('title')}**\n"
        f"📦 `{item.get('size','?')}` | 📥 {item.get('downloads',0)}",
        reply_markup=InlineKeyboardMarkup(rows) if rows else None
    )

#@app.on_message(filters.text & (filters.private | filters.group))
#async def direct_search(_, m: Message):
@app.on_message(filters.text & (filters.private | filters.group), group=-1)
async def direct_search(_, m: Message):   
    if m.text.startswith("/"): return
    uid = m.from_user.id
    if str(uid) in load_json(BANNED_PATH, []): return

    # Password check for file
    if str(uid) in _pending_file_password:
        file_key = _pending_file_password.pop(str(uid))
        file_info = get_file(file_key)
        if file_info and check_file_password(file_info, m.text.strip()):
            await send_file_to_user(m, file_key, file_info)
        else:
            await safe_reply(m, "❌ Wrong password!")
        return

    # Bad word check
    bad = contains_bad_word(m.text)
    if bad:
        log_bad_word(str(uid), bad, m.text)
        s = get_settings()
        max_warn = int(s.get("max_warnings", 3))
        warn_count = add_warning(str(uid), f"Bad word: {bad}")
        if warn_count >= max_warn:
            banned = load_json(BANNED_PATH, [])
            if str(uid) not in banned:
                banned.append(str(uid)); save_json(BANNED_PATH, banned)
            await safe_reply(m, f"🚫 User `{uid}` auto-banned after {warn_count} warnings!")
        else:
            await safe_reply(m, f"⚠️ Warning {warn_count}/{max_warn}! Bad word detected.")
        try: await m.delete()
        except: pass
        return

    # Mute check
    if is_muted(str(uid)):
        try: await m.delete()
        except: pass
        return

    # Spam check
    if check_spam(uid):
        return await safe_reply(m, "⏳ Spam detected! Slow down.")

    s = get_settings()
    if s.get("maintenance") and int(uid) != ADMIN_ID:
        return await safe_reply(m, "🌙 Maintenance mode.")
    if not await check_force_join(uid): return await send_force_join_msg(m)
    if not is_user_active(uid): return await send_activation_prompt(m)
    if is_rate_limited(uid): return await safe_reply(m, f"⏳ Wait {SEARCH_COOLDOWN}s.")
    await handle_search(m, m.text.strip().lower())

async def handle_search(m: Message, query: str):
    save_search(str(m.from_user.id), query)
    s = get_settings()

    # Search movies
    data  = load_json(JSON_PATH, [])
    movies = [d for d in data if query in d.get("title","").lower()]

    # Search files too
    files_found = search_files(query) if is_user_active(m.from_user.id) else []

    if not movies and not files_found:
        suggestions = get_close_matches(query, [d.get("title","").lower() for d in data], n=4, cutoff=0.45)
        text = ("❌ **No results.**\n\n🔍 **Did you mean?**\n" +
                "\n".join([f"• `{s.title()}`" for s in suggestions])) if suggestions else "❌ No results found."
        bot_msg = await m.reply_text(text)
        asyncio.create_task(schedule_delete(m, bot_msg))
        return

    # Build response
    text_parts = []
    rows = []

    if movies:
        item = movies[0]
        row = []
        for i, l in enumerate(item.get("links",[])):
            url = SITE_PREFIX + l
            if s.get("movie_token"): url = get_short_link(url)
            row.append(InlineKeyboardButton(f"DL {i+1}", url=url))
            if (i+1) % 3 == 0: rows.append(row); row=[]
        if row: rows.append(row)
        nav = []
        if len(movies) > 1:
            nav.append(InlineKeyboardButton(f"🎬 All {len(movies)} movies", callback_data=f"page:{query}:0"))
        nav.append(InlineKeyboardButton("⭐ Star", callback_data=f"star:{item['server']}"))
        rows.append(nav)
        text_parts.append(f"🎬 **{item.get('title')}**\n📦 `{item.get('size','?')}` | 📥 {item.get('downloads',0)}")

    if files_found:
        text_parts.append(f"\n📁 **Files ({len(files_found)}):**")
        for f in files_found[:3]:
            pwd = "🔒 " if f.get("password") else ""
            text_parts.append(f"• {pwd}`{f['key']}` — {f['title'][:30]} | 📥 {f.get('downloads',0)}")
            rows.append([InlineKeyboardButton(f"📥 {f['title'][:30]}", callback_data=f"dlfile:{f['key']}")])

    bot_msg = await m.reply_text(
        "\n".join(text_parts) + f"\n\n_{len(movies)} movie(s), {len(files_found)} file(s)_",
        reply_markup=InlineKeyboardMarkup(rows) if rows else None
    )
    asyncio.create_task(schedule_delete(m, bot_msg))

# ══════════════════════════════════════════
#   CALLBACKS
# ══════════════════════════════════════════
@app.on_callback_query(filters.regex(r"^check_join$"))
async def check_join_cb(_, q: CallbackQuery):
    joined = await check_force_join(q.from_user.id)
    if joined: await q.answer("✅ Verified!", show_alert=True); await q.message.delete()
    else: await q.answer("❌ Not joined yet!", show_alert=True)

@app.on_callback_query(filters.regex(r"^page:"))
async def page_nav(_, q: CallbackQuery):
    try:
        _, query, start_str = q.data.split(":", 2)
        start = int(start_str)
        data  = load_json(JSON_PATH, [])
        found = [d for d in data if query in d.get("title","").lower()]
        if not found: return await q.answer("No results", show_alert=True)
        buttons = []
        for offset, item in enumerate(found[start:start+PAGE_SIZE]):
            idx = start + offset
            buttons.append([InlineKeyboardButton(
                f"[{item.get('size','?')}] {item.get('title','')[:38]}",
                callback_data=f"show:{query}:{idx}"
            )])
        nav_row = []
        if start > 0: nav_row.append(InlineKeyboardButton("◀️", callback_data=f"page:{query}:{max(0,start-PAGE_SIZE)}"))
        if start + PAGE_SIZE < len(found): nav_row.append(InlineKeyboardButton("▶️", callback_data=f"page:{query}:{start+PAGE_SIZE}"))
        nav_row.append(InlineKeyboardButton("❌", callback_data="close_page"))
        await q.message.edit_text(
            f"🔎 `{query}` — {len(found)} results | Page {start//PAGE_SIZE+1}",
            reply_markup=InlineKeyboardMarkup(buttons + [nav_row])
        )
    except Exception as e: logger.exception("page_nav: %s", e); await q.answer("Error", show_alert=True)

@app.on_callback_query(filters.regex(r"^show:"))
async def show_item(_, q: CallbackQuery):
    try:
        parts = q.data.split(":", 2)
        query = parts[1]; idx = int(parts[2])
        data  = load_json(JSON_PATH, [])
        found = [d for d in data if query in d.get("title","").lower()]
        if idx >= len(found): return await q.answer("Invalid", show_alert=True)
        item = found[idx]
        s = get_settings()
        rows, row = [], []
        for i, l in enumerate(item.get("links",[])):
            url = SITE_PREFIX + l
            if s.get("movie_token"): url = get_short_link(url)  # FIX: same logic as first result
            row.append(InlineKeyboardButton(f"Download {i+1}", url=url))
            if (i+1) % 3 == 0: rows.append(row); row=[]
        if row: rows.append(row)
        back = max(0, idx - (idx % PAGE_SIZE))
        rows.append([
            InlineKeyboardButton("⭐ Star", callback_data=f"star:{item['server']}"),
            InlineKeyboardButton("🔙 Back", callback_data=f"page:{query}:{back}")
        ])
        increment_download(item["server"])
        await q.message.edit_text(
            f"📁 **{item.get('title')}**\n📦 `{item.get('size','?')}` | 📥 {item.get('downloads',0)+1}",
            reply_markup=InlineKeyboardMarkup(rows)
        )
    except Exception as e: logger.exception("show_item: %s", e); await q.answer("Error", show_alert=True)

@app.on_callback_query(filters.regex(r"^star:"))
async def star_cb(_, q: CallbackQuery):
    try:
        server_id = int(q.data.split(":")[1])
        data = load_json(JSON_PATH, [])
        item = next((d for d in data if int(d.get("server",-1)) == server_id), None)
        if not item: return await q.answer("Not found", show_alert=True)
        added = star_movie(str(q.from_user.id), item)
        await q.answer("⭐ Starred! /mystars" if added else "Already starred ⭐", show_alert=True)
    except Exception as e: logger.exception("star_cb: %s", e)

@app.on_callback_query(filters.regex(r"^dlfile:"))
async def dlfile_cb(_, q: CallbackQuery):
    file_key = q.data.split(":")[1]
    file_info = get_file(file_key)
    if not file_info: return await q.answer("File not found!", show_alert=True)
    if is_file_expired(file_info): return await q.answer("⏰ File expired!", show_alert=True)
    await q.answer()
    if is_file_password_protected(file_info):
        _pending_file_password[str(q.from_user.id)] = file_key
        await app.send_message(q.from_user.id, f"🔒 Password daalo for: {file_info.get('title')}")
    else:
        await send_file_to_user(q.message, file_key, file_info)

@app.on_callback_query(filters.regex(r"^close_page$"))
async def close_page_cb(_, q: CallbackQuery):
    try: await q.message.delete()
    except: await q.answer("Cannot close.")

# ══════════════════════════════════════════
#   MODERATION
# ══════════════════════════════════════════
@app.on_message(filters.command("warn"))
async def warn_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    target_uid = None
    if m.reply_to_message:
        target_uid = str(m.reply_to_message.from_user.id)
    elif len(m.command) >= 2:
        target_uid = m.command[1]
    if not target_uid: return await safe_reply(m, "Reply to message or provide UID.")
    reason = " ".join(m.command[2:]) if len(m.command) > 2 else "No reason"
    s = get_settings()
    max_warn = int(s.get("max_warnings", 3))
    count = add_warning(target_uid, reason)
    if count >= max_warn:
        banned = load_json(BANNED_PATH, [])
        if target_uid not in banned: banned.append(target_uid); save_json(BANNED_PATH, banned)
        await safe_reply(m, f"🚫 `{target_uid}` auto-banned after {count} warnings!")
    else:
        await safe_reply(m, f"⚠️ Warning {count}/{max_warn} given to `{target_uid}`\nReason: {reason}")

@app.on_message(filters.command("warnings"))
async def warnings_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    target_uid = m.reply_to_message.from_user.id if m.reply_to_message else (m.command[1] if len(m.command) > 1 else None)
    if not target_uid: return await safe_reply(m, "Provide UID or reply.")
    warns = get_warnings(str(target_uid))
    if not warns: return await safe_reply(m, f"✅ `{target_uid}` has no warnings.")
    text = f"⚠️ **Warnings for `{target_uid}` ({len(warns)}):**\n\n"
    for i, w in enumerate(warns, 1): text += f"{i}. {w['reason']} — {w['time']}\n"
    await safe_reply(m, text)

@app.on_message(filters.command("clearwarn"))
async def clearwarn_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    uid = m.reply_to_message.from_user.id if m.reply_to_message else (m.command[1] if len(m.command) > 1 else None)
    if not uid: return await safe_reply(m, "Provide UID or reply.")
    clear_warnings(str(uid)); await safe_reply(m, f"✅ Warnings cleared for `{uid}`")

@app.on_message(filters.command("mute"))
async def mute_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    target = m.reply_to_message.from_user.id if m.reply_to_message else (m.command[1] if len(m.command) > 1 else None)
    if not target: return await safe_reply(m, "Provide UID or reply.")
    mins = int(m.command[-1]) if m.command[-1].isdigit() else 60
    mute_user(str(target), mins)
    await safe_reply(m, f"🔇 `{target}` muted for {mins} minutes.")

@app.on_message(filters.command("unmute"))
async def unmute_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    uid = m.reply_to_message.from_user.id if m.reply_to_message else (m.command[1] if len(m.command) > 1 else None)
    if not uid: return await safe_reply(m, "Provide UID or reply.")
    unmute_user(str(uid)); await safe_reply(m, f"🔊 `{uid}` unmuted!")

@app.on_message(filters.command("ban"))
async def ban_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    # Reply to message to ban
    if m.reply_to_message:
        uid = str(m.reply_to_message.from_user.id)
    elif len(m.command) >= 2:
        uid = m.command[1]
    else:
        return await safe_reply(m, "Reply to message or provide UID.")
    banned = load_json(BANNED_PATH, [])
    if uid in banned: return await safe_reply(m, f"`{uid}` already banned.")
    banned.append(uid); save_json(BANNED_PATH, banned)
    await safe_reply(m, f"✅ Banned `{uid}`")

@app.on_message(filters.command("unban"))
async def unban_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "unban"): return await safe_reply(m, "❌ Permission denied.")
    uid = m.command[1] if len(m.command) > 1 else None
    if not uid: return await safe_reply(m, "Provide UID.")
    banned = load_json(BANNED_PATH, [])
    if uid not in banned: return await safe_reply(m, "Not banned.")
    banned.remove(uid); save_json(BANNED_PATH, banned)
    await safe_reply(m, f"✅ Unbanned `{uid}`")

@app.on_message(filters.command("purge"))
async def purge_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    if not m.reply_to_message: return await safe_reply(m, "Reply to message to start purge from.")
    from_id = m.reply_to_message.id
    to_id   = m.id
    deleted = 0
    for msg_id in range(from_id, to_id + 1):
        try: await app.delete_messages(m.chat.id, msg_id); deleted += 1
        except: pass
    await safe_reply(m, f"🗑️ Purged {deleted} messages.")

@app.on_message(filters.command("report"))
async def report_cmd(_, m: Message):
    if not m.reply_to_message: return await safe_reply(m, "Reply to a message to report it.")
    reporter = str(m.from_user.id)
    reported = str(m.reply_to_message.from_user.id)
    reason   = m.text.split(None, 1)[1] if len(m.text.split()) > 1 else "No reason"
    add_report(reporter, reported, reason, m.reply_to_message.text or "")
    await safe_reply(m, "✅ Report submitted to admin!")
    try:
        await app.send_message(ADMIN_ID,
            f"🚨 **New Report!**\n\n"
            f"Reporter: `{reporter}`\n"
            f"Reported: `{reported}`\n"
            f"Reason: {reason}\n\n"
            f"Use /reports to view all."
        )
    except: pass

@app.on_message(filters.command("reports") & filters.user(ADMIN_ID))
async def reports_cmd(_, m: Message):
    pending = get_reports("pending")
    if not pending: return await safe_reply(m, "✅ No pending reports.")
    text = f"🚨 **Pending Reports ({len(pending)}):**\n\n"
    for r in pending[:10]:
        text += f"Reporter: `{r['reporter']}` → Reported: `{r['reported']}`\nReason: {r['reason']}\n\n"
    await safe_reply(m, text)

# ══════════════════════════════════════════
#   NOTES
# ══════════════════════════════════════════
@app.on_message(filters.command("save") & filters.user(ADMIN_ID))
async def save_note_cmd(_, m: Message):
    parts = m.text.split(None, 2)
    if len(parts) < 3: return await safe_reply(m, "Usage: `/save <key> <text>`")
    save_note(parts[1], parts[2], str(m.from_user.id))
    await safe_reply(m, f"✅ Note `{parts[1]}` saved!")

@app.on_message(filters.command("note"))
async def get_note_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/note <key>`")
    note = get_note(m.command[1])
    if not note: return await safe_reply(m, "❌ Note not found.")
    await safe_reply(m, f"📌 **{m.command[1]}:**\n\n{note['text']}")

@app.on_message(filters.command("notes"))
async def notes_list_cmd(_, m: Message):
    notes = get_all_notes()
    if not notes: return await safe_reply(m, "📭 No notes saved.")
    text = f"📌 **Notes ({len(notes)}):**\n\n"
    for key in notes: text += f"• `{key}`\n"
    await safe_reply(m, text)

@app.on_message(filters.command("delnote") & filters.user(ADMIN_ID))
async def delnote_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/delnote <key>`")
    if delete_note(m.command[1]): await safe_reply(m, f"✅ Note `{m.command[1]}` deleted!")
    else: await safe_reply(m, "❌ Note not found.")

# ══════════════════════════════════════════
#   PIN
# ══════════════════════════════════════════
@app.on_message(filters.command("pin"))
async def pin_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "ban"): return await safe_reply(m, "❌ Permission denied.")
    if m.reply_to_message:
        try: await m.reply_to_message.pin(); await safe_reply(m, "📌 Message pinned!")
        except: await safe_reply(m, "❌ Cannot pin. Admin rights needed.")
    else: return await safe_reply(m, "Reply to message to pin it.")

# ══════════════════════════════════════════
#   /mystats
# ══════════════════════════════════════════
@app.on_message(filters.command("mystats"))
async def mystats_cmd(_, m: Message):
    uid = str(m.from_user.id)
    history = get_search_history(uid)
    stars   = get_stars(uid)
    warns   = get_warnings(uid)
    await safe_reply(m,
        f"📊 **Your Stats**\n\n"
        f"🆔 ID: `{m.from_user.id}`\n"
        f"🔍 Total Searches: {len(history)}\n"
        f"⭐ Starred Movies: {len(stars)}\n"
        f"⚠️ Warnings: {len(warns)}\n"
        f"📋 {get_activation_info(m.from_user.id)}"
    )

# ══════════════════════════════════════════
#   REMAINING USER COMMANDS
# ══════════════════════════════════════════
@app.on_message(filters.command("activate"))
async def activate_cmd(_, m: Message):
    uid = m.from_user.id
    if str(uid) in load_json(BANNED_PATH, []): return await safe_reply(m, "⛔ Banned.")
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/activate FILM-XXXX-XXXX-XXXX`")
    if is_user_active(uid): return await safe_reply(m, f"✅ Already active!\n{get_activation_info(uid)}")
    success, msg = use_key(m.command[1].strip().upper(), uid)
    await safe_reply(m, f"🎉 **Key Activated!**\n{get_activation_info(uid)}\n\n🎬 Search now!" if success else msg)

@app.on_message(filters.command("myplan"))
async def myplan_cmd(_, m: Message):
    uid = m.from_user.id
    if int(uid) == ADMIN_ID: return await safe_reply(m, "👑 Admin — Lifetime!")
    if not is_user_active(uid): return await safe_reply(m, "❌ Not activated!\nUse /start")
    activ = load_json(ACTIVATIONS_PATH, {})
    rec = activ.get(str(uid), {})
    exp = datetime.fromtimestamp(int(rec["expires_at_ts"]))
    remaining = exp - datetime.now()
    await safe_reply(m,
        f"📋 **Your Plan**\n\n"
        f"🆔 `{uid}`\n"
        f"📅 Expires: {exp.strftime('%d %b %Y, %I:%M %p')}\n"
        f"⏳ Remaining: **{remaining.days}d {remaining.seconds//3600}h**"
    )

@app.on_message(filters.command("me"))
async def me_cmd(_, m: Message):
    uid = m.from_user.id
    lvl = get_admin_level(uid)
    badge = f"\n{LEVEL_LABELS.get(lvl,'')}" if lvl > 0 else ""
    await safe_reply(m,
        f"👤 **Profile**\n\n"
        f"🆔 `{uid}`\n"
        f"📋 {get_activation_info(uid)}{badge}\n"
        f"⭐ Starred: {len(get_stars(str(uid)))}\n"
        f"🕐 Searches: {len(get_search_history(str(uid)))}"
    )

@app.on_message(filters.command("myhistory"))
async def myhistory_cmd(_, m: Message):
    history = get_search_history(str(m.from_user.id))
    if not history: return await safe_reply(m, "📭 No search history.")
    text = f"🕐 **Recent Searches:**\n\n"
    for i, h in enumerate(history[:20], 1): text += f"{i}. `{h['query']}` — _{h['time']}_\n"
    await safe_reply(m, text)

@app.on_message(filters.command("trending"))
async def trending_cmd(_, m: Message):
    if not is_user_active(m.from_user.id): return await send_activation_prompt(m)
    data = load_json(JSON_PATH, [])
    top = sorted(data, key=lambda x: x.get("downloads",0), reverse=True)[:10]
    if not top: return await safe_reply(m, "📭 No data.")
    text = "🔥 **Top 10 Trending**\n\n"
    for i, item in enumerate(top, 1): text += f"{i}. **{item['title']}** — 📥 {item.get('downloads',0)}\n"
    await safe_reply(m, text)

@app.on_message(filters.command("mystars"))
async def mystars_cmd(_, m: Message):
    stars = get_stars(str(m.from_user.id))
    if not stars: return await safe_reply(m, "⭐ No starred movies.")
    text = f"⭐ **Starred ({len(stars)}):**\n\n"
    for i, s in enumerate(stars, 1): text += f"{i}. {s['title']} `({s['size']})`\n"
    await safe_reply(m, text)

@app.on_message(filters.command("help"))
async def help_cmd(_, m: Message):
    await safe_reply(m,
        "📘 **Bot Help — V16**\n\n"
        "🎬 Type movie name to search\n"
        "/start — Activate | /buy — Plans\n"
        "/activate KEY | /myplan | /me\n"
        "/mystars | /myhistory | /mystats\n"
        "/trending | /random | /searchall\n"
        "/report — Report user\n"
        "/note KEY — Get saved note\n"
        "/cmd — All commands"
    )

# ══════════════════════════════════════════
#   ADMIN COMMANDS
# ══════════════════════════════════════════
@app.on_message(filters.command("genkey"))
async def genkey_cmd(_, m: Message):
    if not has_permission(m.from_user.id, "genkey"): return await safe_reply(m, "❌ Permission denied.")
    try: count = int(m.command[1]) if len(m.command) > 1 else 1; days = int(m.command[2]) if len(m.command) > 2 else 30
    except: return await safe_reply(m, "Usage: `/genkey <count> <days>`")
    new_keys = create_keys(count, days)
    await safe_reply(m, f"🔑 **{count} Key(s) — {days} Day Plan**\n\n" + "\n".join([f"`{k}`" for k in new_keys]))

@app.on_message(filters.command("keys"))
async def list_keys(_, m: Message):
    if not has_permission(m.from_user.id, "genkey"): return await safe_reply(m, "❌ Permission denied.")
    keys_db = load_json(KEYS_PATH, {})
    unused = {k: v for k, v in keys_db.items() if not v.get("used")}
    if not unused: return await safe_reply(m, "📭 No unused keys.")
    text = f"🔑 **Unused Keys ({len(unused)}):**\n\n"
    for k, v in list(unused.items())[:30]: text += f"`{k}` — {v['days']} days\n"
    await safe_reply(m, text)

@app.on_message(filters.command("actuser") & filters.user(ADMIN_ID))
async def actuser_cmd(_, m: Message):
    if len(m.command) < 3: return await safe_reply(m, "Usage: `/actuser <uid> <hours>`")
    try: uid, hours = int(m.command[1]), int(m.command[2])
    except: return await safe_reply(m, "❌ Invalid")
    activate_user(uid, hours, method="admin")
    exp = (datetime.now() + timedelta(hours=hours)).strftime("%d %b %Y")
    await safe_reply(m, f"✅ `{uid}` activated {hours}h → {exp}")

@app.on_message(filters.command("adddays") & filters.user(ADMIN_ID))
async def adddays_cmd(_, m: Message):
    if len(m.command) < 3: return await safe_reply(m, "Usage: `/adddays <uid> <days>`")
    try: uid, days = int(m.command[1]), int(m.command[2])
    except: return await safe_reply(m, "❌ Invalid")
    new_exp = extend_user(uid, days)
    await safe_reply(m, f"✅ +{days} days to `{uid}` → {new_exp}")

@app.on_message(filters.command("revoke") & filters.user(ADMIN_ID))
async def revoke_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/revoke <uid>`")
    try: uid = int(m.command[1])
    except: return await safe_reply(m, "❌ Invalid")
    deactivate_user(uid); await safe_reply(m, f"✅ Revoked `{uid}`")

@app.on_message(filters.command("actlist") & filters.user(ADMIN_ID))
async def actlist_cmd(_, m: Message):
    activ = load_json(ACTIVATIONS_PATH, {})
    now = int(time.time())
    active = {k: v for k, v in activ.items() if int(v.get("expires_at_ts",0)) > now}
    if not active: return await safe_reply(m, "📭 No active users.")
    text = f"✅ **Active ({len(active)}):**\n\n"
    for uid, info in list(active.items())[:30]:
        exp = datetime.fromtimestamp(int(info["expires_at_ts"])).strftime("%d %b %Y")
        text += f"{'🔑' if info.get('method')=='key' else '🔗'} `{uid}` — {exp}\n"
    await safe_reply(m, text)

@app.on_message(filters.command("status") & filters.user(ADMIN_ID))
async def status_handler(_, m: Message):
    data = load_json(JSON_PATH, [])
    users = load_json(USERS_PATH, [])
    activ = load_json(ACTIVATIONS_PATH, {})
    s = get_settings()
    active = sum(1 for v in activ.values() if int(v.get("expires_at_ts",0)) > int(time.time()))
    files = load_json(FILES_DB_PATH, {})
    await safe_reply(m,
        f"📊 **V16 Stats**\n\n"
        f"👥 Users: `{len(users)}` | ✅ Active: `{active}`\n"
        f"🎬 Movies: `{len(data)}` | 📁 Files: `{len(files)}`\n"
        f"📥 DL: `{sum(d.get('downloads',0) for d in data)}`\n\n"
        f"⚙️ Short: {'✅' if s.get('short') else '❌'} | "
        f"Token: {'✅' if s.get('movie_token') else '❌'} | "
        f"FJ: {'✅' if s.get('force_join') else '❌'}\n"
        f"🌙 Maint: {'✅' if s.get('maintenance') else '❌'} | "
        f"Del: {'✅' if s.get('auto_delete') else '❌'} ({s.get('delete_timer',180)}min)"
    )

@app.on_message(filters.command("addadmin") & filters.user(ADMIN_ID))
async def addadmin_cmd(_, m: Message):
    if len(m.command) < 3: return await safe_reply(m,
        "Usage: `/addadmin <uid> <level>`\n\n1=Search+Fetch\n2=+Ban/Genkey\n3=+Broadcast\n4=Creator")
    try: uid = m.command[1]; level = int(m.command[2])
    except: return await safe_reply(m, "❌ Invalid")
    add_admin(uid, level)
    if level == 4: register_creator(uid, "Creator")
    await safe_reply(m, f"✅ `{uid}` → {LEVEL_LABELS.get(level,'?')}")

@app.on_message(filters.command("removeadmin") & filters.user(ADMIN_ID))
async def removeadmin_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/removeadmin <uid>`")
    if remove_admin(m.command[1]): await safe_reply(m, f"✅ Removed `{m.command[1]}`")
    else: await safe_reply(m, "❌ Not found")

@app.on_message(filters.command("badword") & filters.user(ADMIN_ID))
async def badword_cmd(_, m: Message):
    if m.reply_to_message:
        word = m.reply_to_message.text.strip().lower()
    elif len(m.command) >= 2:
        word = m.command[1].lower()
    else:
        return await safe_reply(m, "Reply to message or `/badword <word>`")
    if add_bad_word(word): await safe_reply(m, f"✅ `{word}` added!")
    else: await safe_reply(m, f"⚠️ Already exists!")

@app.on_message(filters.command("removebadword") & filters.user(ADMIN_ID))
async def removebadword_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/removebadword <word>`")
    if remove_bad_word(m.command[1].lower()): await safe_reply(m, f"✅ Removed!")
    else: await safe_reply(m, "❌ Not found!")

@app.on_message(filters.command("setwelcome") & filters.user(ADMIN_ID))
async def setwelcome_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/setwelcome <message>`")
    msg = m.text.split(None, 1)[1]
    update_setting("welcome_msg", msg); await safe_reply(m, f"✅ Welcome message updated!")

@app.on_message(filters.command("setchannel") & filters.user(ADMIN_ID))
async def setchannel_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/setchannel @channel`")
    update_setting("force_channel", m.command[1]); await safe_reply(m, f"✅ Channel: `{m.command[1]}`")

@app.on_message(filters.command("setupi") & filters.user(ADMIN_ID))
async def setupi_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/setupi yourname@upi`")
    update_setting("upi_id", m.command[1]); await safe_reply(m, f"✅ UPI: `{m.command[1]}`")

@app.on_message(filters.command("deleteentry") & filters.user(ADMIN_ID))
async def delete_entry(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/deleteentry <server_id>`")
    try: sid = int(m.command[1])
    except: return await safe_reply(m, "❌ Invalid")
    data = load_json(JSON_PATH, [])
    new = [d for d in data if int(d.get("server",-1)) != sid]
    if len(new) == len(data): return await safe_reply(m, "❌ Not found.")
    save_json(JSON_PATH, new); await safe_reply(m, f"✅ Deleted `{sid}`")

@app.on_message(filters.command("searchlog") & filters.user(ADMIN_ID))
async def searchlog_cmd(_, m: Message):
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/searchlog <uid>`")
    history = get_search_history(m.command[1])
    if not history: return await safe_reply(m, "📭 No history.")
    text = f"🕐 **History `{m.command[1]}`:**\n\n"
    for i, h in enumerate(history[:20], 1): text += f"{i}. `{h['query']}` — {h['time']}\n"
    await safe_reply(m, text)

# ══════════════════════════════════════════
#   BUY / PAYMENT + QR
# ══════════════════════════════════════════
@app.on_message(filters.command("buy"))
async def buy_cmd(_, m: Message):
    if str(m.from_user.id) in load_json(BANNED_PATH, []): return
    buttons = [[InlineKeyboardButton(plan["label"], callback_data=f"buyplan:{k}")] for k, plan in PLANS.items()]
    await safe_reply(m, "💰 **Premium Plans:**", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^buyplan:"))
async def buyplan_cb(_, q: CallbackQuery):
    import secrets as sec
    plan_id = q.data.split(":")[1]
    plan = PLANS.get(plan_id)
    if not plan: return await q.answer("Invalid", show_alert=True)
    pay_id = sec.token_hex(4).upper()
    payments = load_json(PAYMENTS_PATH, {})
    s = get_settings()
    upi = s.get("upi_id", UPI_ID)
    payments[pay_id] = {"uid": str(q.from_user.id), "plan_id": plan_id, "days": plan["days"],
                        "price": plan["price"], "status": "pending", "created_at": datetime.now().isoformat()}
    save_json(PAYMENTS_PATH, payments)

    # Generate QR
    qr_url = generate_upi_qr(plan["price"], upi, UPI_NAME)

    await q.message.edit_text(
        f"💳 **Payment Details**\n\n"
        f"📦 {plan['label']}\n💰 **₹{plan['price']}**\n\n"
        f"🏦 UPI: `{upi}`\n📌 Pay ID: `{pay_id}`\n\n"
        f"Scan QR ya UPI ID pe pay karo → Screenshot bhejo!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📷 View QR Code", url=qr_url)],
            [InlineKeyboardButton("📸 Payment Sent", callback_data=f"paysent:{pay_id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")]
        ])
    )

@app.on_callback_query(filters.regex(r"^paysent:"))
async def paysent_cb(_, q: CallbackQuery):
    pay_id = q.data.split(":")[1]
    payments = load_json(PAYMENTS_PATH, {})
    if pay_id not in payments: return await q.answer("Not found", show_alert=True)
    plan = PLANS.get(payments[pay_id]["plan_id"], {})
    await q.message.edit_text(f"✅ Sent! Admin verify karega.\n📌 Pay ID: `{pay_id}`")
    try:
        await app.send_message(ADMIN_ID,
            f"💰 **New Payment!**\n👤 `{payments[pay_id]['uid']}`\n📌 `{pay_id}`\n{plan.get('label','')}\n₹{payments[pay_id]['price']}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Approve", callback_data=f"paydone:{pay_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"payreject:{pay_id}")
            ]])
        )
    except: pass

@app.on_callback_query(filters.regex(r"^paydone:"))
async def paydone_cb(_, q: CallbackQuery):
    if q.from_user.id != ADMIN_ID: return await q.answer("Admin only!", show_alert=True)
    pay_id = q.data.split(":")[1]
    payments = load_json(PAYMENTS_PATH, {})
    if pay_id not in payments: return
    info = payments[pay_id]; uid = int(info["uid"]); days = info["days"]
    keys = create_keys(1, days); key = keys[0]; use_key(key, uid)
    payments[pay_id]["status"] = "approved"; save_json(PAYMENTS_PATH, payments)
    await q.message.edit_text(f"✅ Approved `{pay_id}`!")
    try: await app.send_message(uid, f"🎉 Payment Approved!\n🔑 `{key}`\n📦 {days} days")
    except: pass

@app.on_callback_query(filters.regex(r"^payreject:"))
async def payreject_cb(_, q: CallbackQuery):
    if q.from_user.id != ADMIN_ID: return await q.answer("Admin only!", show_alert=True)
    pay_id = q.data.split(":")[1]
    payments = load_json(PAYMENTS_PATH, {})
    if pay_id not in payments: return
    uid = int(payments[pay_id]["uid"])
    payments[pay_id]["status"] = "rejected"; save_json(PAYMENTS_PATH, payments)
    await q.message.edit_text(f"❌ Rejected `{pay_id}`")
    try: await app.send_message(uid, f"❌ Payment `{pay_id}` rejected.")
    except: pass

@app.on_callback_query(filters.regex(r"^show_plans$"))
async def show_plans_cb(_, q: CallbackQuery):
    buttons = [[InlineKeyboardButton(plan["label"], callback_data=f"buyplan:{k}")] for k, plan in PLANS.items()]
    await q.message.edit_text("💰 **Plans:**", reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^cancel_buy$"))
async def cancel_buy_cb(_, q: CallbackQuery):
    try: await q.message.delete()
    except: pass

# ══════════════════════════════════════════
#   BROADCAST
# ══════════════════════════════════════════
_pending_broadcasts = {}

@app.on_message(filters.command("broadcast"))
async def broadcast_prep(_, m: Message):
    if not has_permission(m.from_user.id, "broadcast"): return await safe_reply(m, "❌ Permission denied.")
    if len(m.command) < 2: return await safe_reply(m, "Usage: `/broadcast <msg>`")
    text = m.text.split(None, 1)[1]
    _pending_broadcasts[str(m.from_user.id)] = {"text": text}
    users = load_json(USERS_PATH, [])
    await safe_reply(m, f"📢 **Preview:**\n\n{text}\n\n👥 {len(users)} users",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Confirm", callback_data=f"bcast_confirm:{m.from_user.id}")],
            [InlineKeyboardButton("❌ Cancel", callback_data=f"bcast_cancel:{m.from_user.id}")]
        ]))

@app.on_callback_query(filters.regex(r"^bcast_confirm:"))
async def bcast_confirm(_, q: CallbackQuery):
    uid_str = q.data.split(":",1)[1]
    if str(q.from_user.id) != uid_str: return await q.answer("No permission", show_alert=True)
    data = _pending_broadcasts.get(uid_str)
    if not data: return await q.answer("Data lost", show_alert=True)
    text = data["text"]; users = load_json(USERS_PATH, []); banned = load_json(BANNED_PATH, [])
    await q.message.edit_text("⏳ Broadcasting...")
    sent = fail = 0
    for u in users:
        if str(u) in banned: continue
        try: await app.send_message(int(u), text); sent += 1
        except FloodWait as e: await asyncio.sleep(e.value)
        except: fail += 1
        if sent % 20 == 0: await asyncio.sleep(1)
    await q.message.edit_text(f"✅ Done!\n📤 Sent: {sent}\n🚫 Failed: {fail}")
    _pending_broadcasts.pop(uid_str, None)

@app.on_callback_query(filters.regex(r"^bcast_cancel:"))
async def bcast_cancel(_, q: CallbackQuery):
    uid_str = q.data.split(":",1)[1]
    if str(q.from_user.id) != uid_str: return await q.answer("No permission", show_alert=True)
    _pending_broadcasts.pop(uid_str, None); await q.message.edit_text("❌ Cancelled.")

@app.on_message(filters.command("code"))
async def code_cmd(_, m: Message):
    if not is_user_active(m.from_user.id): return await send_activation_prompt(m)
    parts = m.text.strip().split()
    if len(parts) != 3: return await safe_reply(m, "❌ `/code <start> <end>`")
    s_id, e_id = int(parts[1]), int(parts[2])
    data = load_json(JSON_PATH, [])
    matching = [d for d in data if s_id <= int(d.get("server",-1)) <= e_id]
    if not matching: return await safe_reply(m, "⚠️ No data.")
    await safe_reply(m, f"📡 {len(matching)} entries...")
    for entry in matching:
        msg = f"🎬 **{entry.get('title')}**\n📦 `{entry.get('size')}`\n\n"
        for l in entry.get("links",[]): msg += f"`{get_short_link(SITE_PREFIX+l)}`\n"
        for chunk in chunk_text(msg): await m.reply_text(chunk, disable_web_page_preview=True); await asyncio.sleep(0.4)

# ══════════════════════════════════════════
#   /cmd
# ══════════════════════════════════════════
@app.on_message(filters.command("cmd"))
async def cmd_list(_, m: Message):
    uid = m.from_user.id; level = get_admin_level(uid)
    text = ("👤 **User Commands:**\n"
            "/start /activate /buy /myplan /me\n"
            "/mystars /myhistory /mystats\n"
            "/trending /random /searchall\n"
            "/report /note /notes /help /cmd\n")
    if level >= 1: text += "\n⭐ **Lv1+:** /fetch /code\n"
    if level >= 2: text += "⭐⭐ **Lv2+:** /genkey /keys /ban /unban\n/actuser /adddays /revoke /actlist\n/warn /warnings /clearwarn /mute /unmute\n/purge /pin /reports\n"
    if level >= 3: text += "⭐⭐⭐ **Lv3+:** /broadcast\n"
    if level == 4: text += "🎬 **Creator:** Upload files, /myfiles\n/myearnings /setshortener /deletefile\n"
    if level == 99: text += "\n👑 **Admin:** /settings /addadmin /removeadmin\n/addcreator /badword /removebadword\n/badwords /badlogs /setwelcome\n/setchannel /setupi /deleteentry\n/status /payments /searchlog\n/save /delnote /settimer /setwarn\n"
    await safe_reply(m, text)

# ══════════════════════════════════════════
#   WEB PANEL
# ══════════════════════════════════════════
def start_web_panel():
    try:
        from web_panel_v16 import create_app
        panel = create_app()
        panel.run(host="0.0.0.0", port=WEB_PANEL_PORT, debug=False, use_reloader=False)
    except Exception as e:
        logger.error("Web panel error: %s", e)

# ══════════════════════════════════════════
#   RUN
# ══════════════════════════════════════════
if __name__ == "__main__":
    init_files()
    logger.info("🌐 Web Panel starting on port %s...", WEB_PANEL_PORT)
    threading.Thread(target=start_web_panel, daemon=True).start()
    logger.info("🤖 Filmyzilla Bot V16 Starting...")
    try: app.run()
    except Exception as e: logger.exception("Startup failed: %s", e)
