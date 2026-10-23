// ============================================================
// SQLite wrapper (promise-based) + inisialisasi tabel
// ============================================================
const sqlite3 = require('sqlite3').verbose();
const config = require('./config');
const fs = require('fs');
const path = require('path');

const db = new sqlite3.Database(config.dbPath);

const run = (sql, params = []) =>
  new Promise((resolve, reject) => {
    db.run(sql, params, function (err) {
      if (err) reject(err);
      else resolve({ id: this.lastID, changes: this.changes });
    });
  });

const get = (sql, params = []) =>
  new Promise((resolve, reject) => {
    db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
  });

const all = (sql, params = []) =>
  new Promise((resolve, reject) => {
    db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
  });

async function init() {
  await run(`CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    saldo INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    role TEXT DEFAULT 'member'
  )`);
  await run(`ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'member'`).catch(() => {});

  await run(`CREATE TABLE IF NOT EXISTS vpn_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    proto TEXT,
    username TEXT,
    expiry TEXT,
    is_trial INTEGER DEFAULT 0,
    via_cf INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
  )`);

  await run(`CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    type TEXT,
    amount INTEGER,
    ref_id TEXT UNIQUE,
    payment_id TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
  )`);
  await run(`ALTER TABLE transactions ADD COLUMN payment_id TEXT DEFAULT ''`).catch(() => {});
  await run(`ALTER TABLE transactions ADD COLUMN sku TEXT DEFAULT ''`).catch(() => {});
  await run(`ALTER TABLE transactions ADD COLUMN gateway TEXT DEFAULT 'gopay'`).catch(() => {});

  // Konfigurasi Pakasir (payment link QRIS/VA) — diatur admin via panel bot
  await run(`CREATE TABLE IF NOT EXISTS pakasir_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    slug TEXT DEFAULT '',
    api_key TEXT DEFAULT '',
    enabled INTEGER DEFAULT 0
  )`);
  await run(`INSERT OR IGNORE INTO pakasir_config (id, slug, api_key, enabled) VALUES (1, '', '', 0)`);

  await run(`CREATE TABLE IF NOT EXISTS notified_expired (
    account_id INTEGER PRIMARY KEY,
    notified_at TEXT DEFAULT (datetime('now'))
  )`);

  await run(`CREATE TABLE IF NOT EXISTS servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    domain TEXT DEFAULT '',
    harga INTEGER DEFAULT 500
  )`);

  await run(`CREATE TABLE IF NOT EXISTS bonus_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    min_topup INTEGER DEFAULT 0,
    bonus_percent INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 0
  )`);
  await run(`INSERT OR IGNORE INTO bonus_config (id, min_topup, bonus_percent, enabled) VALUES (1, 0, 0, 0)`);

  // Harga VPN per role (diatur admin via panel; product_key = ssh/vmess/vless/trojan/shadowsocks/zivpn)
  await run(`CREATE TABLE IF NOT EXISTS vpn_prices (
    product_key TEXT NOT NULL,
    role TEXT NOT NULL,
    price INTEGER NOT NULL DEFAULT 0,
    cf_price INTEGER,
    PRIMARY KEY (product_key, role)
  )`);

  // Pengaturan umum bot (key-value) — diatur admin via panel:
  // force_join_enabled, force_join_channel_id, force_join_channel_url,
  // force_join_group_id, force_join_group_url, notif_group_id,
  // reseller_min_topup
  await run(`CREATE TABLE IF NOT EXISTS bot_settings (
    key TEXT PRIMARY KEY,
    value TEXT DEFAULT ''
  )`);

  // Grup tujuan broadcast (diatur admin via panel)
  await run(`CREATE TABLE IF NOT EXISTS broadcast_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id TEXT NOT NULL UNIQUE,
    title TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
  )`);
}

