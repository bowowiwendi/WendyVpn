from telethon import *
import datetime as DT
import requests,time,os,subprocess,re,sqlite3,sys,random,base64,json,math,shlex,asyncio,shutil
import logging
#usr/local/bin/kyt
logging.basicConfig(level=logging.INFO)
uptime = DT.datetime.now()

exec(open("kyt/var.txt","r").read())
bot = TelegramClient("ddsdswl","6","eb06d4abfb49dc3eeb1aeb98ae0f581e").start(bot_token=BOT_TOKEN)

API_BASE = os.environ.get("WENDY_API_BASE", "http://127.0.0.1:9000")
API_TOKEN_FILE = os.environ.get("WENDY_API_TOKEN_FILE", "/etc/wendy-api/token")


def api_token():
    try:
        with open(API_TOKEN_FILE, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except Exception:
        return ""


def api_account_command(cmd, timeout=120):
    """Run legacy account command through the Wendy API account endpoints."""
    mapped = api_map_account_command(cmd)
    if not mapped:
        raise ValueError("account command is not supported by API mapping")
    endpoint, payload = mapped
    return api_post(endpoint, payload, timeout=timeout)


def api_maintenance_command(cmd, timeout=180):
    """Run supported maintenance command through dedicated API endpoints."""
    mapped = api_map_maintenance_command(cmd)
    if not mapped:
        raise ValueError("maintenance command is not supported by API mapping")
    endpoint, payload = mapped
    return api_post(endpoint, payload, timeout=timeout)


def api_create_account(service, username, password="", limit_ip="2", quota="100", days="1", bug="", trial=False, timeout=120):
    payload = {
        "service": service,
        "username": username,
        "password": password,
        "limit_ip": str(limit_ip),
        "quota": str(quota),
        "days": str(days),
        "bug": bug,
        "trial": bool(trial),
    }
    return api_post("/api/accounts/create", payload, timeout=timeout)


def api_renew_account(service, username, days="1", quota="100", limit_ip="2", timeout=120):
    payload = {
        "service": service,
        "username": username,
        "days": str(days),
        "quota": str(quota),
        "limit_ip": str(limit_ip),
    }
    return api_post("/api/accounts/renew", payload, timeout=timeout)


def api_delete_account(service, username, timeout=120):
    return api_post("/api/accounts/delete", {"service": service, "username": username}, timeout=timeout)


def api_post(endpoint, payload, timeout=None):
    headers = {}
    token = api_token()
    if token:
        headers["X-API-Token"] = token
    response = requests.post(
        f"{API_BASE}{endpoint}",
        json=payload,
        headers=headers,
        timeout=timeout or 120,
    )
    payload = response.json()
    if response.status_code != 200 or not payload.get("ok"):
        message = payload.get("stderr") or payload.get("error") or "api command failed"
        raise subprocess.CalledProcessError(payload.get("returncode", response.status_code), endpoint, output=payload.get("stdout", ""), stderr=message)
    return payload.get("stdout", "") or payload.get("account_text", "")


def api_extract_printf(cmd):
    if not isinstance(cmd, str):
        return None
    match = re.match(r"^printf\s+['\"]%s\\n['\"]\s+(.*?)\s+\|\s*([A-Za-z0-9_.-]+)\s*$", cmd.strip(), re.S)
    if not match:
        return None
    try:
        values = shlex.split(match.group(1))
    except Exception:
        return None
    return values, match.group(2)


def api_map_account_command(cmd):
    parsed = api_extract_printf(cmd)
    if not parsed:
        return None
    values, script = parsed
    create_map = {
        'addssh': 'ssh', 'addws': 'vmess', 'addvless': 'vless',
        'addtr': 'trojan', 'addss': 'shadowsocks',
    }
    trial_map = {
        'trial': 'ssh', 'trialws': 'vmess', 'trialvless': 'vless',
        'trialtr': 'trojan', 'trialss': 'shadowsocks',
    }
    renew_map = {
        'renewssh': 'ssh', 'renewws': 'vmess', 'renewvless': 'vless',
        'renewtr': 'trojan', 'renewss': 'shadowsocks',
    }
    delete_map = {
        'delssh': 'ssh', 'delws': 'vmess', 'delvless': 'vless',
        'deltr': 'trojan', 'delss': 'shadowsocks',
    }
    if script in create_map:
        svc = create_map[script]
        if svc == 'ssh' and len(values) >= 4:
            return "/api/accounts/create", {"service": svc, "username": values[0], "password": values[1], "limit_ip": values[2], "days": values[3], "bug": values[4] if len(values) > 4 else ""}
        if svc in ('vmess', 'vless', 'trojan') and len(values) >= 4:
            return "/api/accounts/create", {"service": svc, "username": values[0], "limit_ip": values[1], "quota": values[2], "days": values[3], "bug": values[4] if len(values) > 4 else ""}
        if svc == 'shadowsocks' and len(values) >= 4:
            return "/api/accounts/create", {"service": svc, "username": values[0], "limit_ip": values[1], "days": values[2], "quota": values[3], "bug": values[4] if len(values) > 4 else ""}
    if script in trial_map:
        svc = trial_map[script]
        if svc == 'ssh' and len(values) >= 4:
            return "/api/accounts/create", {"service": svc, "username": values[0], "password": values[1], "limit_ip": values[2], "days": values[3], "trial": True}
        if len(values) >= 1:
            import random as _random
            trial_user = "trial" + str(_random.randint(1000, 9999))
            return "/api/accounts/create", {"service": svc, "days": values[0], "trial": True, "username": trial_user}
    if script in renew_map and len(values) >= 2:
        svc = renew_map[script]
        payload = {"service": svc, "username": values[0], "days": values[1]}
        if svc in ('vmess', 'vless', 'trojan'):
            payload["quota"] = values[2] if len(values) > 2 else "100"
            payload["limit_ip"] = values[3] if len(values) > 3 else "2"
        return "/api/accounts/renew", payload
    if script in delete_map and len(values) >= 1:
        return "/api/accounts/delete", {"service": delete_map[script], "username": values[0]}
    return None


def api_map_maintenance_command(cmd):
    if not isinstance(cmd, str):
        return None
    normalized = cmd.strip()
    if normalized == 'cek-ssh-login':
        return '/api/maintenance/cek-login-ssh', {}
    if normalized == 'xp':
        return '/api/maintenance/xp', {}
    if normalized == 'clean_lock.sh':
        return '/api/maintenance/clean-lock', {}
    if normalized == 'bot-backup':
        return '/api/maintenance/backup', {}
    if normalized == 'notif_delet':
        return '/api/maintenance/notif-delet', {}
    if normalized == 'notif_backup':
        return '/api/maintenance/notif-backup', {}
    if normalized == 'notif_limit':
        return '/api/maintenance/notif-limit', {}
    if normalized == 'reboot':
        return '/api/maintenance/reboot', {}
    if normalized == 'speedtest-cli --share':
        return '/api/maintenance/speedtest', {}
    if normalized == 'fixcert':
        return '/api/maintenance/fixcert', {}
    if normalized == "printf '%s\n' '3' | auto-delet.sh":
        return '/api/maintenance/toggle-auto-delete', {'state': 'on'}
    if normalized == "printf '%s\n' '1' | auto-delet.sh":
        return '/api/maintenance/toggle-auto-delete', {'state': 'off'}
    if normalized == "printf '%s\n' '8' | auto-backup.sh":
        return '/api/maintenance/toggle-auto-backup', {'state': 'on'}
    if normalized == "printf '%s\n' '3' | auto-backup.sh":
        return '/api/maintenance/toggle-auto-backup', {'state': 'off'}
    if normalized == "printf '%s\n' '1' | onoff":
        return '/api/maintenance/toggle-limit', {'state': 'on'}
    if normalized == "printf '%s\n' '2' | onoff":
        return '/api/maintenance/toggle-limit', {'state': 'off'}
    if normalized.startswith("printf '%s\\n' ") and normalized.endswith("| addhost"):
        match = re.match(r"^printf '%s\\n' \"?(.*?)\"? \| addhost$", normalized)
        if match:
            return '/api/maintenance/addhost', {'domain': match.group(1)}
    if normalized.startswith("printf '%s\\n' ") and "| add-bot-notif" in normalized:
        parts_m = re.match(r"^printf '%s\\\\n' \"?(.*?)\"? \"?(.*?)\"? \\| add-bot-notif$", normalized)
        if parts_m:
            return '/api/maintenance/add-bot-notif', {'user': parts_m.group(1), 'chat_id': parts_m.group(2)}
    if normalized == 'del-bot-notif':
        return '/api/maintenance/del-bot-notif', {}
    if normalized.startswith("printf '%s\\n' ") and normalized.endswith("| menu"):
        match = re.match(r"^printf '%s\\\\n' \"?(.*?)\"? \\| menu$", normalized)
        if match:
            return '/api/maintenance/run-menu', {'option': match.group(1)}
    if normalized.startswith("printf '%s\\n' ") and normalized.endswith("| bot-restore"):
        match = re.match(r"^printf '%s\\n' \"?(.*?)\"? \| bot-restore$", normalized)
        if match:
            return '/api/maintenance/restore', {'link': match.group(1)}
    restart_match = re.match(r'^(?:systemctl\s+restart\s+|service\s+restart\s+)?([A-Za-z0-9@._-]+)$', normalized)
    if restart_match and normalized.startswith('systemctl restart '):
        return '/api/maintenance/restart', {'service': restart_match.group(1)}
    enable_match = re.match(r'^systemctl\s+enable\s+--now\s+([A-Za-z0-9@._-]+)$', normalized)
    if enable_match:
        return '/api/maintenance/enable', {'service': enable_match.group(1)}
    return None

try:
    with open("kyt/database.db", "rb"):
        pass
except OSError:
    x = sqlite3.connect("kyt/database.db")
    c = x.cursor()
    c.execute("CREATE TABLE admin (user_id)")
    c.execute("INSERT INTO admin (user_id) VALUES (?)",(ADMIN,))
    x.commit()

def get_db():
    x = sqlite3.connect("kyt/database.db", check_same_thread=False)
    x.row_factory = sqlite3.Row
    return x

def valid(id):
    db = get_db()
    try:
        x = db.execute("SELECT user_id FROM admin").fetchall()
        a = [v[0] for v in x]
        if id in a:
            return "true"
        else:
            return "false"
    finally:
        db.close()

def validate_username(username):
    """Validasi username: hanya huruf, angka, underscore, hyphen (max 32 karakter)"""
    return bool(re.match(r'^[a-zA-Z0-9_-]{1,32}$', username))

def clean_username(raw):
    """Bersihkan username dari input chat; kembalikan None bila tidak valid.

    Whitelist ketat (huruf/angka/_/-, maks 32) sehingga aman dipakai di
    perintah shell maupun path file — anti command injection & path traversal."""
    u = (raw or "").replace(" ", "")
    return u if validate_username(u) else None

# ── BATCH-2 SECURITY HELPERS ──────────────────────────────────────────
# Helper anti command-injection / crash untuk dipakai semua modul.

def safe_ip_info():
    """Info IP publik via ip-api.com; tidak pernah raise (kembalikan default)."""
    default = {"query": "-", "country": "-", "city": "-", "isp": "-"}
    try:
        r = requests.get("http://ip-api.com/json/?fields=query,country,city,isp", timeout=10)
        d = r.json()
        if not isinstance(d, dict):
            return default
        return {
            "query": str(d.get("query", "-")),
            "country": str(d.get("country", "-")),
            "city": str(d.get("city", "-")),
            "isp": str(d.get("isp", "-")),
        }
    except Exception:
        return default

def safe_shell_count(cmd, timeout=10):
    """Jalankan perintah hitung akun; kembalikan '?' bila gagal (anti crash)."""
    try:
        return subprocess.check_output(cmd, shell=True, timeout=timeout).decode("ascii").strip()
    except Exception:
        return "?"

def config_user_exists(path, user):
    """Cek pola '^#& user ' di file config TANPA shell (pengganti aman
    untuk: grep "^#& {user} " file). user harus sudah lolos clean_username."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            prefix = "#& " + user + " "
            for line in f:
                if line.startswith(prefix):
                    return True
        return False
    except OSError:
        return False

def passwd_user_exists(user):
    """Cek '^user:' di /etc/passwd TANPA shell (pengganti aman
    untuk: grep -E "^{user}:" /etc/passwd)."""
    try:
        with open("/etc/passwd", "r", encoding="utf-8", errors="replace") as f:
            prefix = user + ":"
            for line in f:
                if line.startswith(prefix):
                    return True
        return False
    except OSError:
        return False

def read_detail_file(service, user):
    """Baca /var/www/html/{service}-{user}.txt TANPA shell.
    Kembalikan isi (str) atau '' bila tidak ada / tidak valid."""
    u = clean_username(user)
    if not u:
        return ""
    path = f"/var/www/html/{service}-{u}.txt"
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""

def extract_vpn_links(api_output, proto):
    """Ekstrak config-link dari output API dengan aman.
    Kembalikan list (bisa kosong) — tidak pernah raise."""
    try:
        text = api_output or ""
        return [m.group() for m in re.finditer(rf"{re.escape(proto)}://(.*)", text)]
    except Exception:
        return []

def extract_link_field(link, pattern, default="-"):
    """Ambil satu field dari config-link via regex dengan aman."""
    try:
        m = re.search(pattern, link or "")
        return m.group(1) if m else default
    except Exception:
        return default

def decode_vmess_payload(link):
    """Decode payload base64 dari link vmess:// dengan aman; None bila gagal."""
    try:
        raw = (link or "").replace("vmess://", "")
        return base64.b64decode(raw).decode("ascii")
    except Exception:
        return None

def schedule_trial_kill(svc, username, minutes=60):
    """Jadwalkan penghapusan akun trial setelah `minutes` menit.
    Pakai `at` bila tersedia; fallback asyncio. Tidak pernah raise."""
    proto = {'ssh': 'ssh', 'vmess': 'vmess', 'vless': 'vless',
             'trojan': 'trojan', 'shadowsocks': 'shadowsocks'}.get(svc, svc)
    mins = max(1, int(minutes))
    try:
        if shutil.which("at"):
            r = subprocess.run(
                f'echo "killtrial {proto} {shlex.quote(username)}" | at now + {mins} minutes',
                shell=True, timeout=10)
            if r.returncode == 0:
                return True
    except Exception:
        pass
    async def _later():
        await asyncio.sleep(mins * 60)
        try:
            api_delete_account(svc, username, timeout=30)
        except Exception:
            pass
    try:
        asyncio.create_task(_later())
    except Exception:
        pass
    return False

def validate_domain(domain):
    """Validasi hostname/domain ketat; kembalikan domain bersih atau None."""
    d = (domain or "").strip().lower()
    if not d or len(d) > 253:
        return None
    if not re.match(r'^[a-z0-9]([a-z0-9.-]{0,251}[a-z0-9])?$', d):
        return None
    if '..' in d or d.startswith('-') or d.startswith('.'):
        return None
    return d

def validate_backup_link(link):
    """Validasi link backup: harus URL http(s) tanpa karakter shell berbahaya."""
    l = (link or "").strip()
    if not l or len(l) > 2048:
        return None
    if not re.match(r'^https?://', l):
        return None
    if re.search(r'[\s\'"`;|&$()<>\\]', l):
        return None
    return l

def validate_ipv4(ip):
    """Validasi IPv4 ketat; kembalikan IP bersih atau None."""
    i = (ip or "").strip()
    parts = i.split(".")
    if len(parts) != 4:
        return None
    for p in parts:
        if not p.isdigit() or not 0 <= int(p) <= 255:
            return None
        if len(p) > 1 and p.startswith("0"):
            return None
    return i

def validate_token_simple(token):
    """Validasi token API sederhana: alfanumerik + - _ . (maks 128)."""
    t = (token or "").strip()
    return t if re.match(r'^[A-Za-z0-9._-]{8,128}$', t) else None

def is_valid_sqlite(path, max_size_mb=100):
    """Validasi file adalah database SQLite yang wajar.
    Kembalikan True bila: ukuran wajar, header 'SQLite format 3', dan
    bisa dibuka + punya tabel inti bot."""
    try:
        size = os.path.getsize(path)
        if size <= 0 or size > max_size_mb * 1024 * 1024:
            return False
        with open(path, "rb") as f:
            header = f.read(16)
        if header != b"SQLite format 3\x00":
            return False
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5)
        try:
            tables = {r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
        finally:
            con.close()
        return "admin" in tables
    except Exception:
        return False

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def _cleanup_old_qr(max_age=3600):
    """Hapus file QR sementara di /tmp yang lebih tua dari max_age detik."""
    try:
        now = time.time()
        for f in os.listdir("/tmp"):
            if f.startswith("kyt_qr_"):
                fp = os.path.join("/tmp", f)
                try:
                    if os.path.isfile(fp) and now - os.path.getmtime(fp) > max_age:
                        os.unlink(fp)
                except OSError:
                    pass
    except OSError:
        pass

def generate_qr(data, label="qr"):
    if not data:
        return None
    _cleanup_old_qr()
    path = f"/tmp/kyt_qr_{label}_{random.randint(10000,99999)}.png"
    try:
        import qrcode
        img = qrcode.make(data, image_factory=qrcode.image.pil.PilImage)
        img.save(path, format="PNG")
        if os.path.getsize(path) > 0:
            return path
    except Exception as e:
        try:
            os.unlink(path)
        except:
            pass
    try:
        import urllib.parse
        encoded = urllib.parse.quote(data, safe="")
        r = requests.get(f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={encoded}", timeout=30)
        if r.status_code == 200 and r.content:
            with open(path, 'wb') as f:
                f.write(r.content)
            return path
    except Exception as e:
        pass
    return None


def download_qr_image(url, label="qris"):
    path = f"/tmp/kyt_qr_{label}_{random.randint(10000,99999)}.png"
    _cleanup_old_qr()
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200 and r.content:
            with open(path, 'wb') as f:
                f.write(r.content)
            return path
    except:
        pass
    return None

# ── USER PANEL DATABASE ───────────────────────────────────────────────
def _init_user_tables():
    _db = sqlite3.connect("kyt/database.db")
    _db.execute("""CREATE TABLE IF NOT EXISTS user_balance (
        telegram_id TEXT PRIMARY KEY,
        balance REAL DEFAULT 0,
        tg_username TEXT DEFAULT '',
        joined_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    _db.execute("""CREATE TABLE IF NOT EXISTS user_services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT NOT NULL,
        service TEXT NOT NULL,
        username TEXT NOT NULL,
        expired_at TEXT,
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    _db.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    _db.execute("""CREATE TABLE IF NOT EXISTS service_prices (
        service TEXT NOT NULL,
        duration INTEGER NOT NULL,
        price REAL NOT NULL,
        PRIMARY KEY (service, duration)
    )""")
    for svc in ['ssh','vmess','vless','trojan','shadowsocks']:
        for dur, price in [(1,1000),(7,3000),(15,5000),(30,10000)]:
            _db.execute("INSERT OR IGNORE INTO service_prices VALUES (?,?,?)", (svc, dur, price))
    _db.commit()
    _db.close()

_init_user_tables()

def format_rupiah(amount):
    return f"Rp {int(amount):,}".replace(',','.')

def ensure_user_exists(telegram_id, tg_username=''):
    db = get_db()
    try:
        db.execute("INSERT OR IGNORE INTO user_balance (telegram_id, tg_username) VALUES (?,?)",
            (str(telegram_id), tg_username))
        if tg_username:
            db.execute("UPDATE user_balance SET tg_username=? WHERE telegram_id=?",
                (tg_username, str(telegram_id)))
        db.commit()
    finally:
        db.close()

def get_balance(telegram_id):
    db = get_db()
    try:
        row = db.execute("SELECT balance FROM user_balance WHERE telegram_id=?", (str(telegram_id),)).fetchone()
        return float(row['balance']) if row else 0.0
    finally:
        db.close()

def add_balance(telegram_id, amount, description="Top Up"):
    db = get_db()
    try:
        db.execute("INSERT OR IGNORE INTO user_balance (telegram_id) VALUES (?)", (str(telegram_id),))
        db.execute("UPDATE user_balance SET balance=balance+? WHERE telegram_id=?", (amount, str(telegram_id)))
        db.execute("INSERT INTO transactions (telegram_id,type,amount,description) VALUES (?,'topup',?,?)",
            (str(telegram_id), amount, description))
        db.commit()
    finally:
        db.close()

def deduct_balance(telegram_id, amount, description="Pembelian"):
    db = get_db()
    try:
        cur = db.execute(
            "UPDATE user_balance SET balance=balance-? WHERE telegram_id=? AND balance>=?",
            (amount, str(telegram_id), amount))
        if cur.rowcount == 0:
            db.rollback()
            return False
        db.execute("INSERT INTO transactions (telegram_id,type,amount,description) VALUES (?,'purchase',?,?)",
            (str(telegram_id), amount, description))
        db.commit()
        return True
    finally:
        db.close()

def get_user_services(telegram_id):
    db = get_db()
    try:
        return db.execute("SELECT * FROM user_services WHERE telegram_id=? ORDER BY created_at DESC",
            (str(telegram_id),)).fetchall()
    finally:
        db.close()

def get_service_prices(service):
    db = get_db()
    try:
        return db.execute("SELECT duration, price FROM service_prices WHERE service=? ORDER BY duration",
            (service,)).fetchall()
    finally:
        db.close()

# ── TRIAL SYSTEM ─────────────────────────────────────────────────────
def _init_trial_table():
    _db = sqlite3.connect("kyt/database.db")
    _db.execute("""CREATE TABLE IF NOT EXISTS trial_claims (
        telegram_id TEXT NOT NULL,
        claim_date TEXT NOT NULL,
        service TEXT NOT NULL,
        username TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now','localtime')),
        PRIMARY KEY (telegram_id, claim_date)
    )""")
    _db.commit()
    _db.close()

_init_trial_table()

# ── REMOTE API SERVERS ─────────────────────────────────────────────────
def _init_remote_servers_table():
    _db = sqlite3.connect("kyt/database.db")
    _db.execute("""CREATE TABLE IF NOT EXISTS remote_servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        url TEXT NOT NULL,
        token TEXT NOT NULL,
        status TEXT DEFAULT 'unknown',
        created_at TEXT DEFAULT (datetime('now','localtime'))
    )""")
    _db.commit()
    _db.close()

_init_remote_servers_table()

def get_remote_servers():
    db = get_db()
    try:
        return db.execute("SELECT * FROM remote_servers ORDER BY name ASC").fetchall()
    finally:
        db.close()

def get_remote_server(sid):
    db = get_db()
    try:
        return db.execute("SELECT * FROM remote_servers WHERE id=?", (sid,)).fetchone()
    finally:
        db.close()

def add_remote_server(name, url, token):
    db = get_db()
    try:
        db.execute("INSERT INTO remote_servers (name,url,token) VALUES (?,?,?)", (name, url, token))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        db.close()

def delete_remote_server(sid):
    db = get_db()
    try:
        db.execute("DELETE FROM remote_servers WHERE id=?", (sid,))
        db.commit()
    finally:
        db.close()

def update_remote_server_status(sid, status):
    db = get_db()
    try:
        db.execute("UPDATE remote_servers SET status=? WHERE id=?", (status, sid))
        db.commit()
    finally:
        db.close()

def api_call_remote(server_id, endpoint, payload, timeout=60, no_notif=True):
    s = get_remote_server(server_id)
    if not s:
        raise ValueError("Remote server not found")
    base = s["url"].rstrip("/")
    headers = {
        "X-API-Token": s["token"],
        "Content-Type": "application/json",
    }
    if no_notif:
        payload = dict(payload)
        payload["no_notif"] = True
    try:
        resp = requests.post(f"{base}{endpoint}", json=payload, headers=headers, timeout=timeout)
        data = resp.json()
        if not data.get("ok"):
            msg = data.get("stderr") or data.get("error") or "remote api error"
            raise subprocess.CalledProcessError(
                data.get("returncode", resp.status_code), endpoint,
                output=data.get("stdout", ""), stderr=msg,
            )
        return data.get("stdout", "") or data.get("account_text", "")
    except requests.exceptions.RequestException as e:
        raise subprocess.CalledProcessError(-1, endpoint, stderr=str(e))

def test_remote_server(sid):
    s = get_remote_server(sid)
    if not s:
        return {"ok": False, "error": "Server not found"}
    try:
        resp = requests.get(f"{s['url'].rstrip('/')}/api/health", headers={"X-API-Token": s["token"]}, timeout=10)
        data = resp.json()
        if data.get("ok"):
            update_remote_server_status(sid, "online")
            return {"ok": True}
        else:
            update_remote_server_status(sid, "offline")
            return {"ok": False, "error": data.get("error", "unknown")}
    except Exception as e:
        update_remote_server_status(sid, "offline")
        return {"ok": False, "error": str(e)}

def can_claim_trial(telegram_id):
    today = DT.date.today().isoformat()
    db = get_db()
    try:
        row = db.execute("SELECT 1 FROM trial_claims WHERE telegram_id=? AND claim_date=?",
            (str(telegram_id), today)).fetchone()
        return row is None
    finally:
        db.close()

def record_trial_claim(telegram_id, service, username):
    """Catat klaim trial. Kembalikan True bila klaim baru, False bila sudah
    pernah klaim hari ini (atomik, anti race condition double-claim)."""
    today = DT.date.today().isoformat()
    db = get_db()
    try:
        cur = db.execute("INSERT OR IGNORE INTO trial_claims (telegram_id, claim_date, service, username) VALUES (?,?,?,?)",
            (str(telegram_id), today, service, username))
        db.commit()
        return cur.rowcount > 0
    finally:
        db.close()

def build_trial_cmd(svc, username, password, limit_ip):
    u = shlex.quote(username)
    p = shlex.quote(password)
    l = shlex.quote(limit_ip)
    cmds = {
        'ssh':         f'printf "%s\\n" {u} {p} {l} 1 "" | addssh',
        'vmess':       f'printf "%s\\n" {u} {l} 100 1 "" | addws',
        'vless':       f'printf "%s\\n" {u} {l} 100 1 "" | addvless',
        'trojan':      f'printf "%s\\n" {u} {l} 100 1 "" | addtr',
        'shadowsocks': f'printf "%s\\n" {u} {l} 1 100 "" | addss',
    }
    return cmds.get(svc, '')

TRIAL_SCRIPT = {
    'ssh': 'ssh', 'vmess': 'vmess', 'vless': 'vless',
    'trojan': 'trojan', 'shadowsocks': 'shadowsocks',
}
