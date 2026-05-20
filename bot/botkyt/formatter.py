"""Utility functions for formatting messages with modern Telegram styling"""

def format_currency(amount: int) -> str:
    """Format number as Indonesian Rupiah"""
    return f"Rp {amount:,.0f}".replace(",", ".")


def main_menu_text(user) -> str:
    """Format main menu message"""
    role_emoji = {"superadmin": "👑", "admin": "🛡️", "user": "👤"}
    role_label = {"superadmin": "Super Admin", "admin": "Admin", "user": "Member"}
    
    role = user['role']
    balance = user['balance']
    name = user['full_name'] or user['username'] or "User"
    
    return f"""
╔══════════════════════════════╗
   🌐 <b>WENDY VPN STORE</b> 🌐
╚══════════════════════════════╝

👋 Halo, <b>{name}</b>!

┌─────────────────────────
│ {role_emoji.get(role, '👤')} Role    : <b>{role_label.get(role, 'User')}</b>
│ 💰 Saldo   : <b>{format_currency(balance)}</b>
│ 🆔 ID      : <code>{user['telegram_id']}</code>
└─────────────────────────

<i>Pilih menu di bawah untuk melanjutkan:</i>
"""


def admin_panel_text(stats: dict) -> str:
    """Format admin panel message"""
    return f"""
╔══════════════════════════════╗
   ⚙️ <b>ADMIN PANEL</b> ⚙️
╚══════════════════════════════╝

┌─────────────────────────
│ 👥 Total User    : <b>{stats['total_users']}</b>
│ 🛡️ Total Admin   : <b>{stats['total_admins']}</b>
│ 💰 Total Saldo   : <b>{format_currency(stats['total_balance'])}</b>
│ 📊 Akun Aktif    : <b>{stats['active_accounts']}</b>
│ 💵 Total Revenue : <b>{format_currency(stats['total_revenue'])}</b>
│ 🖥️ Server Aktif  : <b>{stats['active_servers']}</b>
└─────────────────────────

<i>Pilih menu admin di bawah:</i>
"""


def purchase_menu_text() -> str:
    """Format purchase menu message"""
    return """
╔══════════════════════════════╗
   🛒 <b>BELI AKUN VPN</b> 🛒
╚══════════════════════════════╝

<i>Pilih protokol yang diinginkan:</i>

🔵 <b>SSH/WS</b> - Tunneling SSH via WebSocket
🟢 <b>VMess</b> - V2Ray VMess Protocol
🟡 <b>VLess</b> - V2Ray VLess Protocol  
🔴 <b>Trojan</b> - Trojan-Go Protocol
🟣 <b>Shadowsocks</b> - SS Protocol
"""


def server_select_text(protocol: str) -> str:
    """Format server selection message"""
    protocol_names = {
        "ssh": "SSH/WS",
        "vmess": "VMess",
        "vless": "VLess",
        "trojan": "Trojan",
        "shadowsocks": "Shadowsocks"
    }
    return f"""
╔══════════════════════════════╗
   🖥️ <b>PILIH SERVER</b> 🖥️
╚══════════════════════════════╝

📡 Protokol: <b>{protocol_names.get(protocol, protocol)}</b>

<i>Pilih server yang tersedia:</i>
"""


def duration_select_text(protocol: str, server_name: str) -> str:
    """Format duration selection message"""
    return f"""
╔══════════════════════════════╗
   ⏱ <b>PILIH DURASI</b> ⏱
╚══════════════════════════════╝

📡 Protokol : <b>{protocol.upper()}</b>
🖥️ Server   : <b>{server_name}</b>

<i>Pilih paket durasi di bawah:</i>
"""


def confirm_purchase_text(protocol: str, server_name: str, duration: int, price: int, ip_limit: int, quota_gb: int, balance: int) -> str:
    """Format purchase confirmation message"""
    status = "✅ Saldo Cukup" if balance >= price else "❌ Saldo Tidak Cukup"
    
    text = f"""
╔══════════════════════════════╗
   📝 <b>KONFIRMASI PEMBELIAN</b> 📝
╚══════════════════════════════╝

┌─────────────────────────
│ 📡 Protokol  : <b>{protocol.upper()}</b>
│ 🖥️ Server    : <b>{server_name}</b>
│ ⏱ Durasi    : <b>{duration} Hari</b>
│ 💲 Harga     : <b>{format_currency(price)}</b>
│ 🔗 Limit IP  : <b>{ip_limit} Device</b>
│ 📊 Quota     : <b>{'Unlimited' if quota_gb == 0 else f'{quota_gb} GB'}</b>
└─────────────────────────

💰 Saldo Anda : <b>{format_currency(balance)}</b>
📌 Status     : <b>{status}</b>
"""
    if balance < price:
        text += f"\n⚠️ <i>Saldo tidak cukup. Silakan deposit terlebih dahulu.</i>"
    
    return text


