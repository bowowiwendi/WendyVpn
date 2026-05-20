from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard(role: str = "user"):
    """Main menu keyboard based on user role"""
    keyboard = [
        [
            InlineKeyboardButton("🛒 Beli Akun", callback_data="menu_purchase"),
            InlineKeyboardButton("📋 Akun Saya", callback_data="menu_accounts"),
        ],
        [
            InlineKeyboardButton("💰 Deposit", callback_data="menu_deposit"),
            InlineKeyboardButton("💳 Riwayat", callback_data="menu_history"),
        ],
        [
            InlineKeyboardButton("🎫 Redeem Voucher", callback_data="menu_voucher"),
            InlineKeyboardButton("📊 Server", callback_data="menu_server_info"),
        ],
        [
            InlineKeyboardButton("ℹ️ Bantuan", callback_data="menu_help"),
        ],
    ]
    
    if role in ("admin", "superadmin"):
        keyboard.append([
            InlineKeyboardButton("⚙️ Admin Panel", callback_data="menu_admin"),
        ])
    
    return InlineKeyboardMarkup(keyboard)


def admin_menu_keyboard(role: str = "admin"):
    """Admin panel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("👥 Kelola User", callback_data="admin_users"),
            InlineKeyboardButton("💰 Top-up User", callback_data="admin_topup"),
        ],
        [
            InlineKeyboardButton("🎫 Buat Voucher", callback_data="admin_voucher"),
            InlineKeyboardButton("💲 Set Harga", callback_data="admin_pricing"),
        ],
        [
            InlineKeyboardButton("🖥️ Kelola Server", callback_data="admin_servers"),
            InlineKeyboardButton("📊 Statistik", callback_data="admin_stats"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("📋 List Akun", callback_data="admin_accounts"),
        ],
    ]
    
    if role == "superadmin":
        keyboard.append([
            InlineKeyboardButton("👑 Kelola Admin", callback_data="admin_manage_admins"),
        ])
    
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="back_main"),
    ])
    
    return InlineKeyboardMarkup(keyboard)


def protocol_keyboard():
    """Protocol selection keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("🔵 SSH/WS", callback_data="buy_ssh"),
            InlineKeyboardButton("🟢 VMess", callback_data="buy_vmess"),
        ],
        [
            InlineKeyboardButton("🟡 VLess", callback_data="buy_vless"),
            InlineKeyboardButton("🔴 Trojan", callback_data="buy_trojan"),
        ],
        [
            InlineKeyboardButton("🟣 Shadowsocks", callback_data="buy_shadowsocks"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def server_select_keyboard(servers: list, protocol: str):
    """Server selection keyboard"""
    keyboard = []
    for server in servers:
        keyboard.append([
            InlineKeyboardButton(
                f"🖥️ {server['name']} - {server['domain']}",
                callback_data=f"server_{protocol}_{server['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data="menu_purchase"),
    ])
    return InlineKeyboardMarkup(keyboard)


def duration_keyboard(pricing_list: list, protocol: str, server_id: int):
    """Duration selection keyboard with prices"""
    keyboard = []
    for price in pricing_list:
        label = f"⏱ {price['duration_days']} Hari - Rp {price['price']:,}"
        if price['ip_limit'] > 0:
            label += f" ({price['ip_limit']} IP)"
        keyboard.append([
            InlineKeyboardButton(
                label,
                callback_data=f"dur_{protocol}_{server_id}_{price['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("⬅️ Kembali", callback_data=f"buy_{protocol}"),
    ])
    return InlineKeyboardMarkup(keyboard)


def confirm_purchase_keyboard(price_id: int):
    """Confirm purchase keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Konfirmasi Beli", callback_data=f"confirm_buy_{price_id}"),
            InlineKeyboardButton("❌ Batal", callback_data="menu_purchase"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_keyboard():
    """Deposit method selection"""
    keyboard = [
        [
            InlineKeyboardButton("📱 QRIS (bayar.gg)", callback_data="deposit_qris"),
        ],
        [
            InlineKeyboardButton("🎫 Redeem Voucher", callback_data="menu_voucher"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="back_main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def deposit_amount_keyboard():
    """Deposit amount selection"""
    keyboard = [
        [
            InlineKeyboardButton("Rp 10.000", callback_data="dep_10000"),
            InlineKeyboardButton("Rp 20.000", callback_data="dep_20000"),
        ],
        [
            InlineKeyboardButton("Rp 50.000", callback_data="dep_50000"),
            InlineKeyboardButton("Rp 100.000", callback_data="dep_100000"),
        ],
        [
            InlineKeyboardButton("Rp 200.000", callback_data="dep_200000"),
            InlineKeyboardButton("Rp 500.000", callback_data="dep_500000"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali", callback_data="menu_deposit"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(callback_data: str = "back_main"):
    """Simple back button"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Kembali", callback_data=callback_data)]
    ])


def yes_no_keyboard(yes_data: str, no_data: str = "back_main"):
    """Yes/No confirmation keyboard"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Ya", callback_data=yes_data),
            InlineKeyboardButton("❌ Tidak", callback_data=no_data),
        ]
    ])


def pagination_keyboard(items: list, page: int, total_pages: int, prefix: str):
    """Pagination keyboard"""
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("◀️", callback_data=f"{prefix}_page_{page-1}"))
    
    nav_row.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("▶️", callback_data=f"{prefix}_page_{page+1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    keyboard.append([InlineKeyboardButton("⬅️ Kembali", callback_data="back_main")])
    return InlineKeyboardMarkup(keyboard)
