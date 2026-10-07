#!/usr/bin/env python3
"""vpnstore — halaman penjualan akun VPN (SSH / Xray) untuk pemilik script WendyVpn.

Berjalan di VPS pemilik script (host sendiri). Pembayaran QRIS:
  - mode "own"   : pakai API key P2P milik sendiri (dana ke merchant sendiri)
  - mode "wendi" : perantara via QRIS Wendi (api.shifastore.my.id/api/reseller/order),
                   dana masuk ke Wendi, bagi hasil dicatat di gateway.
Setelah bayar lunas -> akun otomatis dibuat/di perpanjang via WENDY_API lokal (127.0.0.1:9000).
Admin: default admin/admin (wajib diganti), kelola harga & pesanan.
"""
import hashlib
import json
import os
import re
import secrets
import time
from functools import wraps

import requests
from flask import Flask, jsonify, request, send_from_directory, session

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.environ.get("VPNSTORE_CONFIG", os.path.join(BASE, "config.json"))
ORDERS_FILE = os.path.join(BASE, "orders.json")
GATEWAY = "https://api.shifastore.my.id"
WENDY_API = os.environ.get("WENDY_API_BASE", "http://127.0.0.1:9000")

SERVICES = [
    ("ssh", "SSH OVPN"),
    ("vmess", "VMess"),
    ("vless", "VLess"),
    ("trojan", "Trojan"),
    ("shadowsocks", "Shadowsocks"),
]
SVC = dict(SERVICES)
VALID_USER = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

app = Flask(__name__, template_folder=os.path.join(BASE, "templates"), static_folder=None)


def load_config():
    with open(CONFIG_FILE) as fh:
        cfg = json.load(fh)
    app.secret_key = cfg.get("secret_key") or "ganti-ini"
    return cfg


def save_config(cfg):
    tmp = CONFIG_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(cfg, fh, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, CONFIG_FILE)


def load_orders():
    try:
        with open(ORDERS_FILE) as fh:
            return json.load(fh)
    except Exception:
        return []


def save_orders(orders):
    tmp = ORDERS_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(orders, fh, indent=1)
    os.chmod(tmp, 0o600)
    os.replace(tmp, ORDERS_FILE)


