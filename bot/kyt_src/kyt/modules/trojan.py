from kyt import *
from kyt.modules.server_manager import exec_cmd, get_active, get_server

#detail
@bot.on(events.CallbackQuery(data=b'd-trojan'))
async def l_trojan(event):
    async def l_trojan_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
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
[Button.inline("🔄 Ulangi","d-trojan")],
[Button.inline("❌ Batal","trojan")]])
                return
            cmd = f'cat /var/www/html/trojan-{user}.txt'.strip()
            x = exec_cmd(cmd, tid)
            z = x.decode("utf-8")
            if z:
                await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Kembali","trojan")]])
            else:
                await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Kembali","trojan")]])
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await l_trojan_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

#LOCK trojan
@bot.on(events.CallbackQuery(data=b'lock-trojan'))
async def lock_trojan(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def lock_trojan_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "lock-trojan")],
                    [Button.inline("❌ Batal", "trojan")]])
                return
            cmd = f'printf "%s\n" "{user}" | lock-tr'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","trojan")]])
        else:
            await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Kembali","trojan")]])
    await lock_trojan_(event)
#UNLOCK trojan
@bot.on(events.CallbackQuery(data=b'unlock-trojan'))
async def unlock_trojan(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def unlock_trojan_(event):
        cmd = 'cat /etc/xray/.lock.db    | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(" **🔡Username:**")
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "unlock-trojan")],
                    [Button.inline("❌ Batal", "trojan")]])
                return
            cmd = f'printf "%s\n" "{user}" | unlock-tr'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","trojan")]])
        else:
            await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Kembali","trojan")]])
    await unlock_trojan_(event)


_admin_create_state = {}

async def _admin_ask_username(event, chat, state):
    state['step'] = 'username'
    await bot.send_message(chat, "🔡 **Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-trojan-uname")], [Button.inline("❌ Batal", "trojan")]])

async def _admin_ask_limit_ip(event, chat, state):
    state['step'] = 'limit_ip'
    await bot.send_message(chat, "🌐 **Limit IP:**\n\nMasukkan angka limit IP.",
        buttons=[[Button.inline("❌ Batal", "trojan")]])

async def _admin_ask_password(event, chat, state):
    state['step'] = 'password'
    await bot.send_message(chat, "📦 **Password:**\n\nKetik password, atau klik 🔀 Acak untuk password acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-trojan-pass")], [Button.inline("❌ Batal", "trojan")]])

async def _admin_ask_quota(event, chat, state):
    state['step'] = 'quota'
    await bot.send_message(chat, "💾 **Quota (GB):**\n\nMasukkan jumlah quota.",
        buttons=[[Button.inline("❌ Batal", "trojan")]])

