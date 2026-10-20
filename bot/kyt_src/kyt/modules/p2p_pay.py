# Modul pembayaran QRIS via P2P Gateway (pengganti bayar.gg).
# Setiap pemilik bot memakai API Key tenant MILIKNYA SENDIRI (p2p_...) dari
# https://p2p.shifastore.my.id — dana top-up masuk ke akun GoPay Merchant
# masing-masing, bukan ke admin script.
# DEFAULT: bila pemilik bot BELUM punya QRIS/API key, pembayaran otomatis
# lewat QRIS Wendi sebagai perantara (bagi hasil, dicatat di gateway).
from kyt import *
import asyncio
import re

API_BASE = "https://api.shifastore.my.id"

try:
    P2P_API_KEY
except NameError:
    P2P_API_KEY = ""
try:
    SELLER_NAME
except NameError:
    SELLER_NAME = ""

def _headers():
    return {"X-API-Key": P2P_API_KEY}

def _via_wendi():
    """True bila mode perantara (pemilik bot tanpa API key sendiri)."""
    return not P2P_API_KEY

def _seller():
    s = str(SELLER_NAME or "").strip() or "bot"
    return re.sub(r"[^a-zA-Z0-9_.-]", "", s)[:40] or "bot"

def _create_via_wendi(amount, user):
    """Buat order perantara via QRIS master (Wendi)."""
    try:
        amount = int(amount)
    except:
        return {"success": False, "error": "Nominal tidak valid"}
    payload = {
        "seller": _seller(),
        "service": "ssh",
        "username": ("tg" + re.sub(r"\D", "", str(user or ""))[:15]) or "tg0",
        "days": 30,
        "amount": amount,
    }
    try:
        r = requests.post(f"{API_BASE}/api/reseller/order", json=payload, timeout=30)
        d = r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    if not r.ok or not d.get("order"):
        return {"success": False, "error": d.get("error", f"HTTP {r.status_code}")}
    o = d["order"]
    qr_image = d.get("qrImage") or ""
    if qr_image.startswith("/"):
        qr_image = API_BASE + qr_image
    return {"success": True, "data": {
        "invoice_id": o["id"],
        "qris_dynamic_string": d.get("qrString", ""),
        "qris_dynamic_image_url": qr_image,
        "unique_amount": d.get("uniqueAmount", amount),
        "expires_at": d.get("expiresAt", ""),
        "via": "wendi",
    }}

def create_payment(amount, description, customer_name="", method="qris"):
    if _via_wendi():
        return _create_via_wendi(amount, customer_name)
    try:
        amount = int(amount)
    except:
        return {"success": False, "error": "Nominal tidak valid"}
    payload = {
        "amount": amount,
        "reference": str(description or "")[:64],
        "expiryMinutes": 30,
    }
    try:
        r = requests.post(f"{API_BASE}/api/payments", headers=_headers(), json=payload, timeout=30)
        d = r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    if not r.ok or not d.get("id"):
        return {"success": False, "error": d.get("error", f"HTTP {r.status_code}")}
    qr_image = d.get("qrImage") or ""
    if qr_image.startswith("/"):
        qr_image = API_BASE + qr_image
    return {"success": True, "data": {
        "invoice_id": d["id"],
        "qris_dynamic_string": d.get("qrString", ""),
        "qris_dynamic_image_url": qr_image,
        "unique_amount": d.get("uniqueAmount", amount),
        "expires_at": d.get("expiresAt", ""),
    }}

def check_payment(invoice_id):
    if str(invoice_id or "").startswith("RS"):
        # order perantara (via QRIS Wendi)
        try:
            r = requests.get(f"{API_BASE}/api/reseller/order/{invoice_id}", timeout=15)
            d = r.json()
        except Exception as e:
            return {"success": False, "error": str(e)}
        o = d.get("order") or {}
        if not o.get("id"):
            return {"success": False, "error": d.get("error", "Order tidak ditemukan")}
        return {"success": True, "status": o.get("status", "pending"),
                "final_amount": o.get("amount"), "paid_at": ""}
    if not P2P_API_KEY:
        return {"success": False, "error": "API Key P2P belum dikonfigurasi"}
    try:
        r = requests.get(f"{API_BASE}/api/payments/{invoice_id}", headers=_headers(), timeout=15)
        d = r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
    if not r.ok or not d.get("id"):
        return {"success": False, "error": d.get("error", f"HTTP {r.status_code}")}
    return {
        "success": True,
        "status": d.get("status", "pending"),
        "final_amount": d.get("uniqueAmount"),
        "paid_at": "",
    }

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
    cur = db.execute(
        "UPDATE pending_topups SET status='paid', checked_at=datetime('now','localtime') "
        "WHERE invoice_id=? AND status='pending'",
        (invoice_id,)
    )
    db.commit()
    return cur.rowcount > 0

