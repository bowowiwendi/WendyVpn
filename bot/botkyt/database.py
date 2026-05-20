import aiosqlite
import os
from config import DB_PATH

async def init_db():
    """Initialize database with all required tables"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            -- Tabel Users
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                balance INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                is_banned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Tabel Transaksi
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount INTEGER NOT NULL,
                description TEXT,
                admin_id INTEGER,
                reference_id TEXT,
                status TEXT DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );

            -- Tabel Akun VPN
            CREATE TABLE IF NOT EXISTS vpn_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                server_id INTEGER,
                protocol TEXT NOT NULL,
                username TEXT NOT NULL,
                uuid TEXT,
                password TEXT,
                expired_date TEXT NOT NULL,
                ip_limit INTEGER DEFAULT 2,
                quota_gb INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                config_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (server_id) REFERENCES servers(id)
            );

            -- Tabel Harga
            CREATE TABLE IF NOT EXISTS pricing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                duration_days INTEGER NOT NULL,
                price INTEGER NOT NULL,
                ip_limit INTEGER DEFAULT 2,
                quota_gb INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                server_id INTEGER,
                FOREIGN KEY (server_id) REFERENCES servers(id)
            );

            -- Tabel Voucher
            CREATE TABLE IF NOT EXISTS vouchers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                amount INTEGER NOT NULL,
                is_used INTEGER DEFAULT 0,
                used_by INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_at TIMESTAMP
            );

            -- Tabel Servers
            CREATE TABLE IF NOT EXISTS servers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                domain TEXT NOT NULL,
                ssh_port INTEGER DEFAULT 22,
                ssh_user TEXT DEFAULT 'root',
                ssh_password TEXT,
                is_active INTEGER DEFAULT 1,
                max_accounts INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Tabel Payments (bayar.gg)
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                payment_id TEXT UNIQUE,
                amount INTEGER NOT NULL,
                method TEXT DEFAULT 'qris',
                status TEXT DEFAULT 'pending',
                qris_url TEXT,
                callback_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            );

            -- Tabel Settings
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        await db.commit()


# ==================== USER OPERATIONS ====================

async def get_user(telegram_id: int):
    """Get user by telegram ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return await cursor.fetchone()


async def create_user(telegram_id: int, username: str = None, full_name: str = None, role: str = "user"):
    """Create new user"""
    import secrets
    referral_code = secrets.token_hex(4).upper()
    
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT OR IGNORE INTO users (telegram_id, username, full_name, role, referral_code)
               VALUES (?, ?, ?, ?, ?)""",
            (telegram_id, username, full_name, role, referral_code)
        )
        await db.commit()


async def update_user_balance(telegram_id: int, amount: int):
    """Update user balance (positive = add, negative = subtract)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (amount, telegram_id)
        )
        if amount < 0:
            await db.execute(
                "UPDATE users SET total_spent = total_spent + ? WHERE telegram_id = ?",
                (abs(amount), telegram_id)
            )
        await db.commit()


async def set_user_role(telegram_id: int, role: str):
    """Set user role"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE telegram_id = ?",
            (role, telegram_id)
        )
        await db.commit()


async def ban_user(telegram_id: int, banned: bool = True):
    """Ban or unban user"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_banned = ? WHERE telegram_id = ?",
            (1 if banned else 0, telegram_id)
        )
        await db.commit()


async def get_all_users(role: str = None):
    """Get all users, optionally filtered by role"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if role:
            cursor = await db.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY created_at DESC", (role,)
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            )
        return await cursor.fetchall()


async def get_user_count():
    """Get total user count"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        row = await cursor.fetchone()
        return row[0]


# ==================== TRANSACTION OPERATIONS ====================

async def add_transaction(user_id: int, tx_type: str, amount: int, description: str = None, admin_id: int = None, reference_id: str = None):
    """Add transaction record"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO transactions (user_id, type, amount, description, admin_id, reference_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, tx_type, amount, description, admin_id, reference_id)
        )
        await db.commit()


async def get_user_transactions(telegram_id: int, limit: int = 10):
    """Get user transaction history"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM transactions WHERE user_id = ? 
               ORDER BY created_at DESC LIMIT ?""",
            (telegram_id, limit)
        )
        return await cursor.fetchall()


# ==================== VPN ACCOUNT OPERATIONS ====================

async def add_vpn_account(user_id: int, server_id: int, protocol: str, username: str, 
                          uuid: str, expired_date: str, ip_limit: int = 2, 
                          quota_gb: int = 0, config_link: str = None, password: str = None):
    """Add VPN account record"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO vpn_accounts 
               (user_id, server_id, protocol, username, uuid, password, expired_date, ip_limit, quota_gb, config_link)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, server_id, protocol, username, uuid, password, expired_date, ip_limit, quota_gb, config_link)
        )
        await db.commit()


async def get_user_vpn_accounts(telegram_id: int, status: str = "active"):
    """Get user's VPN accounts"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT va.*, s.name as server_name, s.domain as server_domain
               FROM vpn_accounts va
               LEFT JOIN servers s ON va.server_id = s.id
               WHERE va.user_id = ? AND va.status = ?
               ORDER BY va.created_at DESC""",
            (telegram_id, status)
        )
        return await cursor.fetchall()