async def _admin_ask_expiry(event, chat, state):
    state['step'] = 'expiry'
    await bot.send_message(chat, "⏳ **Masaaktif (hari):**\n\nMasukkan jumlah hari.",
        buttons=[[Button.inline("❌ Batal", "trojan")]])

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
            a = api_create_account('trojan', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
            user = uname
            done = True
            break
        except:
            if random_user:
                continue
            break
    if not done:
        await bot.send_message(chat, "**Gagal membuat akun.**", buttons=[[Button.inline("‹ Kembali","trojan")]])
        return
    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    b = [x.group() for x in re.finditer("trojan://(.*)", a)]
    uuid = re.search("trojan://(.*?)@", b[0]).group(1)
    msg = f"""
🔰 **TROJAN ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `{quota}` GB
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **WS** : `{b[0].replace(" ","")}`
🔗 **gRPC** : `{b[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/trojan-{user}.txt)
{svr_label}
"""
    qr_path = generate_qr(b[0].replace(" ",""), "trojan")
    await bot.send_file(chat, qr_path, caption=msg, buttons=[[Button.inline("‹ Kembali","trojan")]])
    if qr_path:
        os.unlink(qr_path)

@bot.on(events.CallbackQuery(data=b'create-trojan'))
async def create_trojan(event):
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
        'svc': 'trojan', 'step': None,
        'username': None, 'limit_ip': None,
        'password': None, 'quota': None,
        'expiry': None,
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
            await event.respond("❌ Limit IP harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-trojan")]])
            return
        state['limit_ip'] = text
        await _admin_ask_password(event, chat, state)
    elif step == 'password':
        if not text or text.lower() == 'random':
            state['password'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
            await event.respond("✅ Password acak: `" + state['password'] + "`")
        else:
            state['password'] = text
        await _admin_ask_quota(event, chat, state)
    elif step == 'quota':
        if not text.isdigit():
            await event.respond("❌ Quota harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-trojan")]])
            return
        state['quota'] = text
        await _admin_ask_expiry(event, chat, state)
    elif step == 'expiry':
        if not text.isdigit():
            await event.respond("❌ Masaaktif harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-trojan")]])
            return
        state['expiry'] = text
        await _admin_finish_create(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-trojan-uname'))
async def _admin_rand_trojan_uname(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'username':
        return
    state['username'] = "user" + str(random.randint(1000, 9999))
    state['random_user'] = True
    await event.edit("✅ Username acak: `" + state['username'] + "`")
    await _admin_ask_limit_ip(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-trojan-pass'))
async def _admin_rand_trojan_pass(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'password':
        return
    state['password'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    await event.edit("✅ Password acak: `" + state['password'] + "`")
    await _admin_ask_quota(event, chat, state)

# AUTO TROJAN
@bot.on(events.CallbackQuery(data=b'auto-trojan'))
async def auto_trojan(event):
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
    async def auto_trojan_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as limit_ip:
            await event.respond("🌐 **Limit IP:**")
            limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            limit_ip = (await limit_ip).raw_text
            if not limit_ip.isdigit():
                await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Batal","trojan")]])
                return
        async with bot.conversation(chat) as pw:
            await event.respond("📦 **Quota:**")
            pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            pw = (await pw).raw_text
            if not pw.isdigit():
                await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Batal","trojan")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond("⏳ **Masaaktif:**")
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Batal","trojan")]])
                return
        bug = ""
        user = "TrojanPrem"+str(random.randint(100,1000))
        try:
            a = api_create_account('trojan', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","trojan")]])
        else:
            inline=[[Button.inline("‹ Kembali","trojan")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            b = [x.group() for x in re.finditer("trojan://(.*)",a)]
            print(b)
            uuid = re.search("trojan://(.*?)@",b[0]).group(1)
            msg = f"""
🔰 **TROJAN ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `{pw}` GB
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **WS** : `{b[0].replace(" ","")}`
🔗 **gRPC** : `{b[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/trojan-{user}.txt)
{svr_label}
"""
            qr_path = generate_qr(b[0].replace(" ",""), "trojan")
            await bot.send_file(event.chat_id, qr_path, caption=msg, buttons=inline)
            os.unlink(qr_path)
    await auto_trojan_(event)

@bot.on(events.CallbackQuery(data=b'cek-trojan'))
async def cek_trojan(event):
    async def cek_trojan_(event):
        cmd = 'bot-cek-tr'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Logged🔸⟩**
**◇━━━━━━━━━━◇**
```                      
{z}
```
**Shows Logged In Users Trojan**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","trojan")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await cek_trojan_(event)
    else:
        await event.answer("Access Denied",alert=True)

# TRIAL TROJAN
@bot.on(events.CallbackQuery(data=b'trial-trojan'))
async def trial_trojan(event):
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
    async def trial_trojan_(event):
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
            a = api_create_account('trojan', f'trial'+__import__('random').randint(1000,9999), days=exp, trial=True)
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","menu")]])
        else:
            inline=[[Button.inline("‹ Kembali","trojan")]]
            b = [x.group() for x in re.finditer("trojan://(.*)",a)]
            print(b)
            remarks = re.search("#(.*)",b[0]).group(1)
            uuid = re.search("trojan://(.*?)@",b[0]).group(1)
            msg = f"""
🔰 **TROJAN ACCOUNT**

👤 **Username** : `{remarks}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `-`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{exp} Minutes`

**◇━━━━━━━━━━◇**
🔗 **WS** : `{b[0].replace(" ","")}`
🔗 **gRPC** : `{b[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/trojan-{remarks}.txt)
{svr_label}
"""
            qr_path = generate_qr(b[0].replace(" ",""), "trojan")
            await bot.send_file(event.chat_id, qr_path, caption=msg, buttons=inline)
            os.unlink(qr_path)
    await trial_trojan_(event)

@bot.on(events.CallbackQuery(data=b'delete-trojan'))
async def delete_trojan(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def delete_trojan_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "delete-trojan")],
                    [Button.inline("❌ Batal", "trojan")]])
                return
        try:
            a = api_delete_account('trojan', user)
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","trojan")]])
        else:
            await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Kembali","trojan")]])
    await delete_trojan_(event)

@bot.on(events.CallbackQuery(data=b'bot-member-trojan'))
async def bot_member_trojan(event):
    async def bot_member_trojan_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Trojan**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","trojan")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await bot_member_trojan_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-tr'))
async def renew_tr(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def renew_tr_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
        async with bot.conversation(chat) as user:
            await event.respond(' **🔡Username Renew:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            cmd_check = f'grep "^#! {user} " /etc/xray/config.json'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "renew-tr")],
                    [Button.inline("❌ Batal", "trojan")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond(' **Ubah Masaaktif:**')
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Batal","trojan")]])
                return
        async with bot.conversation(chat) as quota:
            await event.respond(' **Limit Quota:**')
            quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            quota = (await quota).raw_text
            if not quota.isdigit():
                await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Batal","trojan")]])
                return
        async with bot.conversation(chat) as ip:
            await event.respond(' **Limit Ip:**')
            ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            ip = (await ip).raw_text
            if not ip.isdigit():
                await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Batal","trojan")]])
                return
        try:
            a = api_renew_account('trojan', user, days=exp, quota=quota, limit_ip=ip)
        except:
            await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Kembali","trojan")]])
        else:
            await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Kembali","trojan")]])
    await renew_tr_(event)


@bot.on(events.CallbackQuery(data=b'trojan'))
async def trojan(event):
    async def trojan_(event):
        inline = [
[Button.inline("☣️ Trial","trial-trojan"),
Button.inline("➕ Create","create-trojan")],
[Button.inline("♻️ Renew","renew-tr"),
Button.inline("👤 Member","bot-member-trojan")],
[Button.inline("✅ Check","cek-trojan"),
Button.inline("❌ Delete","delete-trojan")],
[Button.inline("🔒 Lock","lock-trojan"),
Button.inline("🔐 Unlock","unlock-trojan")],
[Button.inline("📝 Detail","d-trojan")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=query,country,city,timezone,isp").json()
        tr = f' cat /etc/trojan/.trojan.db | grep "###" | wc -l'
        trj = exec_cmd(tr, tid).decode("ascii")
        user_id = sender.id
        username = sender.username
        msg = f"""
🔰 **TROJAN MANAGER**

🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
📊 **Total** : `{trj.strip()}` akun

🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await trojan_(event)
    else:
        await event.answer("Access Denied",alert=True)
