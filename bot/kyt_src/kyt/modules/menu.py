from kyt import *

@bot.on(events.NewMessage(pattern=r"(?:.menu|/menu)$"))
@bot.on(events.CallbackQuery(data=b'menu'))
async def menu(event):
    inline = [
        [Button.inline("🔐 SSH OVPN","ssh")],
        [Button.inline("📡 VMess","vmess"),
         Button.inline("🔷 VLess","vless")],
        [Button.inline("🔰 Trojan","trojan"),
         Button.inline("🌑 Shadowsocks","shadowsocks")],
        [Button.inline("ℹ️ VPS Info","info"),
         Button.inline("⚙️ Setting","setting")]]
    sender = await event.get_sender()
    val = valid(str(sender.id))
    if val == "false":
        try:
            await event.answer("Akses Ditolak", alert=True)
        except:
            await event.reply("Akses Ditolak")
    elif val == "true":
        sh = 'cat /etc/ssh/.ssh.db | grep "###" | wc -l'
        ssh = subprocess.check_output(sh, shell=True).decode("ascii")
        vm = 'cat /etc/xray/config.json | grep "###" | wc -l'
        vms = subprocess.check_output(vm, shell=True).decode("ascii")
        vl = 'cat /etc/vless/.vless.db | grep "###" | wc -l'
        vls = subprocess.check_output(vl, shell=True).decode("ascii")
        tr = 'cat /etc/trojan/.trojan.db | grep "###" | wc -l'
        trj = subprocess.check_output(tr, shell=True).decode("ascii")
        ss = 'cat /etc/shadowsocks/.shadowsocks.db | grep "###" | wc -l'
        ssk = subprocess.check_output(ss, shell=True).decode("ascii")
        z = requests.get("http://ip-api.com/json/?fields=query,country,city,isp").json()
        user_id = sender.id
        username = sender.username
        sn = globals().get('STORE_NAME', '🏪 Store')
        tid = str(user_id)
        # Determine active server mode
        try:
            from kyt.modules.server_manager import get_active_api, get_active
            api_sid = get_active_api(tid)
            if api_sid is not None:
                from kyt import get_remote_server
                s = get_remote_server(api_sid)
                mode_text = f"🌐 **Remote**: {s['name']}" if s else "🌐 Remote"
            else:
                ssh_sid = get_active(tid)
                mode_text = f"🔗 **Server #{ssh_sid}**" if ssh_sid is not None else "💻 **Local**"
        except Exception:
            mode_text = "💻 **Local**"
        msg = f"""
👤 **PANEL ADMIN**

Halo, **Admin**!  👋
{sn}

**◇━━━━━━━━━━◇**
🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
**◇━━━━━━━━━━◇**
🖥️ **Mode**: {mode_text}
**◇━━━━━━━━━━◇**
📊 **SSH** : `{ssh.strip()}` | **VMess** : `{vms.strip()}`
🔷 **VLess** : `{vls.strip()}` | 🔰 **Trojan** : `{trj.strip()}`
🌑 **SS** : `{ssk.strip()}`
**◇━━━━━━━━━━◇**
🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        try:
            await event.edit(msg,buttons=inline)
        except:
            await event.reply(msg,buttons=inline)