// ---------- File-based cache (produk Digiflazz) ----------
const dataDir = path.join(__dirname, '../data');
const files = {
  products: path.join(dataDir, 'digiflazz-cache.json'),
  users: path.join(dataDir, 'ppob-users.json'),
  transactions: path.join(dataDir, 'ppob-txs.json'),
};

function readJson(p, def) {
  try {
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  } catch (e) {}
  return def;
}
function writeJson(p, data) {
  // Tulis atomik via file sementara + rename: crash di tengah tulis
  // tidak merusak file JSON (anti data corruption).
  try {
    fs.mkdirSync(path.dirname(p), { recursive: true });
    const tmp = p + '.tmp-' + process.pid;
    fs.writeFileSync(tmp, JSON.stringify(data));
    fs.renameSync(tmp, p);
  } catch (e) {}
}

const DEFAULT_PRODUCTS = { list_prepaid: [], list_pasca: [], lastSync: 0 };
function products() { return readJson(files.products, DEFAULT_PRODUCTS); }
function saveProducts(p) { writeJson(files.products, p); }

// ---------- Users (JSON) ----------
function users() { return readJson(files.users, {}); }
function getUser(uid) {
  const u = users();
  return u[String(uid)] || null;
}
function setUser(uid, data) {
  const u = users();
  u[String(uid)] = Object.assign({}, u[String(uid)], data);
  writeJson(files.users, u);
  return u[String(uid)];
}

// ---------- Saldo (sinkron ke SQLite users) ----------
async function addBalance(uid, amount) {
  await run(`INSERT INTO users (telegram_id, saldo) VALUES (?, ?)
    ON CONFLICT(telegram_id) DO UPDATE SET saldo = saldo + ?`,
    [uid, amount, amount]).catch(async () => {
    // fallback jika ON CONFLICT tidak didukung
    const row = await get(`SELECT saldo FROM users WHERE telegram_id = ?`, [uid]);
    if (row) await run(`UPDATE users SET saldo = saldo + ? WHERE telegram_id = ?`, [amount, uid]);
    else await run(`INSERT INTO users (telegram_id, saldo) VALUES (?, ?)`, [uid, amount]);
  });
  const row = await get(`SELECT saldo FROM users WHERE telegram_id = ?`, [uid]);
  // mirror ke JSON
  const u = getUser(uid) || {};
  u.balance = row ? row.saldo : amount;
  setUser(uid, u);
  return row ? row.saldo : amount;
}
async function deductBalance(uid, amount) {
  const row = await get(`SELECT saldo FROM users WHERE telegram_id = ?`, [uid]);
  const cur = row ? row.saldo : 0;
  if (cur < amount) return false;
  await run(`UPDATE users SET saldo = saldo - ? WHERE telegram_id = ?`, [amount, uid]);
  const u = getUser(uid) || {};
  u.balance = cur - amount;
  setUser(uid, u);
  return true;
}

// ---------- Transaksi PPOB (JSON) ----------
function txs() { return readJson(files.transactions, []); }
function addTx(tx) {
  const arr = txs();
  arr.push(Object.assign({ id: Date.now().toString(36), created: Date.now() }, tx));
  writeJson(files.transactions, arr);
  return arr[arr.length - 1];
}
function getTx(id) { return txs().find(t => String(t.id) === String(id)) || null; }
function updateTx(id, patch) {
  const arr = txs();
  const i = arr.findIndex(t => String(t.id) === String(id));
  if (i >= 0) { arr[i] = Object.assign({}, arr[i], patch); writeJson(files.transactions, arr); return arr[i]; }
  return null;
}
function pendingPayments() { return txs().filter(t => t.status === 'pending' && t.kind === 'payment'); }
function pendingProducts() { return txs().filter(t => t.status === 'pending' && t.kind === 'product'); }

module.exports = { db, run, get, all, init,
  // ===== Kompatibilitas PPOB Aji (registerPPOB) =====
  files, products, saveProducts,
  getUser, setUser, users,
  addBalance, deductBalance,
  addTx, getTx, updateTx, txs,
  pendingPayments, pendingProducts,
};
