from kyt import *
from kyt.modules.server_manager import exec_cmd, get_active, get_server

#detail
@bot.on(events.CallbackQuery(data=b'd-vmess'))
async def l_vmess(event):
    async def l_vmess_(event):
        cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user_event).raw_text.replace(" ", "")
            cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-vmess")],
[Button.inline("❌ Batal","vmess")]])
                return
            cmd = f'cat /var/www/html/vmess-{user}.txt'.strip()
            x = exec_cmd(cmd, tid)
            z = x.decode("utf-8")
            if z:
                await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Kembali","vmess")]])
            else:
                await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Kembali","vmess")]])
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await l_vmess_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

#LOCK VMESS
@bot.on(events.CallbackQuery(data=b'lock-vmess'))
async def lock_vmess(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def lock_vmess_(event):
        cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^### {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "lock-vmess")],
                    [Button.inline("❌ Batal", "vmess")]])
                return
            cmd = f'printf "%s\n" "{user}" | lock-vm'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vmess")]])
        else:
            await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Kembali","vmess")]])
    await lock_vmess_(event)

#UNLOCK VMESS
@bot.on(events.CallbackQuery(data=b'unlock-vmess'))
async def unlock_vmess(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def unlock_vmess_(event):
        cmd = 'cat /etc/xray/.lock.db    | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^### {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "unlock-vmess")],
                    [Button.inline("❌ Batal", "vmess")]])
                return
            cmd = f'printf "%s\n" "{user}" | unlock-vm'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vmess")]])
        else:
            await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Kembali","vmess")]])
    await unlock_vmess_(event)

_admin_create_state = {}

async def _admin_ask_username(event, chat, state):
    state['step'] = 'username'
    await bot.send_message(chat, "🔡 **Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-vmess-uname")], [Button.inline("❌ Batal", "vmess")]])

async def _admin_ask_limit_ip(event, chat, state):
    state['step'] = 'limit_ip'
    await bot.send_message(chat, "🌐 **Limit IP:**\n\nMasukkan angka limit IP.",
        buttons=[[Button.inline("❌ Batal", "vmess")]])

async def _admin_ask_quota(event, chat, state):
    state['step'] = 'quota'
    await bot.send_message(chat, "📦 **Quota (GB):**\n\nMasukkan jumlah quota.",
        buttons=[[Button.inline("❌ Batal", "vmess")]])

