from kyt import *
import asyncio

API_BASE = "https://www.bayar.gg/api"

try:
	BAYARGG_API_KEY
except NameError:
	BAYARGG_API_KEY = ""

try:
	CALLBACK_HOST
except NameError:
	CALLBACK_HOST = ""

def create_payment(amount, description, customer_name="", callback_url="", method="qris_bayar_gg"):
	if not BAYARGG_API_KEY:
		return {"success": False, "error": "API Key tidak dikonfigurasi"}
	payload = {
		"amount": amount,
		"description": description,
		"payment_method": method,
	}
	if customer_name:
		payload["customer_name"] = customer_name
	if callback_url:
		payload["callback_url"] = callback_url
	try:
		r = requests.post(
			f"{API_BASE}/create-payment.php",
			headers={"X-API-Key": BAYARGG_API_KEY},
			json=payload,
			timeout=30
		)
		return r.json()
	except Exception as e:
		return {"success": False, "error": str(e)}

def check_payment(invoice_id):
	if not BAYARGG_API_KEY:
		return {"success": False, "error": "API Key tidak dikonfigurasi"}
	try:
		r = requests.get(
			f"{API_BASE}/check-payment.php",
			headers={"X-API-Key": BAYARGG_API_KEY},
			params={"invoice": invoice_id},
			timeout=15
		)
		return r.json()
	except Exception as e:
		return {"success": False, "error": str(e)}

def _init_pending_tables():
	db = get_db()
	db.execute("""CREATE TABLE IF NOT EXISTS pending_topups (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		telegram_id TEXT NOT NULL,
		invoice_id TEXT NOT NULL UNIQUE,
		amount REAL NOT NULL,
		status TEXT DEFAULT 'pending',
		created_at TEXT DEFAULT (datetime('now','localtime')),
		checked_at TEXT
	)""")
	db.commit()

_init_pending_tables()

def add_pending(telegram_id, invoice_id, amount):
	db = get_db()
	db.execute(
		"INSERT OR IGNORE INTO pending_topups (telegram_id, invoice_id, amount) VALUES (?,?,?)",
		(str(telegram_id), invoice_id, amount)
	)
	db.commit()

def get_pending():
	db = get_db()
	return db.execute(
		"SELECT * FROM pending_topups WHERE status='pending' ORDER BY created_at ASC"
	).fetchall()

def mark_paid(invoice_id):
	db = get_db()
	db.execute(
		"UPDATE pending_topups SET status='paid', checked_at=datetime('now','localtime') WHERE invoice_id=?",
		(invoice_id,)
	)
	db.commit()

def mark_expired(invoice_id):
	db = get_db()
	db.execute(
		"UPDATE pending_topups SET status='expired', checked_at=datetime('now','localtime') WHERE invoice_id=?",
		(invoice_id,)
	)
	db.commit()

async def payment_poller():
	while True:
		await asyncio.sleep(15)
		if not BAYARGG_API_KEY:
			continue
		try:
			pending = get_pending()
			for p in pending:
				res = check_payment(p["invoice_id"])
				if not res.get("success"):
					continue
				status = res.get("status", "pending")
				if status == "paid":
					tid = p["telegram_id"]
					amount = p["amount"]
					final_amount = res.get("final_amount", amount)
					add_balance(tid, amount, f"Top Up via QRIS ({p['invoice_id']})")
					mark_paid(p["invoice_id"])
					try:
						await bot.send_message(int(tid),
							f"✅ **Top Up Berhasil!**\n\n"
							f"💰 `{format_rupiah(amount)}`\n"
							f"📄 Invoice: `{p['invoice_id']}`\n"
							f"💵 Saldo: `{format_rupiah(get_balance(tid))}`"
						)
					except:
						pass
				elif status in ("expired", "cancelled"):
					mark_expired(p["invoice_id"])
		except:
			pass
