"""
Filmyzilla Bot — Web Panel V16
Command Terminal + All Features
"""
import json, os, time, secrets, random, string, io, csv
from datetime import datetime, timedelta
from functools import wraps
from flask import (Flask, render_template_string, request,
                   redirect, session, jsonify, Response)

from helpers import (load_json, save_json, create_keys,
                     activate_user, deactivate_user, extend_user, get_settings, update_setting)
from admin_system import (add_admin, remove_admin, get_all_admins,
                          add_bad_word, remove_bad_word, get_bad_words, get_bad_word_logs,
                          add_warning, clear_warnings, mute_user, unmute_user,
                          save_note, get_note, delete_note, get_all_notes, get_reports)
from creator import (get_all_creators, get_creator_earnings,
                     get_all_files, delete_file, get_creator_files)
from referral import get_all_referrals, get_referral_days
from ads import get_all_ads, add_ad, remove_ad, toggle_ad
from config import *

# ════════════════════════════════
#   BASE HTML
# ════════════════════════════════
BASE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>🎬 Bot Panel V16</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0a14;color:#e0e0e0}
.sidebar{width:220px;background:#12122a;height:100vh;position:fixed;top:0;left:0;overflow-y:auto;padding:0 0 40px}
.logo{padding:18px;background:#1a1a3e;text-align:center;color:#a78bfa;font-size:16px;font-weight:bold;border-bottom:1px solid #2d2d5e}
.sidebar a{display:flex;align-items:center;gap:8px;padding:10px 16px;color:#9ca3af;text-decoration:none;font-size:13px;transition:.2s}
.sidebar a:hover,.sidebar a.on{background:#1e1e40;color:#a78bfa;border-left:3px solid #7c3aed}
.st{padding:10px 16px 3px;color:#374151;font-size:10px;text-transform:uppercase;letter-spacing:1px;margin-top:6px}
.main{margin-left:220px;min-height:100vh}
.topbar{background:#12122a;padding:12px 22px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #2d2d5e;position:sticky;top:0;z-index:99}
.topbar h1{color:#a78bfa;font-size:15px}
.topbar a{color:#f87171;text-decoration:none;font-size:12px}
.content{padding:22px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:12px;margin-bottom:22px}
.card{background:#12122a;border-radius:10px;padding:16px 12px;text-align:center;border:1px solid #2d2d5e;cursor:pointer;transition:.2s;text-decoration:none;display:block}
.card:hover{border-color:#7c3aed;transform:translateY(-2px)}
.card .n{font-size:28px;font-weight:bold}.card .l{font-size:11px;color:#6b7280;margin-top:3px}
.blue .n{color:#60a5fa}.green .n{color:#34d399}.red .n{color:#f87171}.yellow .n{color:#fbbf24}.purple .n{color:#a78bfa}.pink .n{color:#f472b6}.orange .n{color:#fb923c}
.box{background:#12122a;border-radius:10px;padding:18px;margin-bottom:16px;border:1px solid #2d2d5e}
.box h3{color:#a78bfa;margin-bottom:12px;font-size:13px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{background:#0f0f28;color:#a78bfa;padding:8px 10px;text-align:left}
td{padding:8px 10px;border-bottom:1px solid #1e1e3a;color:#d1d5db}
tr:hover td{background:#161630}
.badge{padding:2px 7px;border-radius:20px;font-size:10px;font-weight:700}
.bg{background:#064e3b;color:#34d399}.br{background:#450a0a;color:#f87171}.by{background:#451a03;color:#fbbf24}.bp{background:#2e1065;color:#a78bfa}
input,select,textarea{background:#0f0f28;border:1px solid #2d2d5e;color:#e0e0e0;padding:8px 11px;border-radius:7px;width:100%;margin-bottom:9px;font-size:13px;outline:none}
input:focus,select:focus,textarea:focus{border-color:#7c3aed}
button,.btn{background:#7c3aed;color:#fff;border:none;padding:8px 16px;border-radius:7px;cursor:pointer;font-size:13px;text-decoration:none;display:inline-block;transition:.2s}
button:hover,.btn:hover{background:#6d28d9}
.btn-r{background:#dc2626}.btn-r:hover{background:#b91c1c}
.btn-g{background:#059669}.btn-g:hover{background:#047857}
.btn-y{background:#d97706}.btn-y:hover{background:#b45309}
.alert{padding:10px 14px;border-radius:7px;margin-bottom:14px;font-size:13px}
.alert.s{background:#064e3b;color:#34d399;border:1px solid #065f46}
.alert.e{background:#450a0a;color:#f87171;border:1px solid #7f1d1d}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:9px}
.g3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:9px}
.tag{background:#1e1e3a;color:#a78bfa;padding:2px 6px;border-radius:4px;font-size:11px;font-family:monospace}
.toggle{display:flex;align-items:center;gap:9px;margin-bottom:10px;cursor:pointer;padding:9px;background:#0f0f28;border-radius:7px;border:1px solid #2d2d5e}
.toggle input{width:auto;margin:0}
.login-wrap{display:flex;align-items:center;justify-content:center;min-height:100vh}
.login-box{background:#12122a;padding:38px;border-radius:14px;border:1px solid #2d2d5e;width:340px}
.login-box h2{color:#a78bfa;text-align:center;margin-bottom:22px}
/* Terminal */
.terminal{background:#0a0a0a;border-radius:10px;border:1px solid #2d2d5e;overflow:hidden}
.terminal-header{background:#1a1a2e;padding:10px 16px;font-size:12px;color:#6b7280;display:flex;gap:8px;align-items:center}
.term-dot{width:10px;height:10px;border-radius:50%}
.term-output{height:380px;overflow-y:auto;padding:14px;font-family:monospace;font-size:13px;line-height:1.6}
.term-output .line{margin:2px 0}
.term-output .cmd{color:#a78bfa}.term-output .ok{color:#34d399}.term-output .err{color:#f87171}.term-output .info{color:#60a5fa}
.term-input-wrap{display:flex;align-items:center;padding:10px 14px;background:#111;border-top:1px solid #2d2d5e;gap:8px}
.term-input-wrap span{color:#a78bfa;font-family:monospace;font-size:13px}
.term-input{background:transparent;border:none;color:#e0e0e0;font-family:monospace;font-size:13px;flex:1;outline:none;margin:0;padding:0}
</style>
</head>
<body>
{% if logged_in %}
<div class="sidebar">
  <div class="logo">🎬 Bot Panel V16</div>
  <div class="st">Main</div>
  <a href="/dashboard" class="{{ 'on' if p=='dash' }}">📊 Dashboard</a>
  <a href="/terminal" class="{{ 'on' if p=='term' }}">💻 Command Terminal</a>
  <div class="st">Users</div>
  <a href="/users" class="{{ 'on' if p=='users' }}">👥 All Users</a>
  <a href="/actlist" class="{{ 'on' if p=='actlist' }}">✅ Active Users</a>
  <a href="/banned" class="{{ 'on' if p=='banned' }}">🚫 Banned</a>
  <a href="/warnings_page" class="{{ 'on' if p=='warn' }}">⚠️ Warnings</a>
  <div class="st">Content</div>
  <a href="/movies" class="{{ 'on' if p=='movies' }}">🎬 Movies</a>
  <a href="/files_page" class="{{ 'on' if p=='files' }}">📁 Creator Files</a>
  <a href="/creators" class="{{ 'on' if p=='creators' }}">🎬 Creators</a>
  <a href="/trending" class="{{ 'on' if p=='trend' }}">🔥 Trending</a>
  <div class="st">Keys & Pay</div>
  <a href="/keys" class="{{ 'on' if p=='keys' }}">🔑 Keys</a>
  <a href="/payments" class="{{ 'on' if p=='pay' }}">💰 Payments</a>
  <div class="st">Tools</div>
  <a href="/broadcast" class="{{ 'on' if p=='bcast' }}">📢 Broadcast</a>
  <a href="/admins" class="{{ 'on' if p=='admins' }}">👮 Acting Admins</a>
  <a href="/badwords" class="{{ 'on' if p=='bw' }}">🚫 Bad Words</a>
  <a href="/ads" class="{{ 'on' if p=='ads' }}">📣 Ads</a>
  <a href="/referrals" class="{{ 'on' if p=='ref' }}">🎁 Referrals</a>
  <a href="/notes" class="{{ 'on' if p=='notes' }}">📌 Notes</a>
  <a href="/reports" class="{{ 'on' if p=='reports' }}">🚨 Reports</a>
  <a href="/history" class="{{ 'on' if p=='hist' }}">🕐 Search History</a>
  <div class="st">Config</div>
  <a href="/settings" class="{{ 'on' if p=='set' }}">⚙️ Settings</a>
  <a href="/export" class="{{ 'on' if p=='exp' }}">📤 Export CSV</a>
  <a href="/logout" style="color:#f87171;margin-top:10px">🚪 Logout</a>
</div>
<div class="main">
  <div class="topbar"><h1>{{ title }}</h1><a href="/logout">Logout</a></div>
  <div class="content">
    {% if msg %}<div class="alert {{ 'e' if err else 's' }}">{{ msg }}</div>{% endif %}
    {{ content }}
  </div>
</div>
{% else %}{{ content }}{% endif %}
</body></html>"""

def render(title, content, p="", msg="", err=False):
    return render_template_string(BASE, title=title, content=content, p=p,
        msg=msg, err=err, logged_in="admin" in session)

def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "admin" not in session: return redirect("/login")
        return f(*a, **kw)
    return dec

def create_app():
    app = Flask(__name__)
    app.secret_key = "v16_panel_secret_2024"

    # ── Login ──
    @app.route("/login", methods=["GET","POST"])
    def login():
        err = ""
        if request.method == "POST":
            if request.form.get("password") == WEB_PANEL_PASSWORD:
                session["admin"] = True; return redirect("/dashboard")
            err = "❌ Wrong password!"
        c = f"""<div class="login-wrap"><div class="login-box">
        <h2>🔐 Bot Panel V16</h2>
        {'<div class="alert e">'+err+'</div>' if err else ''}
        <form method="POST">
          <input type="password" name="password" placeholder="Password" autofocus required>
          <button style="width:100%;margin-top:5px">Login</button>
        </form></div></div>"""
        return render("Login", c)

    @app.route("/logout")
    def logout(): session.clear(); return redirect("/login")

    @app.route("/")
    @login_required
    def index(): return redirect("/dashboard")

    # ── Dashboard ──
    @app.route("/dashboard")
    @login_required
    def dashboard():
        data = load_json(JSON_PATH, [])
        users = load_json(USERS_PATH, [])
        banned = load_json(BANNED_PATH, [])
        activ = load_json(ACTIVATIONS_PATH, {})
        keys_db = load_json(KEYS_PATH, {})
        payments = load_json(PAYMENTS_PATH, {})
        files = load_json(FILES_DB_PATH, {})
        creators = load_json(CREATORS_PATH, {})
        now = int(time.time())
        active = sum(1 for v in activ.values() if int(v.get("expires_at_ts",0)) > now)
        unused = sum(1 for v in keys_db.values() if not v.get("used"))
        pending = sum(1 for v in payments.values() if v.get("status")=="pending")
        total_dl = sum(d.get("downloads",0) for d in data)
        file_dl = sum(f.get("downloads",0) for f in files.values())
        top5 = sorted(data, key=lambda x: x.get("downloads",0), reverse=True)[:5]
        rows = "".join([f"<tr><td>{i+1}</td><td>{m['title'][:40]}</td><td>📥 {m.get('downloads',0)}</td></tr>" for i,m in enumerate(top5)])
        c = f"""
        <div class="cards">
          <a href="/users" class="card blue"><div class="n">{len(users)}</div><div class="l">Total Users</div></a>
          <a href="/actlist" class="card green"><div class="n">{active}</div><div class="l">Active Now</div></a>
          <a href="/banned" class="card red"><div class="n">{len(banned)}</div><div class="l">Banned</div></a>
          <a href="/movies" class="card purple"><div class="n">{len(data)}</div><div class="l">Movies</div></a>
          <a href="/files_page" class="card orange"><div class="n">{len(files)}</div><div class="l">Files</div></a>
          <a href="/creators" class="card pink"><div class="n">{len(creators)}</div><div class="l">Creators</div></a>
          <a href="/trending" class="card yellow"><div class="n">{total_dl}</div><div class="l">Movie DL</div></a>
          <a href="/files_page" class="card yellow"><div class="n">{file_dl}</div><div class="l">File DL</div></a>
          <a href="/keys" class="card pink"><div class="n">{unused}</div><div class="l">Unused Keys</div></a>
          <a href="/payments" class="card yellow"><div class="n">{pending}</div><div class="l">Pending Pay</div></a>
        </div>
        <div class="box"><h3>🔥 Top 5 Trending</h3>
        <table><tr><th>#</th><th>Title</th><th>Downloads</th></tr>{rows}</table></div>"""
        return render("Dashboard", c, p="dash")

    # ── Command Terminal ──
    @app.route("/terminal")
    @login_required
    def terminal():
        c = """
        <div class="box">
          <h3>💻 Bot Command Terminal</h3>
          <p style="color:#6b7280;font-size:12px;margin-bottom:14px">
            Type bot commands — same as Telegram. Results show here instantly.
          </p>
          <div class="terminal">
            <div class="terminal-header">
              <div class="term-dot" style="background:#f87171"></div>
              <div class="term-dot" style="background:#fbbf24"></div>
              <div class="term-dot" style="background:#34d399"></div>
              <span style="margin-left:8px">Bot Terminal — V16</span>
            </div>
            <div class="term-output" id="output">
              <div class="line info">Welcome to Bot Panel V16 Terminal</div>
              <div class="line info">Type commands below. Example: /genkey 5 30</div>
              <div class="line" style="color:#374151">─────────────────────────────</div>
            </div>
            <div class="term-input-wrap">
              <span>admin@bot:~$</span>
              <input class="term-input" id="cmd-input" placeholder="Type command..." autocomplete="off">
              <button onclick="runCmd()" style="padding:6px 14px">▶ Run</button>
            </div>
          </div>
          <div style="margin-top:12px;color:#6b7280;font-size:12px">
            <strong style="color:#a78bfa">Quick Commands:</strong>
            <span onclick="setCmd('/status')" style="cursor:pointer;margin:0 6px" class="tag">/status</span>
            <span onclick="setCmd('/genkey 5 30')" style="cursor:pointer;margin:0 6px" class="tag">/genkey 5 30</span>
            <span onclick="setCmd('/actlist')" style="cursor:pointer;margin:0 6px" class="tag">/actlist</span>
            <span onclick="setCmd('/keys')" style="cursor:pointer;margin:0 6px" class="tag">/keys</span>
            <span onclick="setCmd('/badwords')" style="cursor:pointer;margin:0 6px" class="tag">/badwords</span>
            <span onclick="setCmd('/broadcast Hello!')" style="cursor:pointer;margin:0 6px" class="tag">/broadcast</span>
          </div>
        </div>
        <script>
        function setCmd(cmd) {
          document.getElementById('cmd-input').value = cmd;
          document.getElementById('cmd-input').focus();
        }
        document.getElementById('cmd-input').addEventListener('keydown', function(e) {
          if (e.key === 'Enter') runCmd();
        });
        function addLine(text, cls='') {
          const out = document.getElementById('output');
          const div = document.createElement('div');
          div.className = 'line ' + cls;
          div.textContent = text;
          out.appendChild(div);
          out.scrollTop = out.scrollHeight;
        }
        async function runCmd() {
          const input = document.getElementById('cmd-input');
          const cmd = input.value.trim();
          if (!cmd) return;
          addLine('$ ' + cmd, 'cmd');
          input.value = '';
          try {
            const res = await fetch('/api/terminal', {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({cmd: cmd})
            });
            const data = await res.json();
            const lines = data.output.split('\\n');
            lines.forEach(l => addLine(l, data.ok ? 'ok' : 'err'));
          } catch(e) {
            addLine('❌ Error: ' + e, 'err');
          }
        }
        </script>"""
        return render("Command Terminal", c, p="term")

    # ── Terminal API ──
    @app.route("/api/terminal", methods=["POST"])
    @login_required
    def terminal_api():
        data = request.get_json()
        cmd = (data.get("cmd","") or "").strip()
        if not cmd: return jsonify({"ok": False, "output": "❌ Empty command"})

        parts = cmd.split()
        command = parts[0].lower().lstrip("/")
        args = parts[1:]

        try:
            # ── Status ──
            if command == "status":
                movies = load_json(JSON_PATH, [])
                users = load_json(USERS_PATH, [])
                activ = load_json(ACTIVATIONS_PATH, {})
                keys_db = load_json(KEYS_PATH, {})
                now = int(time.time())
                active = sum(1 for v in activ.values() if int(v.get("expires_at_ts",0)) > now)
                unused = sum(1 for v in keys_db.values() if not v.get("used"))
                out = (f"📊 Bot Stats V16\n"
                       f"👥 Users: {len(users)} | ✅ Active: {active}\n"
                       f"🎬 Movies: {len(movies)}\n"
                       f"🔑 Unused Keys: {unused}")
                return jsonify({"ok": True, "output": out})

            # ── Genkey ──
            elif command == "genkey":
                count = int(args[0]) if args else 1
                days  = int(args[1]) if len(args) > 1 else 30
                from helpers import create_keys
                keys = create_keys(count, days)
                out = f"✅ {count} Key(s) — {days} Day Plan:\n" + "\n".join(keys)
                return jsonify({"ok": True, "output": out})

            # ── Keys ──
            elif command == "keys":
                keys_db = load_json(KEYS_PATH, {})
                unused = {k: v for k, v in keys_db.items() if not v.get("used")}
                out = f"🔑 Unused Keys ({len(unused)}):\n" + "\n".join([f"{k} — {v['days']}d" for k,v in list(unused.items())[:20]])
                return jsonify({"ok": True, "output": out or "No unused keys"})

            # ── Ban ──
            elif command == "ban":
                uid = args[0] if args else None
                if not uid: return jsonify({"ok": False, "output": "❌ Provide UID"})
                banned = load_json(BANNED_PATH, [])
                if uid not in banned: banned.append(uid); save_json(BANNED_PATH, banned)
                return jsonify({"ok": True, "output": f"✅ Banned {uid}"})

            # ── Unban ──
            elif command == "unban":
                uid = args[0] if args else None
                if not uid: return jsonify({"ok": False, "output": "❌ Provide UID"})
                banned = load_json(BANNED_PATH, [])
                if uid in banned: banned.remove(uid); save_json(BANNED_PATH, banned)
                return jsonify({"ok": True, "output": f"✅ Unbanned {uid}"})

            # ── Actuser ──
            elif command == "actuser":
                if len(args) < 2: return jsonify({"ok": False, "output": "❌ /actuser <uid> <hours>"})
                activate_user(int(args[0]), int(args[1]), method="panel")
                exp = (datetime.now() + timedelta(hours=int(args[1]))).strftime("%d %b %Y")
                return jsonify({"ok": True, "output": f"✅ {args[0]} activated {args[1]}h → {exp}"})

            # ── Adddays ──
            elif command == "adddays":
                if len(args) < 2: return jsonify({"ok": False, "output": "❌ /adddays <uid> <days>"})
                new_exp = extend_user(int(args[0]), int(args[1]))
                return jsonify({"ok": True, "output": f"✅ +{args[1]} days to {args[0]} → {new_exp}"})

            # ── Revoke ──
            elif command == "revoke":
                if not args: return jsonify({"ok": False, "output": "❌ Provide UID"})
                deactivate_user(int(args[0]))
                return jsonify({"ok": True, "output": f"✅ Revoked {args[0]}"})

            # ── Actlist ──
            elif command == "actlist":
                activ = load_json(ACTIVATIONS_PATH, {})
                now = int(time.time())
                active = {k: v for k, v in activ.items() if int(v.get("expires_at_ts",0)) > now}
                out = f"✅ Active Users ({len(active)}):\n"
                for uid, info in list(active.items())[:15]:
                    exp = datetime.fromtimestamp(int(info["expires_at_ts"])).strftime("%d %b %Y")
                    out += f"  {uid} → {exp}\n"
                return jsonify({"ok": True, "output": out or "No active users"})

            # ── Badwords ──
            elif command == "badwords":
                words = load_json(BAD_WORDS_PATH, [])
                out = f"🚫 Bad Words ({len(words)}):\n" + ", ".join(words)
                return jsonify({"ok": True, "output": out or "No bad words"})

            # ── Badword add ──
            elif command == "badword":
                if not args: return jsonify({"ok": False, "output": "❌ Provide word"})
                add_bad_word(args[0])
                return jsonify({"ok": True, "output": f"✅ Added: {args[0]}"})

            # ── Removebadword ──
            elif command == "removebadword":
                if not args: return jsonify({"ok": False, "output": "❌ Provide word"})
                from admin_system import remove_bad_word
                if remove_bad_word(args[0]): return jsonify({"ok": True, "output": f"✅ Removed: {args[0]}"})
                return jsonify({"ok": False, "output": "❌ Not found"})

            # ── Warn ──
            elif command == "warn":
                if not args: return jsonify({"ok": False, "output": "❌ /warn <uid> [reason]"})
                reason = " ".join(args[1:]) if len(args) > 1 else "Panel warn"
                count = add_warning(args[0], reason)
                return jsonify({"ok": True, "output": f"⚠️ Warning {count} given to {args[0]}"})

            # ── Clearwarn ──
            elif command == "clearwarn":
                if not args: return jsonify({"ok": False, "output": "❌ Provide UID"})
                clear_warnings(args[0])
                return jsonify({"ok": True, "output": f"✅ Warnings cleared for {args[0]}"})

            # ── Mute ──
            elif command == "mute":
                if not args: return jsonify({"ok": False, "output": "❌ /mute <uid> [minutes]"})
                mins = int(args[1]) if len(args) > 1 else 60
                mute_user(args[0], mins)
                return jsonify({"ok": True, "output": f"🔇 {args[0]} muted {mins}min"})

            # ── Unmute ──
            elif command == "unmute":
                if not args: return jsonify({"ok": False, "output": "❌ Provide UID"})
                unmute_user(args[0])
                return jsonify({"ok": True, "output": f"🔊 {args[0]} unmuted"})

            # ── Broadcast ──
            elif command == "broadcast":
                if not args: return jsonify({"ok": False, "output": "❌ Provide message"})
                msg = " ".join(args)
                queue = load_json("broadcast_queue.json", [])
                queue.append({"text": msg, "queued_at": datetime.now().isoformat()})
                save_json("broadcast_queue.json", queue)
                users = load_json(USERS_PATH, [])
                return jsonify({"ok": True, "output": f"📢 Queued for {len(users)} users: {msg[:50]}"})

            # ── Addadmin ──
            elif command == "addadmin":
                if len(args) < 2: return jsonify({"ok": False, "output": "❌ /addadmin <uid> <level>"})
                add_admin(args[0], int(args[1]))
                return jsonify({"ok": True, "output": f"✅ {args[0]} → Level {args[1]} Admin"})

            # ── Removeadmin ──
            elif command == "removeadmin":
                if not args: return jsonify({"ok": False, "output": "❌ Provide UID"})
                if remove_admin(args[0]): return jsonify({"ok": True, "output": f"✅ Removed {args[0]}"})
                return jsonify({"ok": False, "output": "❌ Not found"})

            # ── Deleteentry ──
            elif command == "deleteentry":
                if not args: return jsonify({"ok": False, "output": "❌ Provide server ID"})
                data = load_json(JSON_PATH, [])
                new = [d for d in data if int(d.get("server",-1)) != int(args[0])]
                if len(new) == len(data): return jsonify({"ok": False, "output": "❌ Not found"})
                save_json(JSON_PATH, new)
                return jsonify({"ok": True, "output": f"✅ Deleted server {args[0]}"})

            # ── Searchlog ──
            elif command == "searchlog":
                if not args: return jsonify({"ok": False, "output": "❌ Provide UID"})
                from helpers import get_search_history
                history = get_search_history(args[0])
                if not history: return jsonify({"ok": True, "output": "No history"})
                out = f"🕐 History for {args[0]}:\n"
                for i, h in enumerate(history[:10], 1): out += f"  {i}. {h['query']} — {h['time']}\n"
                return jsonify({"ok": True, "output": out})

            # ── Payments ──
            elif command == "payments":
                payments = load_json(PAYMENTS_PATH, {})
                pending = {k: v for k, v in payments.items() if v.get("status") == "pending"}
                if not pending: return jsonify({"ok": True, "output": "✅ No pending payments"})
                out = f"💰 Pending ({len(pending)}):\n"
                for pid, info in list(pending.items())[:5]:
                    out += f"  {pid} — User {info['uid']} — ₹{info['price']}\n"
                return jsonify({"ok": True, "output": out})

            # ── Help ──
            elif command == "help":
                out = ("Available commands:\n"
                       "/status /genkey /keys /ban /unban\n"
                       "/actuser /adddays /revoke /actlist\n"
                       "/badwords /badword /removebadword\n"
                       "/warn /clearwarn /mute /unmute\n"
                       "/broadcast /addadmin /removeadmin\n"
                       "/deleteentry /searchlog /payments")
                return jsonify({"ok": True, "output": out})

            else:
                return jsonify({"ok": False, "output": f"❌ Unknown command: /{command}\nType /help for list"})

        except Exception as e:
            return jsonify({"ok": False, "output": f"❌ Error: {type(e).__name__}: {e}"})

    # ── Users ──
    @app.route("/users", methods=["GET","POST"])
    @login_required
    def users_page():
        msg = err = ""
        users = load_json(USERS_PATH, [])
        banned = load_json(BANNED_PATH, [])
        activ = load_json(ACTIVATIONS_PATH, {})
        now = int(time.time())
        if request.method == "POST":
            action = request.form.get("action")
            uid = request.form.get("uid","").strip()
            days = int(request.form.get("days",30))
            if action == "ban" and uid:
                if uid not in banned: banned.append(uid); save_json(BANNED_PATH, banned)
                msg = f"✅ Banned {uid}"
            elif action == "unban" and uid:
                if uid in banned: banned.remove(uid); save_json(BANNED_PATH, banned)
                msg = f"✅ Unbanned {uid}"
            elif action == "activate" and uid:
                activate_user(int(uid), days*24, method="panel"); msg = f"✅ Activated {uid} for {days} days"
            elif action == "deactivate" and uid:
                deactivate_user(int(uid)); msg = f"✅ Deactivated {uid}"
            elif action == "adddays" and uid:
                new_exp = extend_user(int(uid), days); msg = f"✅ +{days} days to {uid} → {new_exp}"
        q = request.args.get("q","").lower()
        rows = ""
        for uid in (users[-100:][::-1]):
            if q and q not in uid: continue
            rec = activ.get(uid)
            if rec and int(rec.get("expires_at_ts",0)) > now:
                exp = datetime.fromtimestamp(int(rec["expires_at_ts"])).strftime("%d %b %Y")
                st = f'<span class="badge bg">Active till {exp}</span>'
            else: st = '<span class="badge br">Inactive</span>'
            ban_st = '<span class="badge br">Banned</span>' if uid in banned else ""
            rows += (f"<tr><td><span class='tag'>{uid}</span></td><td>{st} {ban_st}</td><td>"
                     f"<form method='POST' style='display:inline'><input type='hidden' name='uid' value='{uid}'>")
            if uid in banned:
                rows += '<button name="action" value="unban" class="btn-g" style="padding:3px 8px;font-size:11px">Unban</button>'
            else:
                rows += '<button name="action" value="ban" class="btn-r" style="padding:3px 8px;font-size:11px">Ban</button>'
            rows += "</form></td></tr>"
        c = f"""
        <div class="box"><h3>⚡ Quick Action</h3>
        <form method="POST">
          <div class="g3">
            <input name="uid" placeholder="User ID" required>
            <input name="days" type="number" value="30" placeholder="Days">
            <select name="action">
              <option value="activate">✅ Activate</option>
              <option value="deactivate">❌ Deactivate</option>
              <option value="adddays">➕ Add Days</option>
              <option value="ban">🚫 Ban</option>
              <option value="unban">✅ Unban</option>
            </select>
          </div>
          <button>Apply</button>
        </form></div>
        <div class="box"><h3>👥 Users (Last 100)</h3>
        <form method="GET" style="margin-bottom:10px">
          <input style="width:220px;margin:0" name="q" value="{q}" placeholder="Search UID...">
        </form>
        <table><tr><th>User ID</th><th>Status</th><th>Action</th></tr>{rows}</table></div>"""
        return render("Users", c, p="users", msg=msg, err=bool(err))

    # ── Active Users ──
    @app.route("/actlist")
    @login_required
    def actlist_page():
        activ = load_json(ACTIVATIONS_PATH, {})
        now = int(time.time())
        active = {k:v for k,v in activ.items() if int(v.get("expires_at_ts",0)) > now}
        rows = "".join([
            f"<tr><td><span class='tag'>{uid}</span></td>"
            f"<td>{'🔑' if v.get('method')=='key' else '🔗'}</td>"
            f"<td>{datetime.fromtimestamp(int(v['expires_at_ts'])).strftime('%d %b %Y')}</td></tr>"
            for uid,v in list(active.items())[:50]
        ])
        c = f"""<div class="box"><h3>✅ Active Users ({len(active)})</h3>
        <table><tr><th>User ID</th><th>Method</th><th>Expires</th></tr>{rows}</table></div>"""
        return render("Active Users", c, p="actlist")

    # ── Banned ──
    @app.route("/banned", methods=["GET","POST"])
    @login_required
    def banned_page():
        msg = ""
        banned = load_json(BANNED_PATH, [])
        if request.method == "POST":
            uid = request.form.get("uid","")
            if uid in banned: banned.remove(uid); save_json(BANNED_PATH, banned); msg = f"✅ Unbanned {uid}"
        rows = "".join([
            f"<tr><td><span class='tag'>{uid}</span></td><td>"
            f"<form method='POST' style='display:inline'><input type='hidden' name='uid' value='{uid}'>"
            f"<button class='btn-g' style='padding:3px 8px;font-size:11px'>Unban</button></form></td></tr>"
            for uid in banned
        ])
        c = f"""<div class="box"><h3>🚫 Banned ({len(banned)})</h3>
        <table><tr><th>User ID</th><th>Action</th></tr>
        {rows or "<tr><td colspan=2 style=color:#555;text-align:center>No banned users</td></tr>"}
        </table></div>"""
        return render("Banned", c, p="banned", msg=msg)

    # ── Warnings ──
    @app.route("/warnings_page")
    @login_required
    def warnings_page():
        warnings = load_json(WARNINGS_PATH, {})
        rows = "".join([
            f"<tr><td><span class='tag'>{uid}</span></td><td>{len(warns)}</td>"
            f"<td>{warns[-1]['reason'] if warns else ''}</td></tr>"
            for uid, warns in warnings.items() if warns
        ])
        c = f"""<div class="box"><h3>⚠️ User Warnings</h3>
        <table><tr><th>User ID</th><th>Count</th><th>Last Reason</th></tr>
        {rows or "<tr><td colspan=3 style=color:#555;text-align:center>No warnings</td></tr>"}
        </table></div>"""
        return render("Warnings", c, p="warn")

    # ── Keys ──
    @app.route("/keys", methods=["GET","POST"])
    @login_required
    def keys_page():
        msg = ""
        keys_db = load_json(KEYS_PATH, {})
        if request.method == "POST":
            action = request.form.get("action")
            if action == "generate":
                count = int(request.form.get("count",1))
                days  = int(request.form.get("days",30))
                from helpers import create_keys
                create_keys(count, days)
                keys_db = load_json(KEYS_PATH, {})
                msg = f"✅ {count} key(s) generated for {days} days!"
            elif action == "delete":
                k = request.form.get("key")
                if k in keys_db: del keys_db[k]; save_json(KEYS_PATH, keys_db); msg = "✅ Key deleted"
        unused = [(k,v) for k,v in keys_db.items() if not v.get("used")]
        used   = [(k,v) for k,v in keys_db.items() if v.get("used")]
        u_rows = "".join([
            f"<tr><td><span class='tag'>{k}</span></td><td>{v['days']}d</td>"
            f"<td>{v.get('created_at','')[:10]}</td>"
            f"<td><form method='POST' style='display:inline'>"
            f"<input type='hidden' name='action' value='delete'>"
            f"<input type='hidden' name='key' value='{k}'>"
            f"<button class='btn-r' style='padding:3px 8px;font-size:11px'>Del</button></form></td></tr>"
            for k,v in unused[:50]
        ])
        c = f"""
        <div class="box"><h3>🔑 Generate Keys</h3>
        <form method="POST"><input type="hidden" name="action" value="generate">
          <div class="g2">
            <input name="count" type="number" value="5" placeholder="Count">
            <input name="days" type="number" value="30" placeholder="Days">
          </div>
          <button>Generate</button>
          <a href="/export?type=keys" class="btn btn-y" style="margin-left:8px">📤 Export CSV</a>
        </form></div>
        <div class="box"><h3>🔓 Unused ({len(unused)})</h3>
        <table><tr><th>Key</th><th>Plan</th><th>Created</th><th>Del</th></tr>
        {u_rows or '<tr><td colspan=4 style=color:#555;text-align:center>None</td></tr>'}</table></div>
        <div class="box"><h3>✅ Used ({len(used)})</h3>
        <table><tr><th>Key</th><th>Plan</th><th>Used By</th><th>Date</th></tr>
        {"".join([f'<tr><td><span class=tag>{k}</span></td><td>{v[\"days\"]}d</td><td><span class=tag>{v.get(\"used_by\",\"?\")}</span></td><td>{v.get(\"used_at\",\"\")[:10]}</td></tr>' for k,v in used[-20:]])
        or '<tr><td colspan=4 style=color:#555;text-align:center>None</td></tr>'}</table></div>"""
        return render("Keys", c, p="keys", msg=msg)

    # ── Payments ──
    @app.route("/payments", methods=["GET","POST"])
    @login_required
    def payments_page():
        msg = ""
        payments = load_json(PAYMENTS_PATH, {})
        activ = load_json(ACTIVATIONS_PATH, {})
        if request.method == "POST":
            action = request.form.get("action")
            pay_id = request.form.get("pay_id")
            if pay_id in payments:
                info = payments[pay_id]
                if action == "approve":
                    from helpers import create_keys, use_key
                    uid = int(info["uid"]); days = info["days"]
                    keys = create_keys(1, days); use_key(keys[0], uid)
                    payments[pay_id]["status"] = "approved"
                    save_json(PAYMENTS_PATH, payments)
                    msg = f"✅ Approved {pay_id}!"
                elif action == "reject":
                    payments[pay_id]["status"] = "rejected"
                    save_json(PAYMENTS_PATH, payments)
                    msg = f"❌ Rejected {pay_id}"
        rows = ""
        for pid, info in sorted(payments.items(), key=lambda x: x[1].get("created_at",""), reverse=True)[:50]:
            st = info.get("status","pending")
            bc = "bg" if st=="approved" else ("br" if st=="rejected" else "by")
            rows += (f"<tr><td><span class='tag'>{pid}</span></td>"
                     f"<td><span class='tag'>{info.get('uid','?')}</span></td>"
                     f"<td>₹{info.get('price','?')} / {info.get('days','?')}d</td>"
                     f"<td>{info.get('created_at','')[:10]}</td>"
                     f"<td><span class='badge {bc}'>{st.upper()}</span></td><td>")
            if st == "pending":
                rows += (f"<form method='POST' style='display:inline'>"
                         f"<input type='hidden' name='pay_id' value='{pid}'>"
                         f"<button name='action' value='approve' class='btn-g' style='padding:3px 8px;font-size:11px'>✅</button> "
                         f"<button name='action' value='reject' class='btn-r' style='padding:3px 8px;font-size:11px'>❌</button></form>")
            rows += "</td></tr>"
        c = f"""<div class="box"><h3>💰 Payments ({len(payments)})</h3>
        <table><tr><th>Pay ID</th><th>User</th><th>Plan</th><th>Date</th><th>Status</th><th>Action</th></tr>
        {rows or "<tr><td colspan=6 style=color:#555;text-align:center>No payments</td></tr>"}</table></div>"""
        return render("Payments", c, p="pay", msg=msg)

    # ── Movies ──
    @app.route("/movies", methods=["GET","POST"])
    @login_required
    def movies_page():
        msg = ""
        data = load_json(JSON_PATH, [])
        if request.method == "POST":
            sid = int(request.form.get("server_id",-1))
            data = [d for d in data if int(d.get("server",-1)) != sid]
            save_json(JSON_PATH, data); msg = f"✅ Deleted {sid}"
        q = request.args.get("q","").lower()
        pg = int(request.args.get("pg",0))
        filtered = [d for d in data if q in d.get("title","").lower()] if q else data
        chunk = filtered[pg*50:(pg+1)*50]
        rows = "".join([
            f"<tr><td>{d.get('server')}</td><td>{d.get('title','')[:40]}</td>"
            f"<td>{d.get('size','?')}</td><td>📥 {d.get('downloads',0)}</td>"
            f"<td><form method='POST' style='display:inline'>"
            f"<input type='hidden' name='server_id' value='{d.get('server')}'>"
            f"<button class='btn-r' style='padding:3px 8px;font-size:11px' onclick=\"return confirm('Delete?')\">Del</button></form></td></tr>"
            for d in chunk
        ])
        pb = f"<a href='?q={q}&pg={pg-1}' class='btn'>◀️</a> " if pg > 0 else ""
        nb = f"<a href='?q={q}&pg={pg+1}' class='btn'>▶️</a>" if (pg+1)*50 < len(filtered) else ""
        c = f"""<div class="box"><h3>🎬 Movies ({len(filtered)})</h3>
        <div style="display:flex;gap:8px;margin-bottom:10px">
          <form method="GET"><input style="margin:0;width:200px" name="q" value="{q}" placeholder="Search...">
          <button type="submit" style="margin-left:6px">🔍</button></form>
          <a href="/export?type=movies" class="btn btn-y">📤 CSV</a>
        </div>
        <table><tr><th>Server</th><th>Title</th><th>Size</th><th>DL</th><th>Del</th></tr>{rows}</table>
        <div style="margin-top:10px">{pb}{nb}</div></div>"""
        return render("Movies", c, p="movies", msg=msg)

    # ── Creator Files ──
    @app.route("/files_page", methods=["GET","POST"])
    @login_required
    def files_page():
        msg = ""
        if request.method == "POST":
            key = request.form.get("file_key","")
            delete_file(key); msg = f"✅ File {key} deleted"
        files = get_all_files()
        rows = ""
        for key, info in list(files.items())[:50]:
            if not info.get("active"): continue
            pwd = "🔒" if info.get("password") else ""
            rows += (f"<tr><td><span class='tag'>{key}</span></td>"
                     f"<td>{pwd} {info.get('title','')[:30]}</td>"
                     f"<td>{info.get('file_type','?')}</td>"
                     f"<td><span class='tag'>{info.get('creator_uid','?')}</span></td>"
                     f"<td>📥 {info.get('downloads',0)}</td>"
                     f"<td><form method='POST' style='display:inline'>"
                     f"<input type='hidden' name='file_key' value='{key}'>"
                     f"<button class='btn-r' style='padding:3px 8px;font-size:11px'>Del</button></form></td></tr>")
        c = f"""<div class="box"><h3>📁 Creator Files ({len(files)})</h3>
        <table><tr><th>Key</th><th>Title</th><th>Type</th><th>Creator</th><th>DL</th><th>Del</th></tr>
        {rows or "<tr><td colspan=6 style=color:#555;text-align:center>No files</td></tr>"}</table></div>"""
        return render("Creator Files", c, p="files", msg=msg)

    # ── Creators ──
    @app.route("/creators")
    @login_required
    def creators_page():
        creators = get_all_creators()
        rows = ""
        for uid, info in creators.items():
            stats = get_creator_earnings(uid)
            rows += (f"<tr><td><span class='tag'>{uid}</span></td>"
                     f"<td>{info.get('name','?')}</td>"
                     f"<td>📥 {stats.get('total_dl',0)}</td>"
                     f"<td>💵 ${stats.get('earned',0)}</td>"
                     f"<td>${stats.get('pending',0)}</td></tr>")
        c = f"""<div class="box"><h3>🎬 Creators ({len(creators)})</h3>
        <table><tr><th>User ID</th><th>Name</th><th>Total DL</th><th>Earned</th><th>Pending</th></tr>
        {rows or "<tr><td colspan=5 style=color:#555;text-align:center>No creators</td></tr>"}</table></div>"""
        return render("Creators", c, p="creators")

    # ── Trending ──
    @app.route("/trending")
    @login_required
    def trending_page():
        data = load_json(JSON_PATH, [])
        top = sorted(data, key=lambda x: x.get("downloads",0), reverse=True)[:20]
        rows = "".join([f"<tr><td>{i+1}</td><td>{m['title'][:40]}</td><td>📥 {m.get('downloads',0)}</td><td>{m.get('size','?')}</td></tr>" for i,m in enumerate(top)])
        c = f"""<div class="box"><h3>🔥 Top 20 Trending</h3>
        <table><tr><th>#</th><th>Title</th><th>Downloads</th><th>Size</th></tr>{rows}</table></div>"""
        return render("Trending", c, p="trend")

    # ── Broadcast ──
    @app.route("/broadcast", methods=["GET","POST"])
    @login_required
    def broadcast_page():
        msg = ""
        users = load_json(USERS_PATH, [])
        if request.method == "POST":
            text = request.form.get("message","").strip()
            if text:
                queue = load_json("broadcast_queue.json", [])
                queue.append({"text": text, "queued_at": datetime.now().isoformat()})
                save_json("broadcast_queue.json", queue)
                msg = f"✅ Queued for {len(users)} users!"
        c = f"""<div class="box"><h3>📢 Broadcast</h3>
        <p style="color:#6b7280;font-size:12px;margin-bottom:12px">Target: <strong style="color:#a78bfa">{len(users)}</strong> users</p>
        <form method="POST">
          <textarea name="message" rows="5" placeholder="Message..." required></textarea>
          <button>📤 Send</button>
        </form></div>"""
        return render("Broadcast", c, p="bcast", msg=msg)

    # ── Acting Admins ──
    @app.route("/admins", methods=["GET","POST"])
    @login_required
    def admins_page():
        msg = ""
        if request.method == "POST":
            action = request.form.get("action")
            uid = request.form.get("uid","").strip()
            if action == "add" and uid:
                add_admin(uid, int(request.form.get("level",1)))
                msg = f"✅ Added {uid}"
            elif action == "remove" and uid:
                remove_admin(uid); msg = f"✅ Removed {uid}"
        admins = get_all_admins()
        rows = "".join([
            f"<tr><td><span class='tag'>{uid}</span></td>"
            f"<td>{LEVEL_LABELS.get(info.get('level',1),'?')}</td>"
            f"<td>{info.get('added_at','')[:10]}</td>"
            f"<td><form method='POST' style='display:inline'><input type='hidden' name='uid' value='{uid}'>"
            f"<button name='action' value='remove' class='btn-r' style='padding:3px 8px;font-size:11px'>Remove</button></form></td></tr>"
            for uid,info in admins.items()
        ])
        c = f"""
        <div class="box"><h3>➕ Add Admin</h3>
        <form method="POST"><input type="hidden" name="action" value="add">
          <div class="g2">
            <input name="uid" placeholder="User ID" required>
            <select name="level">
              <option value="1">Level 1 — Search+Fetch</option>
              <option value="2">Level 2 — +Ban/Genkey</option>
              <option value="3">Level 3 — +Broadcast</option>
              <option value="4">Creator — File Upload</option>
            </select>
          </div>
          <button>Add</button>
        </form></div>
        <div class="box"><h3>👮 Acting Admins ({len(admins)})</h3>
        <table><tr><th>User ID</th><th>Level</th><th>Added</th><th>Remove</th></tr>
        {rows or "<tr><td colspan=4 style=color:#555;text-align:center>None</td></tr>"}</table></div>"""
        return render("Acting Admins", c, p="admins", msg=msg)

    # ── Bad Words ──
    @app.route("/badwords", methods=["GET","POST"])
    @login_required
    def badwords_page():
        msg = ""
        if request.method == "POST":
            action = request.form.get("action")
            word = request.form.get("word","").strip().lower()
            if action == "add" and word:
                if add_bad_word(word): msg = f"✅ Added: {word}"
                else: msg = "⚠️ Already exists"
            elif action == "remove" and word:
                if remove_bad_word(word): msg = f"✅ Removed: {word}"
                else: msg = "❌ Not found"
        words = get_bad_words()
        logs = get_bad_word_logs(20)
        w_items = "".join([
            f"<span style='display:inline-flex;align-items:center;gap:4px;background:#1e1e3a;padding:3px 8px;border-radius:5px;margin:2px'>"
            f"<span class='tag'>{w}</span>"
            f"<form method='POST' style='display:inline'><input type='hidden' name='action' value='remove'>"
            f"<input type='hidden' name='word' value='{w}'>"
            f"<button style='background:none;border:none;color:#f87171;cursor:pointer;padding:0;font-size:13px'>✕</button></form></span>"
            for w in words
        ])
        log_rows = "".join([
            f"<tr><td><span class='tag'>{l['uid']}</span></td>"
            f"<td><span class='badge br'>{l['word_used']}</span></td>"
            f"<td style='color:#9ca3af'>{l['time']}</td></tr>"
            for l in logs
        ])
        c = f"""
        <div class="box"><h3>➕ Add Bad Word</h3>
        <form method="POST" style="display:flex;gap:8px">
          <input name="word" placeholder="Enter word..." required style="margin:0">
          <input type="hidden" name="action" value="add">
          <button>Add</button>
        </form></div>
        <div class="box"><h3>🚫 Words ({len(words)})</h3>
        <div style="padding:6px 0">{w_items or '<span style=color:#555>None yet</span>'}</div></div>
        <div class="box"><h3>📋 Logs</h3>
        <table><tr><th>User</th><th>Word</th><th>Time</th></tr>
        {log_rows or "<tr><td colspan=3 style=color:#555;text-align:center>No logs</td></tr>"}</table></div>"""
        return render("Bad Words", c, p="bw", msg=msg)

    # ── Ads ──
    @app.route("/ads", methods=["GET","POST"])
    @login_required
    def ads_page():
        msg = ""
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add":
                ad_id = add_ad(request.form.get("title",""), request.form.get("url",""), request.form.get("button_text","Visit"))
                msg = f"✅ Ad added! ID: {ad_id}"
            elif action == "delete":
                remove_ad(request.form.get("ad_id","")); msg = "✅ Deleted"
            elif action == "toggle":
                st = toggle_ad(request.form.get("ad_id",""))
                msg = f"✅ {'Activated' if st else 'Deactivated'}"
        ads = get_all_ads()
        rows = "".join([
            f"<tr><td><span class='tag'>{ad['id']}</span></td><td>{ad['title'][:25]}</td>"
            f"<td>{ad.get('button_text','')}</td><td>👆 {ad.get('clicks',0)}</td>"
            f"<td>{'✅' if ad.get('active') else '❌'}</td><td>"
            f"<form method='POST' style='display:inline'><input type='hidden' name='ad_id' value='{ad['id']}'>"
            f"<button name='action' value='toggle' class='btn-y' style='padding:3px 8px;font-size:11px'>Toggle</button> "
            f"<button name='action' value='delete' class='btn-r' style='padding:3px 8px;font-size:11px'>Del</button></form></td></tr>"
            for ad in ads
        ])
        c = f"""
        <div class="box"><h3>➕ New Ad</h3>
        <form method="POST"><input type="hidden" name="action" value="add">
          <div class="g2">
            <input name="title" placeholder="Ad Title" required>
            <input name="url" placeholder="URL (https://...)" required>
          </div>
          <input name="button_text" placeholder="Button Text" required>
          <button>Add Ad</button>
        </form></div>
        <div class="box"><h3>📣 Ads ({len(ads)})</h3>
        <table><tr><th>ID</th><th>Title</th><th>Button</th><th>Clicks</th><th>Status</th><th>Action</th></tr>
        {rows or "<tr><td colspan=6 style=color:#555;text-align:center>None</td></tr>"}</table></div>"""
        return render("Advertisements", c, p="ads", msg=msg)

    # ── Referrals ──
    @app.route("/referrals")
    @login_required
    def referrals_page():
        refs = get_all_referrals()
        days = get_referral_days()
        rows = "".join([
            f"<tr><td><span class='tag'>{code}</span></td>"
            f"<td><span class='tag'>{info.get('owner','?')}</span></td>"
            f"<td>👥 {info.get('uses',0)}</td>"
            f"<td>{info.get('created_at','')[:10]}</td></tr>"
            for code,info in list(refs.items())[:50]
        ])
        c = f"""
        <div class="box"><h3>⚙️ Settings</h3>
        <div style="display:flex;justify-content:space-between;padding:8px 0;font-size:13px">
          <span>Days per referral:</span><span style="color:#a78bfa">{days} days</span>
        </div>
        <p style="color:#6b7280;font-size:11px">Change: /setreferral &lt;days&gt; in bot</p></div>
        <div class="box"><h3>🎁 Referrals ({len(refs)})</h3>
        <table><tr><th>Code</th><th>Owner</th><th>Uses</th><th>Created</th></tr>
        {rows or "<tr><td colspan=4 style=color:#555;text-align:center>None</td></tr>"}</table></div>"""
        return render("Referrals", c, p="ref")

    # ── Notes ──
    @app.route("/notes", methods=["GET","POST"])
    @login_required
    def notes_page():
        msg = ""
        if request.method == "POST":
            action = request.form.get("action")
            if action == "add":
                save_note(request.form.get("key",""), request.form.get("text",""), "panel")
                msg = "✅ Note saved!"
            elif action == "delete":
                delete_note(request.form.get("key",""))
                msg = "✅ Note deleted"
        notes = get_all_notes()
        rows = "".join([
            f"<tr><td><span class='tag'>{k}</span></td><td>{v.get('text','')[:50]}</td>"
            f"<td>{v.get('time','')}</td>"
            f"<td><form method='POST' style='display:inline'><input type='hidden' name='action' value='delete'>"
            f"<input type='hidden' name='key' value='{k}'>"
            f"<button class='btn-r' style='padding:3px 8px;font-size:11px'>Del</button></form></td></tr>"
            for k,v in notes.items()
        ])
        c = f"""
        <div class="box"><h3>➕ Add Note</h3>
        <form method="POST"><input type="hidden" name="action" value="add">
          <div class="g2">
            <input name="key" placeholder="Key (e.g. rules)" required>
            <input name="text" placeholder="Note text" required>
          </div>
          <button>Save Note</button>
        </form></div>
        <div class="box"><h3>📌 Notes ({len(notes)})</h3>
        <table><tr><th>Key</th><th>Text</th><th>Date</th><th>Del</th></tr>
        {rows or "<tr><td colspan=4 style=color:#555;text-align:center>None</td></tr>"}</table></div>"""
        return render("Notes", c, p="notes", msg=msg)

    # ── Reports ──
    @app.route("/reports")
    @login_required
    def reports_page():
        pending = get_reports("pending")
        rows = "".join([
            f"<tr><td><span class='tag'>{r['reporter']}</span></td>"
            f"<td><span class='tag'>{r['reported']}</span></td>"
            f"<td>{r['reason']}</td><td>{r['time']}</td></tr>"
            for r in pending
        ])
        c = f"""<div class="box"><h3>🚨 Pending Reports ({len(pending)})</h3>
        <table><tr><th>Reporter</th><th>Reported</th><th>Reason</th><th>Time</th></tr>
        {rows or "<tr><td colspan=4 style=color:#555;text-align:center>No pending reports</td></tr>"}</table></div>"""
        return render("Reports", c, p="reports")

    # ── History ──
    @app.route("/history")
    @login_required
    def history_page():
        history = load_json(SEARCH_HIST_PATH, {})
        uid_f = request.args.get("uid","").strip()
        all_s = []
        for uid, searches in history.items():
            if uid_f and uid != uid_f: continue
            for s in searches[:10]: all_s.append({"uid": uid, **s})
        all_s = sorted(all_s, key=lambda x: x.get("time",""), reverse=True)[:200]
        rows = "".join([f"<tr><td><span class='tag'>{s['uid']}</span></td><td>{s['query']}</td><td style='color:#6b7280'>{s['time']}</td></tr>" for s in all_s])
        c = f"""<div class="box"><h3>🕐 Search History</h3>
        <form method="GET" style="display:flex;gap:8px;margin-bottom:10px">
          <input style="margin:0;width:200px" name="uid" value="{uid_f}" placeholder="Filter by UID...">
          <button type="submit">🔍</button>
          {'<a href="/history" class="btn btn-y">Clear</a>' if uid_f else ''}
        </form>
        <table><tr><th>User</th><th>Query</th><th>Time</th></tr>
        {rows or "<tr><td colspan=3 style=color:#555;text-align:center>No history</td></tr>"}</table></div>"""
        return render("Search History", c, p="hist")

    # ── Settings ──
    @app.route("/settings", methods=["GET","POST"])
    @login_required
    def settings_page():
        msg = ""
        s = get_settings()
        if request.method == "POST":
            for key in ["short","act_short","creator_short","force_join","maintenance",
                        "auto_delete","new_user_alert","movie_token","captcha_enabled","original_link"]:
                update_setting(key, key in request.form)
            for key, typ in [("delete_timer",int),("referral_days",int),("max_warnings",int)]:
                val = request.form.get(key,"")
                try: update_setting(key, typ(val))
                except: pass
            for key in ["force_channel","promote_channel","welcome_msg","upi_id"]:
                val = request.form.get(key,"")
                if val: update_setting(key, val)
            msg = "✅ Settings saved!"; s = get_settings()
        def chk(k): return "checked" if s.get(k) else ""
        c = f"""<div class="box"><h3>⚙️ Bot Settings V16</h3>
        <form method="POST">
          <label class="toggle"><input type="checkbox" name="short" {chk('short')}><span>🔗 DL Shortener</span></label>
          <label class="toggle"><input type="checkbox" name="act_short" {chk('act_short')}><span>🔑 Activation Shortener</span></label>
          <label class="toggle"><input type="checkbox" name="creator_short" {chk('creator_short')}><span>🎬 Creator Shortener</span></label>
          <label class="toggle"><input type="checkbox" name="original_link" {chk('original_link')}><span>🔗 Show Original Links</span></label>
          <label class="toggle"><input type="checkbox" name="movie_token" {chk('movie_token')}><span>🎟️ Movie Link Token</span></label>
          <label class="toggle"><input type="checkbox" name="force_join" {chk('force_join')}><span>📢 Force Join</span></label>
          <label class="toggle"><input type="checkbox" name="maintenance" {chk('maintenance')}><span>🌙 Maintenance Mode</span></label>
          <label class="toggle"><input type="checkbox" name="auto_delete" {chk('auto_delete')}><span>🗑️ Auto Delete</span></label>
          <label class="toggle"><input type="checkbox" name="new_user_alert" {chk('new_user_alert')}><span>🔔 New User Alert</span></label>
          <label class="toggle"><input type="checkbox" name="captcha_enabled" {chk('captcha_enabled')}><span>🤖 CAPTCHA</span></label>
          <div class="g3" style="margin-top:10px">
            <div><label style="color:#9ca3af;font-size:11px">⏰ Delete Timer (min)</label>
            <input name="delete_timer" type="number" value="{s.get('delete_timer',180)}"></div>
            <div><label style="color:#9ca3af;font-size:11px">🎁 Referral Days</label>
            <input name="referral_days" type="number" value="{s.get('referral_days',3)}"></div>
            <div><label style="color:#9ca3af;font-size:11px">⚠️ Max Warnings</label>
            <input name="max_warnings" type="number" value="{s.get('max_warnings',3)}"></div>
          </div>
          <label style="color:#9ca3af;font-size:11px">📢 Force Join Channel</label>
          <input name="force_channel" value="{s.get('force_channel','')}">
          <label style="color:#9ca3af;font-size:11px">📣 Promote Channel</label>
          <input name="promote_channel" value="{s.get('promote_channel','')}">
          <label style="color:#9ca3af;font-size:11px">💳 UPI ID</label>
          <input name="upi_id" value="{s.get('upi_id','')}">
          <label style="color:#9ca3af;font-size:11px">👋 Welcome Message</label>
          <textarea name="welcome_msg" rows="3">{s.get('welcome_msg','')}</textarea>
          <button>💾 Save Settings</button>
        </form></div>"""
        return render("Settings", c, p="set", msg=msg)

    # ── Export CSV ──
    @app.route("/export")
    @login_required
    def export_page():
        export_type = request.args.get("type","")
        if export_type == "users":
            users = load_json(USERS_PATH, [])
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["User ID"])
            for u in users: w.writerow([u])
            return Response(output.getvalue(), mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=users.csv"})
        elif export_type == "keys":
            keys_db = load_json(KEYS_PATH, {})
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["Key","Days","Used","Used By","Used At","Created"])
            for k,v in keys_db.items():
                w.writerow([k, v.get("days",""), v.get("used",""), v.get("used_by",""), v.get("used_at",""), v.get("created_at","")])
            return Response(output.getvalue(), mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=keys.csv"})
        elif export_type == "movies":
            data = load_json(JSON_PATH, [])
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["Server","Title","Size","Downloads","Fetched At"])
            for d in data: w.writerow([d.get("server",""), d.get("title",""), d.get("size",""), d.get("downloads",0), d.get("fetched_at","")])
            return Response(output.getvalue(), mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=movies.csv"})
        elif export_type == "creators":
            creators = get_all_creators()
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["User ID","Name","Total DL","Earned $","Withdrawn $"])
            for uid, info in creators.items():
                stats = get_creator_earnings(uid)
                w.writerow([uid, info.get("name",""), stats.get("total_dl",0), stats.get("earned",0), stats.get("withdrawn",0)])
            return Response(output.getvalue(), mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=creators.csv"})
        elif export_type == "files":
            files = get_all_files()
            output = io.StringIO()
            w = csv.writer(output)
            w.writerow(["File Key","Title","Type","Creator","Downloads","Uploaded At"])
            for key, info in files.items():
                w.writerow([key, info.get("title",""), info.get("file_type",""), info.get("creator_uid",""), info.get("downloads",0), info.get("uploaded_at","")])
            return Response(output.getvalue(), mimetype="text/csv",
                headers={"Content-Disposition": "attachment;filename=files.csv"})

        # Export selection page
        c = """<div class="box"><h3>📤 Export CSV</h3>
        <p style="color:#6b7280;font-size:12px;margin-bottom:14px">Choose what to export:</p>
        <div style="display:flex;flex-wrap:wrap;gap:10px">
          <a href="/export?type=users" class="btn">👥 Users</a>
          <a href="/export?type=keys" class="btn">🔑 Keys</a>
          <a href="/export?type=movies" class="btn btn-y">🎬 Movies</a>
          <a href="/export?type=creators" class="btn btn-g">🎬 Creators</a>
          <a href="/export?type=files" class="btn" style="background:#db2777">📁 Files</a>
        </div></div>"""
        return render("Export CSV", c, p="exp")

    # ── API Stats ──
    @app.route("/api/stats")
    @login_required
    def api_stats():
        data = load_json(JSON_PATH, [])
        users = load_json(USERS_PATH, [])
        activ = load_json(ACTIVATIONS_PATH, {})
        now = int(time.time())
        return jsonify({
            "users": len(users),
            "active": sum(1 for v in activ.values() if int(v.get("expires_at_ts",0)) > now),
            "movies": len(data),
            "downloads": sum(d.get("downloads",0) for d in data)
        })

    return app

if __name__ == "__main__":
    panel = create_app()
    print("🌐 Web Panel V16 → http://localhost:5000")
    panel.run(host="0.0.0.0", port=5000, debug=True)
