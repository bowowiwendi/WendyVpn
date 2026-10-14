"""
Akun Saya Module for WendyVpn Bot
==================================
Port dari BotVPN2 (Aji) — user bisa lihat akun VPN miliknya sendiri.

Fitur:
- /akunsaya atau tombol "Akun Saya"
- Tampilkan daftar akun per protokol dengan paginasi
- Detail tiap akun (username, expiry, dll)

Catatan: bot Wendi adalah bot ADMIN (valid() check).
Modul ini menampilkan SEMUA akun dengan paginasi agar mudah dicari,
mengikuti pola BotVPN2 (tampilkanAkun dengan page).
"""
from kyt import *
import math

PER_PAGE = 10

# DB akun per protokol
ACCOUNT_DBS = [
    ("🔐 SSH", "/etc/ssh/.ssh.db"),
    ("📡 VMess", "/etc/xray/config.json"),
    ("🔷 VLess", "/etc/vless/.vless.db"),
    ("🔰 Trojan", "/etc/trojan/.trojan.db"),
    ("🌑 Shadowsocks", "/etc/shadowsocks/.shadowsocks.db"),
]


def _get_all_accounts():
    """Return list of (proto_label, user, expiry)."""
    accounts = []
    today = DT.date.today()
    for label, db_path in ACCOUNT_DBS:
        try:
            with open(db_path, "r") as f:
                content = f.read()
        except Exception:
            continue
        for line in content.splitlines():
            line = line.strip()
            if not line.startswith("###"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            user, expiry_str = parts[1], parts[2]
            try:
                expiry = DT.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                sisa = (expiry - today).days
                status = "✅" if sisa >= 0 else "❌"
            except Exception:
                sisa = "?"
                status = "❓"
            accounts.append((label, user, expiry_str, sisa, status))
    # Urut: yang mau expired dulu
    def _sort_key(a):
        try:
            return int(a[3])
        except Exception:
            return 9999
    accounts.sort(key=_sort_key)
    return accounts


def _render_page(accounts, page):
    total = len(accounts)
    pages = max(1, math.ceil(total / PER_PAGE))
    page = max(1, min(page, pages))
    start = (page - 1) * PER_PAGE
    chunk = accounts[start:start + PER_PAGE]

    lines = [f"👤 **DAFTAR AKUN** (hal {page}/{pages})\n"]
    lines.append(f"Total: **{total}** akun\n")
    for label, user, expiry, sisa, status in chunk:
        lines.append(f"{status} {label} `{user}`\n   └ Exp: `{expiry}` ({sisa} hari)")

    buttons = []
    nav = []
    if page > 1:
        nav.append(Button.inline("◀️", f"akun-page-{page-1}"))
    if page < pages:
        nav.append(Button.inline("▶️", f"akun-page-{page+1}"))
    if nav:
        buttons.append(nav)
    buttons.append([Button.inline("‹ Kembali", "menu")])
    return "\n".join(lines), buttons


@bot.on(events.CallbackQuery(data=b'akun-saya'))
@bot.on(events.NewMessage(pattern=r'^/akunsaya$'))
async def akun_saya(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        try:
            await event.answer("Akses Ditolak", alert=True)
        except Exception:
            await event.reply("Akses Ditolak")
        return
    accounts = _get_all_accounts()
    if not accounts:
        await event.respond("📭 Belum ada akun.",
                            buttons=[[Button.inline("‹ Kembali", "menu")]])
        return
    msg, buttons = _render_page(accounts, 1)
    try:
        await event.edit(msg, buttons=buttons)
    except Exception:
        await event.respond(msg, buttons=buttons)


@bot.on(events.CallbackQuery(pattern=r'^akun-page-(\d+)$'))
async def akun_saya_page(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    page = int(event.pattern_match.group(1))
    accounts = _get_all_accounts()
    msg, buttons = _render_page(accounts, page)
    await event.edit(msg, buttons=buttons)
