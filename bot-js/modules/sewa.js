// ============================================================
// Modul Sewa Script VPN — paket, bayar QRIS, aktivasi lisensi
// Alur: pilih paket -> bayar QRIS (P2P gateway) -> input username+IP
//        -> order pending -> fulfillment cron aktivasi lisensi
// ============================================================
const crypto = require('crypto');
const axios = require('axios');
const config = require('../src/config');
const digi = require('../src/digiflazz');
const { run, get, all } = require('../src/db');

const PACKAGES = [
  { days: 30, price: 10000 },
  { days: 60, price: 20000 },
  { days: 90, price: 30000 },
];

const refId = (prefix = 'SEWA') =>
  `${prefix}${Date.now().toString(36).toUpperCase()}${crypto.randomBytes(3).toString('hex').toUpperCase()}`;

async function initTable() {
  await run(`CREATE TABLE IF NOT EXISTS sewa_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    username TEXT,
    ip TEXT,
    days INTEGER,
    amount INTEGER,
    payment_ref TEXT UNIQUE,
    payment_id TEXT,
    status TEXT DEFAULT 'pending',
    expiry TEXT,
    created_at TEXT DEFAULT (datetime('now'))
  )`);
}

// ---------- Buat order sewa + QRIS ----------
async function createSewaOrder(telegramId, username, ip, days) {
  const pkg = PACKAGES.find((p) => p.days === days);
  if (!pkg) return { success: false, message: '❌ Paket tidak valid.' };
  const { gatewayUrl, apiKey } = config.p2p;
  if (!apiKey) return { success: false, message: '❌ Gateway QRIS belum dikonfigurasi.' };

  const ref = refId('SEWA');
  const { data } = await axios.post(
    `${gatewayUrl}/api/payments`,
    { amount: pkg.price, reference: ref },
    { headers: { 'X-API-Key': apiKey }, timeout: 20000 }
  ).catch(() => ({ data: {} }));

  if (!data?.id) return { success: false, message: '❌ Gagal membuat QRIS. Coba lagi.' };

  await run(
    `INSERT INTO sewa_orders (telegram_id, username, ip, days, amount, payment_ref, payment_id, status)
     VALUES (?,?,?,?,?,?,?,?)`,
    [telegramId, username, ip, days, pkg.price, ref, data.id, 'pending']
  );

  const qrUrl = `${gatewayUrl}/api/qr/${data.id}.png`;
  let qrBuffer = null;
  try {
    const qrRes = await axios.get(qrUrl, {
      responseType: 'arraybuffer', timeout: 20000,
      headers: { 'X-API-Key': apiKey },
    });
    qrBuffer = Buffer.from(qrRes.data);
  } catch (e) {}

  return {
    success: true, ref, paymentId: data.id,
    amount: pkg.price, uniqueAmount: data.uniqueAmount,
    days, username, ip, qrBuffer, qrUrl,
  };
}

// ---------- Cek status pembayaran di gateway ----------
async function checkSewaPayment(paymentId) {
  const { gatewayUrl, apiKey } = config.p2p;
  const { data } = await axios.get(
    `${gatewayUrl}/api/payments/${paymentId}`,
    { headers: { 'X-API-Key': apiKey }, timeout: 15000 }
  ).catch(() => ({ data: {} }));
  return (data?.status || 'unknown').toLowerCase();
}

async function markSewaPaid(ref) {
  await run(`UPDATE sewa_orders SET status = 'paid' WHERE payment_ref = ?`, [ref]);
}

async function markSewaFulfilled(ref, expiry) {
  await run(`UPDATE sewa_orders SET status = 'fulfilled', expiry = ? WHERE payment_ref = ?`, [expiry, ref]);
}

async function getSewaOrder(ref) {
  return get(`SELECT * FROM sewa_orders WHERE payment_ref = ?`, [ref]);
}

async function mySewaOrders(telegramId) {
  return all(`SELECT * FROM sewa_orders WHERE telegram_id = ? ORDER BY id DESC LIMIT 10`, [telegramId]);
}

async function pendingSewaOrders() {
  return all(`SELECT * FROM sewa_orders WHERE status = 'paid' ORDER BY id ASC`);
}

// ---------- Validasi ----------
function validUsername(u) {
  return /^[a-zA-Z0-9]{3,20}$/.test(u || '');
}

function validIp(ip) {
  const parts = (ip || '').trim().split('.');
  if (parts.length !== 4) return false;
  return parts.every((p) => /^\d{1,3}$/.test(p) && Number(p) >= 0 && Number(p) <= 255);
}

function packageListText() {
  return PACKAGES.map((p, i) =>
    `${i + 1}. <b>${p.days} hari</b> — ${digi.rp(p.price)}`
  ).join('\n');
}

module.exports = {
  PACKAGES, initTable, createSewaOrder, checkSewaPayment,
  markSewaPaid, markSewaFulfilled, getSewaOrder,
  mySewaOrders, pendingSewaOrders, validUsername, validIp, packageListText,
};
