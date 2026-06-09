# ═══════════════════════════════════════════
#   scheduler.py — V16
#   Daily Report + Expiry Warnings
# ═══════════════════════════════════════════
import asyncio, time, logging
from datetime import datetime
from helpers import load_json, save_json
from config import *

logger = logging.getLogger(__name__)

async def send_expiry_warnings(bot):
    activ = load_json(ACTIVATIONS_PATH, {})
    now = int(time.time())
    tomorrow = now + 86400
    for uid, info in activ.items():
        exp_ts = int(info.get("expires_at_ts", 0))
        if now < exp_ts < tomorrow:
            if now - info.get("warned_at", 0) > 86000:
                try:
                    exp_str = datetime.fromtimestamp(exp_ts).strftime("%d %b %Y, %I:%M %p")
                    await bot.send_message(int(uid),
                        f"⚠️ **Expiry Warning!**\n\n"
                        f"Plan kal expire hoga!\n"
                        f"📅 Expires: **{exp_str}**\n\n"
                        f"Renew karo: /buy"
                    )
                    activ[uid]["warned_at"] = now
                    save_json(ACTIVATIONS_PATH, activ)
                except: pass
                await asyncio.sleep(0.3)

async def send_daily_report(bot):
    data     = load_json(JSON_PATH, [])
    users    = load_json(USERS_PATH, [])
    activ    = load_json(ACTIVATIONS_PATH, {})
    keys_db  = load_json(KEYS_PATH, {})
    payments = load_json(PAYMENTS_PATH, {})
    files    = load_json(FILES_DB_PATH, {})
    now      = int(time.time())

    active_count = sum(1 for v in activ.values() if int(v.get("expires_at_ts",0)) > now)
    unused_keys  = sum(1 for v in keys_db.values() if not v.get("used"))
    pending_pay  = sum(1 for v in payments.values() if v.get("status") == "pending")
    total_dl     = sum(d.get("downloads",0) for d in data)
    total_file_dl = sum(f.get("downloads",0) for f in files.values())
    top = sorted(data, key=lambda x: x.get("downloads",0), reverse=True)
    top_movie = top[0]["title"][:30] if top else "N/A"

    try:
        await bot.send_message(ADMIN_ID,
            f"📊 **Daily Report — {datetime.now().strftime('%d %b %Y')}**\n\n"
            f"👥 Total Users: `{len(users)}`\n"
            f"✅ Active Now: `{active_count}`\n"
            f"📥 Movie DL: `{total_dl}`\n"
            f"📁 File DL: `{total_file_dl}`\n"
            f"🔑 Unused Keys: `{unused_keys}`\n"
            f"💰 Pending Pay: `{pending_pay}`\n"
            f"🎬 Movies: `{len(data)}` | 📁 Files: `{len(files)}`\n\n"
            f"🏆 Top: _{top_movie}_\n"
            f"_Auto report — {datetime.now().strftime('%I:%M %p')}_"
        )
        logger.info("Daily report sent")
    except Exception as e:
        logger.error("Daily report failed: %s", e)

async def scheduler_loop(bot):
    logger.info("⏰ Scheduler started")
    last_daily = 0
    while True:
        try:
            now = datetime.now()
            if now.hour == 0 and now.minute < 2:
                today_ts = int(datetime.now().replace(hour=0,minute=0,second=0).timestamp())
                if last_daily < today_ts:
                    await send_daily_report(bot)
                    last_daily = today_ts
            await send_expiry_warnings(bot)
        except Exception as e:
            logger.exception("Scheduler error: %s", e)
        await asyncio.sleep(3600)
