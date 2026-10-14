"""
Statistik Module for WendyVpn Bot
==================================
Port dari BotVPN2 (Aji) — dashboard statistik VPN.

Fitur:
- Total akun per protokol
- Akun aktif vs expired vs trial
- Info server (uptime, RAM, dll)
"""
from kyt import *

ACCOUNT_DBS = [
    ("🔐 SSH", "/etc/ssh/.ssh.db"),
    ("📡 VMess", "/etc/xray/config.json"),
    ("🔷 VLess", "/etc/vless/.vless.db"),
    ("🔰 Trojan", "/etc/trojan/.trojan.db"),
    ("🌑 Shadowsocks", "/etc/shadowsocks/.shadowsocks.db"),
]


def _count_accounts():
    today = DT.date.today()
    stats = {}
    for label, db_path in ACCOUNT_DBS:
        total = aktif = expired = trial = 0
        try:
            with open(db_path, "r") as f:
                content = f.read()
        except Exception:
            stats[label] = {"total": 0, "aktif": 0, "expired": 0, "trial": 0}
            continue
        for line in content.splitlines():
            line = line.strip()
            if not line.startswith("###"):
                continue
            parts = line.split()
            if len(parts) < 3:
                continue
            user, expiry_str = parts[1], parts[2]
            total += 1
            if user.lower().startswith("trial"):
                trial += 1
            try:
                expiry = DT.datetime.strptime(expiry_str, "%Y-%m-%d").date()
                if expiry >= today:
                    aktif += 1
                else:
                    expired += 1
            except Exception:
                pass
        stats[label] = {"total": total, "aktif": aktif, "expired": expired, "trial": trial}
    return stats


def _server_info():
    info = {}
    try:
        out = subprocess.check_output("uptime -p", shell=True).decode().strip()
        info["uptime"] = out
    except Exception:
        info["uptime"] = "-"
    try:
        out = subprocess.check_output("free -m | awk '/Mem:/ {print $3\"/\"$2\" MB\"}'",
                                      shell=True).decode().strip()
        info["ram"] = out
    except Exception:
        info["ram"] = "-"
    try:
        out = subprocess.check_output("df -h / | awk 'NR==2 {print $3\"/\"$2}'",
                                      shell=True).decode().strip()
        info["disk"] = out
    except Exception:
        info["disk"] = "-"
    return info


@bot.on(events.CallbackQuery(data=b'statistik'))
@bot.on(events.NewMessage(pattern=r'^/statistik$'))
async def statistik(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        try:
            await event.answer("Akses Ditolak", alert=True)
        except Exception:
            await event.reply("Akses Ditolak")
        return

    stats = _count_accounts()
    srv = _server_info()

    lines = ["📊 **STATISTIK VPN**\n"]
    grand_total = grand_aktif = grand_exp = grand_trial = 0
    for label, s in stats.items():
        lines.append(
            f"{label}\n"
            f"   Total: `{s['total']}` | ✅ `{s['aktif']}` | "
            f"❌ `{s['expired']}` | 🎁 `{s['trial']}`"
        )
        grand_total += s["total"]
        grand_aktif += s["aktif"]
        grand_exp += s["expired"]
        grand_trial += s["trial"]

    lines.append(f"\n**◇━━━━━━━━━━◇**")
    lines.append(f"📦 **Total:** `{grand_total}` | ✅ `{grand_aktif}` | ❌ `{grand_exp}` | 🎁 `{grand_trial}`")
    lines.append(f"\n🖥️ **Server:**")
    lines.append(f"   ⏱️ Uptime: `{srv['uptime']}`")
    lines.append(f"   💾 RAM: `{srv['ram']}`")
    lines.append(f"   💿 Disk: `{srv['disk']}`")

    msg = "\n".join(lines)
    try:
        await event.edit(msg, buttons=[[Button.inline("‹ Kembali", "menu")]])
    except Exception:
        await event.respond(msg, buttons=[[Button.inline("‹ Kembali", "menu")]])
