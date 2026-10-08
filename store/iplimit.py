"""Modul batas IP: baca limit, hitung IP terpakai, dan banned.

Dipakai oleh store/app.py (tampilan admin) dan limitwatch.py (auto-banned).
"""
import json
import os
import re
import subprocess

LIMIT_BASE = "/etc/kyt/limit"
XRAY_ACCESS = "/var/log/xray/access.log"
XRAY_CONFIG = "/etc/xray/config.json"
LOCK_DB = "/etc/xray/.lock.db"
SERVICES = ("ssh", "vmess", "vless", "trojan", "shadowsocks")

# marker awal blok akun di /etc/xray/config.json per protokol
XRAY_MARKERS = {
    "vmess": ("### ",),
    "vless": ("#& ",),
    "trojan": ("#! ",),
    "shadowsocks": ("#!! ", "#&! "),
}


def _read_tail(path, lines=1000):
    try:
        with open(path, "rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            block = 8192
            data = b""
            while len(data.split(b"\n")) <= lines + 1 and size > 0:
                step = min(block, size)
                size -= step
                fh.seek(size)
                data = fh.read(step) + data
            return data.decode("utf-8", "replace").splitlines()[-lines:]
    except (OSError, IOError):
        return []


def get_limits():
    """{service: {user: limit}} dari /etc/kyt/limit/*/ip/"""
    out = {}
    for svc in SERVICES:
        d = os.path.join(LIMIT_BASE, svc, "ip")
        users = {}
        if os.path.isdir(d):
            for u in os.listdir(d):
                try:
                    with open(os.path.join(d, u)) as fh:
                        users[u.strip()] = int(fh.read().strip() or 0)
                except (OSError, ValueError):
                    continue
        out[svc] = users
    return out


def ssh_current_ips(user, lines=1500):
    """IP unik dari login sukses terakhir di auth.log."""
    ips = set()
    for path in ("/var/log/auth.log", "/var/log/secure"):
        for line in _read_tail(path, lines):
            m = re.search(r"Password auth succeeded for '([^']+)' from (\d+\.\d+\.\d+\.\d+)", line)
            if not m:
                m = re.search(r"Accepted (?:password|publickey) for (\S+) from (\d+\.\d+\.\d+\.\d+)", line)
            if m and m.group(1) == user:
                ips.add(m.group(2))
    return sorted(ips)


def xray_current_ips(user, lines=1000):
    """IP unik dari access.log xray untuk email=user."""
    ips = set()
    for line in _read_tail(XRAY_ACCESS, lines):
        m = re.search(r"\[([^\]]+)\]\s*$", line)
        if not m or m.group(1) != user:
            continue
        m2 = re.search(r"(\d+\.\d+\.\d+\.\d+):\d+", line)
        if m2:
            ips.add(m2.group(1))
    return sorted(ips)


def current_ips(svc, user):
    if svc == "ssh":
        return ssh_current_ips(user)
    return xray_current_ips(user)


def is_banned_ssh(user):
    try:
        r = subprocess.run(["passwd", "-S", user], capture_output=True, text=True, timeout=10)
        parts = r.stdout.split()
        return len(parts) > 1 and parts[1] == "L"
    except Exception:
        return False


def banned_xray_users():
    users = set()
    try:
        with open(LOCK_DB) as fh:
            for line in fh:
                m = re.match(r"^(?:###|#&|#!|#!!|#&!)\s+(\S+)", line.strip())
                if m:
                    users.add(m.group(1))
    except OSError:
        pass
    return users


def ban_ssh(user):
    subprocess.run(["passwd", "-l", user], timeout=15)


def ban_xray(svc, user):
    """Hapus akun dari config xray + catat di lock.db + restart xray."""
    markers = XRAY_MARKERS.get(svc, ())
    try:
        with open(XRAY_CONFIG) as fh:
            clines = fh.readlines()
    except OSError:
        return False
    out, skip, removed, exp = [], False, False, ""
    for line in clines:
        s = line.strip()
        if not skip:
            for mk in markers:
                if s.startswith(mk):
                    parts = s.split()
                    if len(parts) >= 2 and parts[1] == user:
                        skip = True
                        removed = True
                        if len(parts) >= 3:
                            exp = parts[2]
                        break
            if skip:
                continue
        else:
            if s == "},{":  # akhir blok inbound user
                skip = False
            continue
        out.append(line)
    if not removed:
        return False
    with open(XRAY_CONFIG, "w") as fh:
        fh.writelines(out)
    try:
        with open(LOCK_DB, "a") as fh:
            fh.write(f"{markers[0]}{user} {exp} banned-by-limitwatch\n")
    except OSError:
        pass
    subprocess.run(["systemctl", "restart", "xray"], timeout=60)
    return True


def unban_ssh(user):
    r = subprocess.run(["passwd", "-u", user], capture_output=True, text=True, timeout=15)
    return r.returncode == 0


def tracking():
    """Data untuk admin: [{service,user,limit,ips,count,banned}]"""
    limits = get_limits()
    bx = banned_xray_users()
    rows = []
    for svc in SERVICES:
        for user, limit in sorted(limits[svc].items()):
            ips = current_ips(svc, user)
            banned = is_banned_ssh(user) if svc == "ssh" else (user in bx)
            rows.append({
                "service": svc, "user": user, "limit": limit,
                "ips": ips, "count": len(ips), "banned": banned,
                "over": (not banned) and len(ips) > limit,
            })
    rows.sort(key=lambda r: (not r["over"], not r["banned"], r["service"], r["user"]))
    return rows