def account_detail_text(account, server_domain: str = "") -> str:
    """Format VPN account detail"""
    protocol = account['protocol'].upper()
    
    return f"""
╔══════════════════════════════╗
   📋 <b>DETAIL AKUN {protocol}</b>
╚══════════════════════════════╝

┌─────────────────────────
│ 📡 Protokol  : <b>{protocol}</b>
│ 🖥️ Server    : <b>{account.get('server_name', '-')}</b>
│ 👤 Username  : <code>{account['username']}</code>
│ 🔑 UUID/Pass : <code>{account.get('uuid') or account.get('password') or '-'}</code>
│ 🌐 Domain    : <code>{server_domain}</code>
│ ⏱ Expired   : <b>{account['expired_date']}</b>
│ 🔗 Limit IP  : <b>{account['ip_limit']} Device</b>
│ 📊 Status    : <b>{'🟢 Active' if account['status'] == 'active' else '🔴 Expired'}</b>
└─────────────────────────
"""


def deposit_text(balance: int) -> str:
    """Format deposit menu message"""
    return f"""
╔══════════════════════════════╗
   💰 <b>DEPOSIT SALDO</b> 💰
╚══════════════════════════════╝

💳 Saldo saat ini: <b>{format_currency(balance)}</b>

<i>Pilih metode deposit:</i>

📱 <b>QRIS</b> - Scan & bayar via semua e-wallet
🎫 <b>Voucher</b> - Redeem kode voucher
"""


def deposit_qris_text(amount: int) -> str:
    """Format QRIS deposit message"""
    return f"""
╔══════════════════════════════╗
   📱 <b>DEPOSIT VIA QRIS</b> 📱
╚══════════════════════════════╝

💲 Nominal: <b>{format_currency(amount)}</b>

<i>Pilih nominal deposit:</i>
"""


def payment_qris_text(amount: int, payment_id: str) -> str:
    """Format QRIS payment message"""
    return f"""
╔══════════════════════════════╗
   📱 <b>PEMBAYARAN QRIS</b> 📱
╚══════════════════════════════╝

💲 Nominal  : <b>{format_currency(amount)}</b>
🆔 Order ID : <code>{payment_id}</code>

⏳ <b>Scan QRIS di bawah untuk membayar</b>
⚠️ Pembayaran otomatis terverifikasi

<i>QRIS berlaku 15 menit</i>
"""


def transaction_history_text(transactions: list) -> str:
    """Format transaction history"""
    if not transactions:
        return """
╔══════════════════════════════╗
   💳 <b>RIWAYAT TRANSAKSI</b> 💳
╚══════════════════════════════╝

<i>Belum ada transaksi.</i>
"""
    
    text = """
╔══════════════════════════════╗
   💳 <b>RIWAYAT TRANSAKSI</b> 💳
╚══════════════════════════════╝

"""
    type_emoji = {
        "topup": "💰",
        "purchase": "🛒",
        "refund": "↩️",
        "transfer": "💸",
        "voucher": "🎫"
    }
    
    for tx in transactions:
        emoji = type_emoji.get(tx['type'], "📝")
        sign = "+" if tx['amount'] > 0 else ""
        text += f"│ {emoji} {tx['type'].upper()} | {sign}{format_currency(tx['amount'])} | {tx['created_at'][:10]}\n"
        if tx['description']:
            text += f"│    <i>{tx['description']}</i>\n"
    
    return text


def help_text() -> str:
    """Format help message"""
    return """
╔══════════════════════════════╗
   ℹ️ <b>BANTUAN</b> ℹ️
╚══════════════════════════════╝

<b>Cara Menggunakan Bot:</b>

1️⃣ <b>Deposit Saldo</b>
   Pilih menu Deposit → QRIS → Pilih nominal
   Scan QRIS dan saldo otomatis masuk

2️⃣ <b>Beli Akun VPN</b>
   Pilih menu Beli Akun → Pilih Protokol
   → Pilih Server → Pilih Durasi → Konfirmasi

3️⃣ <b>Cek Akun</b>
   Pilih menu Akun Saya untuk melihat
   semua akun VPN yang aktif

4️⃣ <b>Redeem Voucher</b>
   Dapatkan kode voucher dari admin
   Pilih menu Redeem Voucher → Input kode

<b>Kontak Admin:</b>
📱 WhatsApp: +6283153170199
💬 Telegram: @WendiVpn
"""


def server_info_text(servers: list) -> str:
    """Format server info message"""
    if not servers:
        return """
╔══════════════════════════════╗
   📊 <b>INFO SERVER</b> 📊
╚══════════════════════════════╝

<i>Belum ada server tersedia.</i>
"""
    
    text = """
╔══════════════════════════════╗
   📊 <b>INFO SERVER</b> 📊
╚══════════════════════════════╝

"""
    for s in servers:
        text += f"""┌─────────────────────────
│ 🖥️ <b>{s['name']}</b>
│ 🌐 Domain: <code>{s['domain']}</code>
│ 📡 Status: {'🟢 Online' if s['is_active'] else '🔴 Offline'}
└─────────────────────────
"""
    return text
