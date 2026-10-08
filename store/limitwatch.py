#!/usr/bin/env python3
"""Auto-banned pelanggar batas IP.

Dijalankan tiap 5 menit via systemd timer. Pelanggaran harus terlihat di
2x pengecekan beruntun sebelum di-banned (anti false-positive karena
pindah jaringan).
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iplimit

STATE_FILE = "/opt/vpnstore/limitwatch_state.json"
BANS_FILE = "/opt/vpnstore/bans.json"


def load_json(path, default):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def save_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh)
    os.replace(tmp, path)


def main():
    state = load_json(STATE_FILE, {})
    bans = load_json(BANS_FILE, [])
    limits = iplimit.get_limits()
    now = int(time.time())
    changed = False

    for svc in iplimit.SERVICES:
        for user, limit in limits[svc].items():
            if not limit or limit <= 0:
                continue
            banned = iplimit.is_banned_ssh(user) if svc == "ssh" else (user in iplimit.banned_xray_users())
            if banned:
                state.pop(f"{svc}:{user}", None)
                continue
            ips = iplimit.current_ips(svc, user)
            key = f"{svc}:{user}"
            if len(ips) > limit:
                prev = state.get(key)
                if prev and prev.get("ips") == ips:
                    # pelanggaran beruntun ke-2 -> banned
                    ok = False
                    try:
                        if svc == "ssh":
                            iplimit.ban_ssh(user)
                            ok = True
                        else:
                            ok = iplimit.ban_xray(svc, user)
                    except Exception:
                        ok = False
                    bans.append({"ts": now, "service": svc, "user": user,
                                 "ips": ips, "limit": limit, "banned": ok})
                    bans = bans[-200:]
                    state.pop(key, None)
                    changed = True
                else:
                    state[key] = {"ips": ips, "first": now}
                    changed = True
            else:
                if key in state:
                    state.pop(key, None)
                    changed = True

    save_json(STATE_FILE, state)
    save_json(BANS_FILE, bans)


if __name__ == "__main__":
    main()