async def expire_vpn_account(account_id: int):
    """Mark VPN account as expired"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE vpn_accounts SET status = 'expired' WHERE id = ?",
            (account_id,)
        )
        await db.commit()


# ==================== PRICING OPERATIONS ====================

async def get_pricing(protocol: str = None, server_id: int = None):
    """Get pricing list"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        query = "SELECT * FROM pricing WHERE is_active = 1"
        params = []
        
        if protocol:
            query += " AND protocol = ?"
            params.append(protocol)
        if server_id:
            query += " AND (server_id = ? OR server_id IS NULL)"
            params.append(server_id)
        
        query += " ORDER BY protocol, duration_days"
        cursor = await db.execute(query, params)
        return await cursor.fetchall()


async def set_pricing(protocol: str, duration_days: int, price: int, ip_limit: int = 2, quota_gb: int = 0, server_id: int = None):
    """Set or update pricing"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if exists
        cursor = await db.execute(
            """SELECT id FROM pricing 
               WHERE protocol = ? AND duration_days = ? AND (server_id = ? OR (server_id IS NULL AND ? IS NULL))""",
            (protocol, duration_days, server_id, server_id)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await db.execute(
                """UPDATE pricing SET price = ?, ip_limit = ?, quota_gb = ? WHERE id = ?""",
                (price, ip_limit, quota_gb, existing[0])
            )
        else:
            await db.execute(
                """INSERT INTO pricing (protocol, duration_days, price, ip_limit, quota_gb, server_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (protocol, duration_days, price, ip_limit, quota_gb, server_id)
            )
        await db.commit()


# ==================== VOUCHER OPERATIONS ====================

async def create_voucher(code: str, amount: int, created_by: int):
    """Create new voucher"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO vouchers (code, amount, created_by) VALUES (?, ?, ?)",
            (code, amount, created_by)
        )
        await db.commit()


async def redeem_voucher(code: str, user_id: int):
    """Redeem voucher, returns amount or None if invalid"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM vouchers WHERE code = ? AND is_used = 0",
            (code,)
        )
        voucher = await cursor.fetchone()
        
        if voucher:
            await db.execute(
                """UPDATE vouchers SET is_used = 1, used_by = ?, used_at = CURRENT_TIMESTAMP 
                   WHERE code = ?""",
                (user_id, code)
            )
            await db.commit()
            return voucher[2]  # amount
        return None


# ==================== SERVER OPERATIONS ====================

async def add_server(name: str, host: str, domain: str, ssh_port: int = 22, 
                     ssh_user: str = "root", ssh_password: str = None, max_accounts: int = 100):
    """Add new server"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO servers (name, host, domain, ssh_port, ssh_user, ssh_password, max_accounts)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, host, domain, ssh_port, ssh_user, ssh_password, max_accounts)
        )
        await db.commit()


async def get_servers(active_only: bool = True):
    """Get all servers"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if active_only:
            cursor = await db.execute("SELECT * FROM servers WHERE is_active = 1")
        else:
            cursor = await db.execute("SELECT * FROM servers")
        return await cursor.fetchall()


async def get_server(server_id: int):
    """Get server by ID"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        return await cursor.fetchone()


async def delete_server(server_id: int):
    """Deactivate server"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE servers SET is_active = 0 WHERE id = ?", (server_id,))
        await db.commit()


# ==================== PAYMENT OPERATIONS ====================

async def create_payment(user_id: int, amount: int, payment_id: str = None, qris_url: str = None):
    """Create payment record"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO payments (user_id, amount, payment_id, qris_url)
               VALUES (?, ?, ?, ?)""",
            (user_id, amount, payment_id, qris_url)
        )
        await db.commit()


async def update_payment_status(payment_id: str, status: str):
    """Update payment status"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE payments SET status = ?, paid_at = CURRENT_TIMESTAMP 
               WHERE payment_id = ?""",
            (status, payment_id)
        )
        await db.commit()


async def get_pending_payment(user_id: int):
    """Get user's pending payment"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT * FROM payments WHERE user_id = ? AND status = 'pending' 
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        )
        return await cursor.fetchone()


# ==================== SETTINGS OPERATIONS ====================

async def get_setting(key: str, default: str = None):
    """Get setting value"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = await cursor.fetchone()
        return row[0] if row else default


async def set_setting(key: str, value: str):
    """Set setting value"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        await db.commit()


# ==================== STATISTICS ====================

async def get_stats():
    """Get overall statistics"""
    async with aiosqlite.connect(DB_PATH) as db:
        stats = {}
        
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        stats['total_admins'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COALESCE(SUM(balance), 0) FROM users")
        stats['total_balance'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM vpn_accounts WHERE status = 'active'")
        stats['active_accounts'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = 'purchase'"
        )
        stats['total_revenue'] = (await cursor.fetchone())[0]
        
        cursor = await db.execute("SELECT COUNT(*) FROM servers WHERE is_active = 1")
        stats['active_servers'] = (await cursor.fetchone())[0]
        
        return stats
