from kyt import *
from kyt.modules.server_manager import exec_cmd, get_active, get_server

#LOCK ss
@bot.on(events.CallbackQuery(data=b'lock-ss'))
async def lock_ss(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def lock_ss_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 SS Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#!! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "lock-ss")],
                    [Button.inline("❌ Batal", "shadowsocks")]])
                return
            cmd = f'printf "%s\n" "{user}" | lock-ss'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
        else:
            await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
    await lock_ss_(event)

#UNLOCK ss
@bot.on(events.CallbackQuery(data=b'unlock-ss'))
async def unlock_ss(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def unlock_ss_(event):
        cmd = 'cat /etc/xray/.lock.db | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 SS Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#!! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "unlock-ss")],
                    [Button.inline("❌ Batal", "shadowsocks")]])
                return
            cmd = f'printf "%s\n" "{user}" | unlock-ss'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
        else:
            await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
    await unlock_ss_(event)

#detail
@bot.on(events.CallbackQuery(data=b'd-ss'))
async def l_ss(event):
    async def l_ss_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd = f'cat /var/www/html/sodosokws-{user}.txt'.strip()
            x = exec_cmd(cmd, tid)
            print(x)
            z = exec_cmd(cmd, tid).decode("utf-8")
            if z:
                await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
            else:
                await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await l_ss_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

_admin_create_state = {}

async def _admin_ask_username(event, chat, state):
    state['step'] = 'username'
    await bot.send_message(chat, "🔡 **Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-ss-uname")], [Button.inline("❌ Batal", "shadowsocks")]])

async def _admin_ask_limit_ip(event, chat, state):
    state['step'] = 'limit_ip'
    await bot.send_message(chat, "🌐 **Limit IP:**\n\nMasukkan angka limit IP.",
        buttons=[[Button.inline("❌ Batal", "shadowsocks")]])

async def _admin_ask_quota(event, chat, state):
    state['step'] = 'quota'
    await bot.send_message(chat, "📦 **Quota (GB):**\n\nMasukkan jumlah quota.",
        buttons=[[Button.inline("❌ Batal", "shadowsocks")]])

async def _admin_ask_expiry(event, chat, state):
    state['step'] = 'expiry'
    await bot.send_message(chat, "⏳ **Masaaktif (hari):**\n\nMasukkan jumlah hari.",
        buttons=[[Button.inline("❌ Batal", "shadowsocks")]])

