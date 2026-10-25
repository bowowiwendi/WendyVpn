#!/usr/bin/env python3
"""trial-killer: lapis kedua penghapus trial 1 jam, independen dari proses bot.

Dijalankan cron tiap 5 menit. Membaca vpn_accounts di DB bot, mencari
trial (is_trial=1) yang trial_expires_at-nya sudah lewat (UTC, sama seperti
sweeper bot), lalu menghapusnya lewat VPN API lokal (127.0.0.1:5888).

JAMINAN yang tidak dimiliki sweeper bot lama:
- Baris DB HANYA dihapus setelah penghapusan di server TERVERIFIKASI
  (SSH: user sistem sudah tidak ada; Xray: baris '### username' sudah
  tidak ada di /etc/xray/config.json). Kalau verifikasi gagal, baris
  dipertahankan dan dicoba lagi di run berikutnya, jadi trial tidak
  pernah 'dianggap mati' padahal masih hidup di server.
- Berjalan lewat cron, jadi tetap jalan walau proses bot sedang mati.

Log: /var/log/trial-killer.log
Pemakaian: trial-killer.py <path-bot.db>  (mis. /root/wendi-bot-js/data/bot.db)
Auth API dibaca dari <bot-dir>/.env (VPN_API_AUTH), tanpa ditampilkan.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

API_BASE = "http://127.0.0.1:5888"
XRAY_CONFIG = "/etc/xray/config.json"
LOG_FILE = "/var/log/trial-killer.log"


def log(msg):
    line = "%s %s" % (datetime.now(timezone(timedelta(hours=7))).strftime("%Y-%m-%d %H:%M:%S WIB"), msg)
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_api_auth(db_path):
    bot_dir = os.path.dirname(os.path.dirname(os.path.abspath(db_path)))
    env_path = os.path.join(bot_dir, ".env")
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("VPN_API_AUTH="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def api_delete(proto, user, auth):
    params = urllib.parse.urlencode({"auth": auth, "proto": proto, "user": user})
    req = urllib.request.Request(API_BASE + "/delete?" + params, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode() or "{}")
            return data.get("status", "success") == "success", data
    except Exception as e:
        return False, {"error": str(e)}


def server_account_gone(proto, username):
    if proto == "zivpn":
        # Zivpn tidak terpasang di server: tidak ada akun server untuk dibunuh.
        return True
    if proto == "ssh":
        r = subprocess.run(["id", username], capture_output=True)
        return r.returncode != 0
    # VMess/VLess/Trojan/Shadowsocks: klien Xray ditandai '### username '
    try:
        with open(XRAY_CONFIG) as f:
            cfg = f.read()
        return re.search(r"^### " + re.escape(username) + r"( |$)", cfg, re.M) is None
    except Exception:
        return False


def main():
    if len(sys.argv) < 2:
        print("usage: trial-killer.py <bot.db>", file=sys.stderr)
        return 2
    db_path = sys.argv[1]
    auth = read_api_auth(db_path)
    try:
        con = sqlite3.connect(db_path)
        rows = con.execute(
            "SELECT proto, username FROM vpn_accounts "
            "WHERE is_trial = 1 AND trial_expires_at IS NOT NULL "
            "AND trial_expires_at < datetime('now')"
        ).fetchall()
    except Exception as e:
        log("ERROR baca DB %s: %s" % (db_path, e))
        return 1
    if not rows:
        return 0
    for proto, username in rows:
        ok, data = api_delete(proto, username, auth)
        if not ok:
            log("API-FAIL %s/%s dipertahankan, coba lagi run berikutnya: %s" % (proto, username, data))
            continue
        if not server_account_gone(proto, username):
            log("VERIFY-FAIL %s/%s masih ada di server, dipertahankan" % (proto, username))
            continue
        try:
            con.execute("DELETE FROM vpn_accounts WHERE username = ? AND proto = ?", (username, proto))
            con.commit()
            log("DELETED %s/%s" % (proto, username))
        except Exception as e:
            log("ERROR hapus DB %s/%s: %s" % (proto, username, e))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
