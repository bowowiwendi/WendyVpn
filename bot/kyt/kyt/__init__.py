from telethon import *
import datetime as DT
from telethon import *
import requests,time,os,subprocess,re,sqlite3,sys,random,base64,json,math,shlex,asyncio
import logging
#usr/local/bin/kyt
logging.basicConfig(level=logging.INFO)
uptime = DT.datetime.now()

exec(open("kyt/var.txt","r").read())
bot = TelegramClient("ddsdswl","6","eb06d4abfb49dc3eeb1aeb98ae0f581e").start(bot_token=BOT_TOKEN)
try:
	open("kyt/database.db")
except:
	x = sqlite3.connect("kyt/database.db")
	c = x.cursor()
	c.execute("CREATE TABLE admin (user_id)")
	c.execute("INSERT INTO admin (user_id) VALUES (?)",(ADMIN,))
	x.commit()

def get_db():
	x = sqlite3.connect("kyt/database.db")
	x.row_factory = sqlite3.Row
	return x

def valid(id):
	db = get_db()
	x = db.execute("SELECT user_id FROM admin").fetchall()
	a = [v[0] for v in x]
	if id in a:
		return "true"
	else:
		return "false"

def validate_username(username):
	"""Validasi username: hanya huruf, angka, underscore, hyphen (max 32 karakter)"""
	return bool(re.match(r'^[a-zA-Z0-9_-]{1,32}$', username))

def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

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
		for dur, price in [(7,5000),(30,15000),(60,25000),(90,35000)]:
			_db.execute("INSERT OR IGNORE INTO service_prices VALUES (?,?,?)", (svc, dur, price))
	_db.commit()
	_db.close()

_init_user_tables()

def format_rupiah(amount):
	return f"Rp {int(amount):,}".replace(',','.')

def ensure_user_exists(telegram_id, tg_username=''):
	db = get_db()
	db.execute("INSERT OR IGNORE INTO user_balance (telegram_id, tg_username) VALUES (?,?)",
		(str(telegram_id), tg_username))
	if tg_username:
		db.execute("UPDATE user_balance SET tg_username=? WHERE telegram_id=?",
			(tg_username, str(telegram_id)))
	db.commit()

def get_balance(telegram_id):
	db = get_db()
	row = db.execute("SELECT balance FROM user_balance WHERE telegram_id=?", (str(telegram_id),)).fetchone()
	return float(row['balance']) if row else 0.0

def add_balance(telegram_id, amount, description="Top Up"):
	db = get_db()
	ensure_user_exists(telegram_id)
	db.execute("UPDATE user_balance SET balance=balance+? WHERE telegram_id=?", (amount, str(telegram_id)))
	db.execute("INSERT INTO transactions (telegram_id,type,amount,description) VALUES (?,'topup',?,?)",
		(str(telegram_id), amount, description))
	db.commit()

def deduct_balance(telegram_id, amount, description="Pembelian"):
	db = get_db()
	bal = get_balance(telegram_id)
	if bal < amount:
		return False
	db.execute("UPDATE user_balance SET balance=balance-? WHERE telegram_id=?", (amount, str(telegram_id)))
	db.execute("INSERT INTO transactions (telegram_id,type,amount,description) VALUES (?,'purchase',?,?)",
		(str(telegram_id), amount, description))
	db.commit()
	return True

def get_user_services(telegram_id):
	db = get_db()
	return db.execute("SELECT * FROM user_services WHERE telegram_id=? ORDER BY created_at DESC",
		(str(telegram_id),)).fetchall()

def get_service_prices(service):
	db = get_db()
	return db.execute("SELECT duration, price FROM service_prices WHERE service=? ORDER BY duration",
		(service,)).fetchall()