async def _admin_finish_create(event, chat, state):
    if chat in _admin_create_state:
        del _admin_create_state[chat]
    user = state['username']
    limit_ip = state['limit_ip']
    quota = state['quota']
    exp = state['expiry']
    random_user = state.get('random_user', False)
    svr_label = state.get('svr_label', '')
    tid = state['_tid']
    done = False
    for attempt in range(5 if random_user else 1):
        uname = ("user" + str(random.randint(1000, 9999)) if random_user else user)
        try:
            a = api_create_account('shadowsocks', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
            user = uname
            done = True
            break
        except:
            if random_user:
                continue
            break
    if not done:
        await bot.send_message(chat, "**Gagal membuat akun.**", buttons=[
[Button.inline("🔄 Ulangi", "create-shadowsocks")],
[Button.inline("❌ Batal","shadowsocks")]])
        return
    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    x = [x.group() for x in re.finditer("ss://(.*)", a)]
    uuid = re.search("ss://(.*?)@", x[0]).group(1)
    msg = f"""
🌑 **SHADOWSOCKS ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://${DOMAIN}:8443/oc-sodosokws-{user}.txt)
{svr_label}
"""
    qr_path = generate_qr(x[0].replace(" ",""), "ss")
    await bot.send_file(chat, qr_path, caption=msg, buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
    if qr_path:
        os.unlink(qr_path)

@bot.on(events.CallbackQuery(data=b'create-shadowsocks'))
async def create_shadowsocks(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    state = {
        'svc': 'shadowsocks', 'step': None,
        'username': None, 'limit_ip': None,
        'quota': None, 'expiry': None,
        'random_user': False, 'svr_label': svr_label,
        '_chat': chat, '_tid': tid, '_sender_id': sender.id,
    }
    _admin_create_state[chat] = state
    await _admin_ask_username(event, chat, state)

@bot.on(events.NewMessage(incoming=True))
async def _admin_handle_create_input(event):
    chat = event.chat_id
    if chat not in _admin_create_state:
        return
    state = _admin_create_state[chat]
    sender = await event.get_sender()
    if sender.id != state.get('_sender_id'):
        return
    text = event.raw_text.strip().replace(" ", "")
    step = state.get('step')
    
    if step == 'username':
        if not text or text.lower() == 'random':
            state['username'] = "user" + str(random.randint(1000, 9999))
            state['random_user'] = True
            await event.respond("✅ Username acak: `" + state['username'] + "`")
        else:
            state['username'] = text
            state['random_user'] = False
        await _admin_ask_limit_ip(event, chat, state)
    elif step == 'limit_ip':
        if not text.isdigit():
            await event.respond("❌ Limit IP harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-shadowsocks")]])
            return
        state['limit_ip'] = text
        await _admin_ask_quota(event, chat, state)
    elif step == 'quota':
        if not text.isdigit():
            await event.respond("❌ Quota harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-shadowsocks")]])
            return
        state['quota'] = text
        await _admin_ask_expiry(event, chat, state)
    elif step == 'expiry':
        if not text.isdigit():
            await event.respond("❌ Masaaktif harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-shadowsocks")]])
            return
        state['expiry'] = text
        await _admin_finish_create(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-ss-uname'))
async def _admin_rand_ss_uname(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'username':
        return
    state['username'] = "user" + str(random.randint(1000, 9999))
    state['random_user'] = True
    await event.edit("✅ Username acak: `" + state['username'] + "`")
    await _admin_ask_limit_ip(event, chat, state)

@bot.on(events.CallbackQuery(data=b'auto-shadowsocks'))
async def auto_shadowsocks(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    async def auto_shadowsocks_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as limit_ip:
            await event.respond("🌐 **Limit IP:**")
            limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            limit_ip = (await limit_ip).raw_text
            if not limit_ip.isdigit():
                await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-shadowsocks")],
[Button.inline("❌ Batal","shadowsocks")]])
                return
        async with bot.conversation(chat) as pw:
            await event.respond("📦 **Quota:**")
            pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            pw = (await pw).raw_text
            if not pw.isdigit():
                await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-shadowsocks")],
[Button.inline("❌ Batal","shadowsocks")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond("⏳ **Masaaktif:**")
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-shadowsocks")],
[Button.inline("❌ Batal","shadowsocks")]])
                return
        bug = ""
        user = "ShadowPrem"+str(random.randint(100,1000))
        try:
            a = api_create_account('shadowsocks', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
        except:
            await event.respond("**User Already Exist**")
        else:
            inline=[[Button.inline("‹ Kembali","menu")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            x = [x.group() for x in re.finditer("ss://(.*)",a)]
            print(x)
            uuid = re.search("ss://(.*?)@",x[0]).group(1)
            msg = f"""
🌑 **SHADOWSOCKS ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://${DOMAIN}:8443/oc-sodosokws-{user}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await auto_shadowsocks_(event)

@bot.on(events.CallbackQuery(data=b'cek-shadowsocks'))
async def cek_shadowsocks(event):
    async def cek_shadowsocks_(event):
        cmd = 'bot-cek-ss'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Logged🔸⟩**
**◇━━━━━━━━━━◇**
```                      
{z}
```
**Shows Logged In Users Shadowsocks**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","menu")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await cek_shadowsocks_(event)
    else:
        await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-shadowsocks'))
async def delete_shadowsocks(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def delete_shadowsocks_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#!! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "delete-shadowsocks")],
                    [Button.inline("❌ Batal", "shadowsocks")]])
                return
        try:
            a = api_delete_account('shadowsocks', user)
        except:
            await event.respond(f"**User** `{user}` **Successfully Deleted**",buttons=[[Button.inline("‹ Kembali","shadowsocks")]])
        else:
            inline=[[Button.inline("‹ Kembali","shadowsocks")]]
            msg = f"""**Successfully Deleted**"""
            await event.respond(msg,buttons=inline)
    await delete_shadowsocks_(event)

@bot.on(events.CallbackQuery(data=b'trial-shadowsocks'))
async def trial_shadowsocks(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    async def trial_shadowsocks_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as exp:
            await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        try:
            a = api_create_account('shadowsocks', f'trial'+__import__('random').randint(1000,9999), days=exp, trial=True)
        except:
            await event.respond("**User Already Exist**")
        else:
            inline=[[Button.inline("‹ Kembali","menu")]]
            x = [x.group() for x in re.finditer("ss://(.*)",a)]
            print(x)
            remarks = re.search("#(.*)",x[0]).group(1)
            uuid = re.search("ss://(.*?)@",x[0]).group(1)
            msg = f"""
🌑 **SHADOWSOCKS ACCOUNT**

👤 **Username** : `{remarks}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `-`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{exp} Minutes`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://${DOMAIN}:8443/ss-{remarks}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await trial_shadowsocks_(event)

@bot.on(events.CallbackQuery(data=b'bot-member-ss'))
async def bot_member_ss(event):
    async def bot_member_ss_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Shadowsocks**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","menu")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await bot_member_ss_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-ss'))
async def renew_ss(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def renew_ss_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        print(x)
        z = exec_cmd(cmd, tid).decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Shadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username Renew:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#!! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "renew-ss")],
                    [Button.inline("❌ Batal", "shadowsocks")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond(' **Ubah Masaaktif:**')
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ss")],
[Button.inline("❌ Batal","shadowsocks")]])
                return
        try:
            a = api_renew_account('shadowsocks', user, days=exp)
        except:
            await event.respond(f"**User** `{user}` **Not Found**",buttons=[[Button.inline("‹ Kembali","menu")]])
        else:
            await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Kembali","menu")]])
    await renew_ss_(event)

@bot.on(events.CallbackQuery(data=b'shadowsocks'))
async def shadowsocks(event):
    async def shadowsocks_(event):
        inline = [
[Button.inline("☣️ Trial","trial-shadowsocks"),
Button.inline("➕ Create","create-shadowsocks")],
[Button.inline("♻️ Renew","renew-ss"),
Button.inline("👤 Member","bot-member-ss")],
[Button.inline("✅ Check","cek-shadowsocks"),
Button.inline("❌ Delete","delete-shadowsocks")],
[Button.inline("🔒 Lock","lock-ss"),
Button.inline("🔐 Unlock","unlock-ss")],
[Button.inline("📝 Detail","d-ss")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=query,country,city,timezone,isp").json()
        ss = f' cat /etc/shadowsocks/.shadowsocks.db | grep "###" | wc -l'
        ssk = exec_cmd(ss, tid).decode("ascii")
        username = sender.username
        user_id = sender.id
        msg = f"""
🌑 **SHADOWSOCKS MANAGER**

🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
📊 **Total** : `{ssk.strip()}` akun

🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await shadowsocks_(event)
    else:
        await event.answer("Access Denied",alert=True)