def mark_expired(invoice_id):
    db = get_db()
    db.execute(
        "UPDATE pending_topups SET status='expired', checked_at=datetime('now','localtime') WHERE invoice_id=?",
        (invoice_id,)
    )
    db.commit()

def claim_paid_topup(invoice_id, credit_amount):
    """Tandai invoice lunas DAN kredit saldo dalam SATU transaksi atomik.

    Kembalikan (telegram_id, credit_amount) bila klaim berhasil, atau None
    bila invoice sudah tidak pending (sudah diproses / duplikat).
    Crash di tengah jalan tidak bisa menyebabkan 'sudah bayar tapi saldo
    tidak masuk' karena keduanya commit bersamaan."""
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT telegram_id, amount FROM pending_topups WHERE invoice_id=? AND status='pending'",
            (invoice_id,)).fetchone()
        if not row:
            db.rollback()
            return None
        tid = row["telegram_id"]
        try:
            credit = float(credit_amount)
        except (TypeError, ValueError):
            credit = float(row["amount"])
        db.execute(
            "UPDATE pending_topups SET status='paid', checked_at=datetime('now','localtime') WHERE invoice_id=?",
            (invoice_id,))
        db.execute("INSERT OR IGNORE INTO user_balance (telegram_id) VALUES (?)", (tid,))
        db.execute("UPDATE user_balance SET balance=balance+? WHERE telegram_id=?", (credit, tid))
        db.execute("INSERT INTO transactions (telegram_id,type,amount,description) VALUES (?,'topup',?,?)",
            (tid, credit, f"Top Up via QRIS ({invoice_id})"))
        db.commit()
        return tid, credit
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        raise

async def payment_poller():
    while True:
        await asyncio.sleep(5)
        try:
            pending = get_pending()
            for p in pending:
                res = check_payment(p["invoice_id"])
                if not res.get("success"):
                    continue
                status = res.get("status", "pending")
                if status == "paid":
                    # Kredit sebesar nominal unik yang benar-benar dibayar
                    credit_amount = res.get("final_amount") or p["amount"]
                    pay_method = "QRIS"
                    # Klaim atomik: tandai lunas + kredit saldo dalam 1 transaksi.
                    # Hanya invoice yang masih 'pending' yang dikreditkan (anti dobel).
                    claimed = claim_paid_topup(p["invoice_id"], credit_amount)
                    if not claimed:
                        continue
                    tid, amount = claimed
                    try:
                        notif = (
                            f"✅ **Top Up Berhasil!**\n\n"
                            f"💰 Nominal: `{format_rupiah(amount)}`\n"
                            f"💳 Metode: `{pay_method}`\n"
                            f"📄 Invoice: `{p['invoice_id']}`\n"
                            f"💵 Saldo: `{format_rupiah(get_balance(tid))}`"
                        )
                        await bot.send_message(int(tid), notif)
                    except:
                        pass
                elif status in ("expired", "cancelled"):
                    mark_expired(p["invoice_id"])
        except:
            pass

def cancel_payment(invoice_id):
    """Batalkan pembayaran. Order perantara (RS...) tidak bisa dibatalkan
    via API (tanpa key master) — order kedaluwarsa otomatis 60 menit."""
    if str(invoice_id or "").startswith("RS"):
        return {"success": True, "skipped": True}
    if not P2P_API_KEY:
        return {"success": False, "error": "API Key P2P belum dikonfigurasi"}
    try:
        r = requests.post(f"{API_BASE}/api/payments/{invoice_id}/cancel",
                          headers=_headers(), timeout=15)
        return {"success": r.ok}
    except Exception as e:
        return {"success": False, "error": str(e)}