async def _admin_ask_expiry(event, chat, state):
    state['step'] = 'expiry'
    await bot.send_message(chat, "⏳ **Masaaktif (hari):**\n\nMasukkan jumlah hari.",
        buttons=[[Button.inline("❌ Batal", "vmess")]])

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
            a = api_create_account('vmess', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
            user = uname
            done = True
            break
        except:
            if random_user:
                continue
            break
    if not done:
        await bot.send_message(chat, "**Gagal membuat akun. Coba lagi.**", buttons=[[Button.inline("‹ Kembali","vmess")]])
        return
    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    b = [x.group() for x in re.finditer("vmess://(.*)", a)]
    z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
    z = json.loads(z)
    z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
    z1 = json.loads(z1)
    msg = f"""
📡 **VMESS ACCOUNT**

👤 **Username** : `{z["ps"]}`
🔑 **UUID** : `{z["id"]}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{b[0].strip("'").replace(" ","")}`
🔗 **NTLS** : `{b[1].strip("'").replace(" ","")}`
🔗 **gRPC** : `{b[2].strip("'")}`
💾 [OpenClash](https://{DOMAIN}:8443/vmess-{z["ps"]}.txt)
{svr_label}
"""
    await bot.send_message(chat, msg, buttons=[[Button.inline("‹ Kembali","vmess")]])

@bot.on(events.CallbackQuery(data=b'create-vmess'))
async def create_vmess(event):
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
        'svc': 'vmess', 'step': None,
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
            await event.respond("❌ Limit IP harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vmess")]])
            return
        state['limit_ip'] = text
        await _admin_ask_quota(event, chat, state)
    elif step == 'quota':
        if not text.isdigit():
            await event.respond("❌ Quota harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vmess")]])
            return
        state['quota'] = text
        await _admin_ask_expiry(event, chat, state)
    elif step == 'expiry':
        if not text.isdigit():
            await event.respond("❌ Masaaktif harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vmess")]])
            return
        state['expiry'] = text
        await _admin_finish_create(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-vmess-uname'))
async def _admin_rand_vmess_uname(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'username':
        return
    state['username'] = "user" + str(random.randint(1000, 9999))
    state['random_user'] = True
    await event.edit("✅ Username acak: `" + state['username'] + "`")
    await _admin_ask_limit_ip(event, chat, state)

# TRIAL VMESS
@bot.on(events.CallbackQuery(data=b'trial-vmess'))
async def trial_vmess(event):
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
    async def trial_vmess_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as exp:
            await event.respond(" **Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        try:
            a = api_create_account('vmess', f'trial'+__import__('random').randint(1000,9999), days=exp, trial=True)
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","menu")]])
        else:
            inline=[[Button.inline("‹ Kembali","vmess")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            b = [x.group() for x in re.finditer("vmess://(.*)",a)]
            print(b)
            z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
            z = json.loads(z)
            z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
            z1 = json.loads(z1)
            msg = f"""
📡 **VMESS ACCOUNT**

👤 **Username** : `{z["ps"]}`
🔑 **UUID** : `{z["id"]}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `-`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{exp} Minutes`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{b[0].strip("'").replace(" ","")}`
🔗 **NTLS** : `{b[1].strip("'").replace(" ","")}`
🔗 **gRPC** : `{b[2].strip("'")}`
💾 [OpenClash](https://{DOMAIN}:8443/vmess-{z["ps"]}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await trial_vmess_(event)

# AUTO VMESS
@bot.on(events.CallbackQuery(data=b'auto-vmess'))
async def auto_vmess(event):
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
    async def auto_vmess_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as limit_ip:
            await event.respond("🌐 **Limit IP:**")
            limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            limit_ip = (await limit_ip).raw_text
            if not limit_ip.isdigit():
                await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Batal","vmess")]])
                return
        async with bot.conversation(chat) as pw:
            await event.respond("📦 **Quota:**")
            pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            pw = (await pw).raw_text
            if not pw.isdigit():
                await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Batal","vmess")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond("⏳ **Masaaktif:**")
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Batal","vmess")]])
                return
        bug = ""
        user = "VmessPrem" + str(random.randint(100,1000))
        try:
            a = api_create_account('vmess', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","vmess")]])
        else:
            inline=[[Button.inline("‹ Kembali","vmess")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            b = [x.group() for x in re.finditer("vmess://(.*)",a)]
            print(b)
            z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
            z = json.loads(z)
            z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
            z1 = json.loads(z1)
            msg = f"""
📡 **VMESS ACCOUNT**

👤 **Username** : `{z["ps"]}`
🔑 **UUID** : `{z["id"]}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{b[0].strip("'").replace(" ","")}`
🔗 **NTLS** : `{b[1].strip("'").replace(" ","")}`
🔗 **gRPC** : `{b[2].strip("'")}`
💾 [OpenClash](https://{DOMAIN}:8443/vmess-{z["ps"]}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await auto_vmess_(event)

@bot.on(events.CallbackQuery(data=b'bot-member-vmess'))
async def bot_member_vmess(event):
    async def bot_member_vmess_(event):
        cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
** Menampilkan Member Vmess**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","vmess")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await bot_member_vmess_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

#CEK VMESS
@bot.on(events.CallbackQuery(data=b'cek-vmess'))
async def cek_vmess(event):
    async def cek_vmess_(event):
        cmd = 'bot-cek-ws.sh'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Logged🔸⟩**
**◇━━━━━━━━━━◇**
```                      
{z}
```
**Shows Logged In Users Vmess**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","vmess")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await cek_vmess_(event)
    else:
        await event.answer("Access Denied",alert=True)
        

@bot.on(events.CallbackQuery(data=b'delete-vmess'))
async def delete_vmess(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def delete_vmess_(event):
        cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^### {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "delete-vmess")],
                    [Button.inline("❌ Batal", "vmess")]])
                return
        try:
            a = api_delete_account('vmess', user)
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vmess")]])
        else:
            await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Kembali","vmess")]])
    await delete_vmess_(event)

@bot.on(events.CallbackQuery(data=b'renew-ws'))
async def renew_ws(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def renew_ws_(event):
        cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username Renew:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^### {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "renew-ws")],
                    [Button.inline("❌ Batal", "vmess")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond(' **Ubah Masaaktif:**')
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vmess")]])
                return
        async with bot.conversation(chat) as quota:
            await event.respond(' **Limit Quota:**')
            quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            quota = (await quota).raw_text
            if not quota.isdigit():
                await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vmess")]])
                return
        async with bot.conversation(chat) as ip:
            await event.respond(' **Limit Ip:**')
            ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            ip = (await ip).raw_text
            if not ip.isdigit():
                await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vmess")]])
                return
        try:
            a = api_renew_account('vmess', user, days=exp, quota=quota, limit_ip=ip)
        except:
            await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Kembali","vmess")]])
        else:
            await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Kembali","vmess")]])
    await renew_ws_(event)

@bot.on(events.CallbackQuery(data=b'vmess'))
async def vmess(event):
    async def vmess_(event):
        inline = [
[Button.inline("☣️ Trial","trial-vmess"),
Button.inline("➕ Create","create-vmess")],
[Button.inline("♻️ Renew","renew-ws"),
Button.inline("👤 Member","bot-member-vmess")],
[Button.inline("✅ Check","cek-vmess"),
Button.inline("❌ Delete","delete-vmess")],
[Button.inline("🔒 Lock","lock-vmess"),
Button.inline("🔐 Unlock","unlock-vmess")],
[Button.inline("📝 Detail","d-vmess")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=query,country,city,timezone,isp").json()
        vm = f' cat /etc/xray/config.json | grep "###" | wc -l'
        vms = exec_cmd(vm, tid).decode("ascii")
        user_id = sender.id
        username = sender.username
        msg = f"""
📡 **VMESS MANAGER**

🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
📊 **Total** : `{vms.strip()}` akun

🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await vmess_(event)
    else:
        await event.answer("Access Denied",alert=True)