def hash_pass(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.scrypt(pw.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"{salt}${h}"


def check_pass(pw, stored):
    try:
        salt, h = stored.split("$")
        return secrets.compare_digest(hash_pass(pw, salt).split("$")[1], h)
    except Exception:
        return False


def login_required(f):
    @wraps(f)
    def wrap(*a, **kw):
        if not session.get("admin"):
            return jsonify({"error": "Belum login."}), 401
        return f(*a, **kw)
    return wrap


# ---------------- pembayaran ----------------

def create_payment_own(cfg, amount, reference):
    r = requests.post(f"{GATEWAY}/api/payments",
                      headers={"X-API-Key": cfg["p2p_api_key"]},
                      json={"amount": amount, "reference": reference, "expiryMinutes": 60},
                      timeout=30)
    d = r.json()
    if r.status_code != 200 or not d.get("id"):
        raise RuntimeError(d.get("error") or "Gagal membuat pembayaran.")
    return {"upstream": "own:" + d["id"], "payment_id": d["id"],
            "qr_string": d.get("qrString"), "qr_image": d.get("qrImage") or d.get("qr_image"),
            "unique_amount": d.get("uniqueAmount"), "expires_at": d.get("expiresAt")}


def create_payment_wendi(cfg, seller, service, username, days, amount):
    r = requests.post(f"{GATEWAY}/api/reseller/order",
                      json={"seller": seller, "service": service, "username": username,
                            "days": days, "amount": amount},
                      timeout=30)
    d = r.json()
    if r.status_code != 200 or not d.get("order"):
        raise RuntimeError(d.get("error") or "Gagal membuat order perantara.")
    o = d["order"]
    return {"upstream": "wendi:" + o["id"], "payment_id": o["id"],
            "qr_string": d.get("qrString"), "qr_image": d.get("qrImage"),
            "unique_amount": d.get("uniqueAmount"), "expires_at": d.get("expiresAt")}


def check_upstream(cfg, upstream):
    kind, pid = upstream.split(":", 1)
    if kind == "own":
        r = requests.get(f"{GATEWAY}/api/payments/{pid}",
                         headers={"X-API-Key": cfg["p2p_api_key"]}, timeout=20)
        d = r.json()
        return d.get("status"), d
    r = requests.get(f"{GATEWAY}/api/reseller/order/{pid}", timeout=20)
    d = r.json()
    o = d.get("order") or {}
    return o.get("status"), o


# ---------------- provisioning akun ----------------

def provision(order):
    """Buat/perpanjang akun via WENDY_API lokal. Return dict detail akun."""
    data = {"service": order["service"], "username": order["username"],
            "days": str(order["days"])}
    if order["kind"] == "buy":
        url = f"{WENDY_API}/api/accounts/create"
        if order["service"] == "ssh":
            data["password"] = order["password"]
            data["limit_ip"] = "2"
        else:
            data["limit_ip"] = "2"
            data["quota"] = "100"
    else:
        url = f"{WENDY_API}/api/accounts/renew"
        if order["service"] in ("vmess", "vless", "trojan"):
            data["quota"] = "100"
            data["limit_ip"] = "2"
    r = requests.post(url, json=data, timeout=60)
    try:
        d = r.json()
    except Exception:
        d = {"raw": r.text[:2000]}
    return {"http": r.status_code, "result": d}


# ---------------- halaman publik ----------------

@app.get("/")
def index():
    return send_from_directory(os.path.join(BASE, "templates"), "store.html")


@app.get("/api/services")
def api_services():
    cfg = load_config()
    return jsonify({"store_name": cfg.get("store_name", "Toko VPN"),
                    "mode": cfg.get("mode", "own"),
                    "services": [{"id": s, "label": l} for s, l in SERVICES],
                    "prices": cfg.get("prices", {})})


@app.post("/api/order")
def api_order():
    cfg = load_config()
    b = request.get_json(force=True, silent=True) or {}
    kind = b.get("kind")
    service = str(b.get("service", "")).lower()
    username = str(b.get("username", "")).strip()
    password = str(b.get("password", "") or "")
    days = int(b.get("days") or 0)
    if kind not in ("buy", "renew"):
        return jsonify({"error": "Jenis order tidak valid."}), 400
    if service not in SVC:
        return jsonify({"error": "Layanan tidak dikenal."}), 400
    if not VALID_USER.match(username):
        return jsonify({"error": "Username 3-20 karakter (huruf, angka, underscore)."}), 400
    if kind == "buy" and service == "ssh" and len(password) < 3:
        return jsonify({"error": "Password SSH minimal 3 karakter."}), 400
    if kind == "renew" and service == "ssh" and len(password) < 3:
        # perpanjang SSH wajib tahu username + password (aturan pemilik)
        return jsonify({"error": "Perpanjang SSH wajib isi username + password."}), 400
    prices = cfg.get("prices", {}).get(service, {})
    price = prices.get(str(days))
    if not (price and price > 0):
        return jsonify({"error": "Paket durasi tidak tersedia."}), 400

    oid = "V" + secrets.token_hex(5).upper()
    ref = f"STORE-{oid}"
    try:
        if cfg.get("mode") == "wendi":
            pay = create_payment_wendi(cfg, cfg.get("seller_name", "toko"),
                                       service, username, days, price)
        else:
            if not cfg.get("p2p_api_key"):
                return jsonify({"error": "Toko belum dikonfigurasi (API key kosong)."}), 500
            pay = create_payment_own(cfg, price, ref)
    except Exception as e:
        return jsonify({"error": str(e)}), 502

    orders = load_orders()
    orders.append({"id": oid, "kind": kind, "service": service, "username": username,
                   "password": password if service == "ssh" else "",
                   "days": days, "amount": price,
                   "upstream": pay["upstream"], "status": "pending",
                   "created_at": int(time.time())})
    save_orders(orders[-500:])
    return jsonify({"order_id": oid, "qr_string": pay["qr_string"],
                    "qr_image": pay["qr_image"], "unique_amount": pay["unique_amount"],
                    "expires_at": pay["expires_at"], "amount": price})


@app.get("/api/order/<oid>")
def api_order_status(oid):
    cfg = load_config()
    orders = load_orders()
    o = next((x for x in orders if x["id"] == oid), None)
    if not o:
        return jsonify({"error": "Order tidak ditemukan."}), 404
    if o["status"] == "pending":
        try:
            status, _ = check_upstream(cfg, o["upstream"])
        except Exception as e:
            return jsonify({"order_id": oid, "status": "pending", "note": str(e)})
        if status == "paid":
            o["status"] = "paid"
            try:
                o["account"] = provision(o)
                o["status"] = "fulfilled"
            except Exception as e:
                o["provision_error"] = str(e)
            save_orders(orders)
        elif status in ("cancelled", "expired"):
            o["status"] = status
            save_orders(orders)
    out = {"order_id": oid, "status": o["status"], "kind": o["kind"],
           "service": o["service"], "service_label": SVC.get(o["service"]),
           "username": o["username"], "days": o["days"], "amount": o["amount"]}
    if o.get("account"):
        out["account"] = o["account"]
    if o.get("provision_error"):
        out["provision_error"] = o["provision_error"]
    return jsonify(out)


# ---------------- admin ----------------

@app.get("/admin")
def admin_page():
    return send_from_directory(os.path.join(BASE, "templates"), "admin.html")


LOGIN_HITS = {}


@app.post("/api/admin/login")
def admin_login():
    cfg = load_config()
    ip = request.headers.get("x-forwarded-for", request.remote_addr)
    arr = [t for t in LOGIN_HITS.get(ip, []) if time.time() - t < 300]
    if len(arr) >= 10:
        return jsonify({"error": "Terlalu banyak percobaan, tunggu 5 menit."}), 429
    b = request.get_json(force=True, silent=True) or {}
    if b.get("user") == cfg.get("admin_user", "admin") and check_pass(
            str(b.get("pass", "")), cfg.get("admin_pass_hash", "")):
        session["admin"] = True
        LOGIN_HITS.pop(ip, None)
        return jsonify({"ok": True})
    arr.append(time.time())
    LOGIN_HITS[ip] = arr
    return jsonify({"error": "Username/password salah."}), 401


@app.post("/api/admin/logout")
def admin_logout():
    session.pop("admin", None)
    return jsonify({"ok": True})


@app.get("/api/admin/orders")
@login_required
def admin_orders():
    return jsonify({"orders": load_orders()[-200:][::-1]})


@app.get("/api/admin/config")
@login_required
def admin_config():
    cfg = load_config()
    safe = {k: v for k, v in cfg.items() if k not in ("admin_pass_hash", "secret_key", "p2p_api_key")}
    safe["has_api_key"] = bool(cfg.get("p2p_api_key"))
    return jsonify({"config": safe, "services": [s for s, _ in SERVICES]})


@app.post("/api/admin/config")
@login_required
def admin_config_save():
    cfg = load_config()
    b = request.get_json(force=True, silent=True) or {}
    if "store_name" in b:
        cfg["store_name"] = str(b["store_name"])[:60]
    if b.get("mode") in ("own", "wendi"):
        cfg["mode"] = b["mode"]
    if "seller_name" in b and re.match(r"^[a-zA-Z0-9_.\-]{2,40}$", str(b["seller_name"] or "")):
        cfg["seller_name"] = str(b["seller_name"])
    if "p2p_api_key" in b and str(b["p2p_api_key"]).strip():
        cfg["p2p_api_key"] = str(b["p2p_api_key"]).strip()
    if isinstance(b.get("prices"), dict):
        clean = {}
        for svc, vals in b["prices"].items():
            if svc not in SVC or not isinstance(vals, dict):
                continue
            clean[svc] = {str(int(k)): int(v) for k, v in vals.items()
                          if str(k).isdigit() and int(v) > 0}
        cfg["prices"] = clean
    save_config(cfg)
    return jsonify({"ok": True})


@app.post("/api/admin/password")
@login_required
def admin_password():
    cfg = load_config()
    b = request.get_json(force=True, silent=True) or {}
    if not check_pass(str(b.get("old", "")), cfg.get("admin_pass_hash", "")):
        return jsonify({"error": "Password lama salah."}), 400
    new = str(b.get("new", ""))
    if len(new) < 4:
        return jsonify({"error": "Password baru minimal 4 karakter."}), 400
    cfg["admin_pass_hash"] = hash_pass(new)
    if b.get("user"):
        cfg["admin_user"] = str(b["user"])[:30]
    save_config(cfg)
    return jsonify({"ok": True})


if __name__ == "__main__":
    cfg = load_config()
    app.run(host="127.0.0.1", port=int(cfg.get("port", 8091)))
