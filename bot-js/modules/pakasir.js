// ============================================================
// Pakasir — payment link service (QRIS & Virtual Account)
// API: https://app.pakasir.com
//   POST /api/transactioncreate/{method}  body: {project, order_id, amount, api_key}
//   GET  /api/transactiondetail?project=&amount=&order_id=&api_key=
//   POST /api/transactioncancel           body: {project, order_id, amount, api_key}
// Metode: qris, bni_va, bri_va, cimb_niaga_va, maybank_va, permata_va,
//         bnc_va, sampoerna_va, atm_bersama_va, artha_graha_va
// Status: pending | completed | cancelled | expired
// ============================================================
const axios = require('axios');
const { get, run } = require('../src/db');

const BASE_URL = 'https://app.pakasir.com';
const TIMEOUT = 20000;

// ---------- Config (DB) ----------
async function getConfig() {
  const row = await get('SELECT slug, api_key, enabled FROM pakasir_config WHERE id = 1').catch(() => null);
  return {
    slug: row?.slug || '',
    api_key: row?.api_key || '',
    enabled: !!row?.enabled,
  };
}

async function setConfig(slug, apiKey) {
  await run(
    `INSERT INTO pakasir_config (id, slug, api_key) VALUES (1, ?, ?)
     ON CONFLICT(id) DO UPDATE SET slug = excluded.slug, api_key = excluded.api_key`,
    [String(slug || '').trim(), String(apiKey || '').trim()]
  );
}

async function setEnabled(enabled) {
  await run(
    `INSERT INTO pakasir_config (id, enabled) VALUES (1, ?)
     ON CONFLICT(id) DO UPDATE SET enabled = excluded.enabled`,
    [enabled ? 1 : 0]
  );
}

async function isReady() {
  const c = await getConfig();
  return !!(c.slug && c.api_key && c.enabled);
}

// Masking API key: tampilkan 4 karakter terakhir saja
function maskKey(key) {
  if (!key) return '(kosong)';
  const k = String(key);
  if (k.length <= 4) return '****';
  return '****' + k.slice(-4);
}

// ---------- API calls ----------
function apiError(e) {
  const status = e?.response?.status;
  const msg = e?.response?.data?.message || e?.response?.data?.error || e?.message || 'unknown';
  if (status === 401 || status === 403) return new Error('API key salah / tidak valid (401/403).');
  if (status === 404) return new Error('Project slug tidak ditemukan (404).');
  if (!e?.response) return new Error('Gagal konek ke Pakasir (network/timeout).');
  return new Error(`Pakasir error ${status}: ${msg}`);
}

// Buat payment link. method default 'qris'.
async function createPayment(amount, orderId, method = 'qris') {
  const c = await getConfig();
  if (!c.slug || !c.api_key) throw new Error('Pakasir belum dikonfigurasi (slug/API key kosong).');
  if (!amount || amount <= 0) throw new Error('Nominal tidak valid.');
  if (!orderId) throw new Error('order_id wajib diisi.');
  try {
    const { data } = await axios.post(
      `${BASE_URL}/api/transactioncreate/${method}`,
      { project: c.slug, order_id: orderId, amount, api_key: c.api_key },
      { timeout: TIMEOUT, headers: { 'User-Agent': 'wendi-bot-js/1.0' } }
    );
    const p = data?.payment || data || {};
    return {
      orderId: p.order_id || p.orderId || orderId,
      amount: p.amount || amount,
      fee: p.fee || 0,
      totalPayment: p.total_payment || p.totalPayment || amount,
      method: p.method || method,
      paymentNumber: p.payment_number || p.paymentNumber || '', // QRIS string / nomor VA
      paymentUrl: `${BASE_URL}/pay/${encodeURIComponent(c.slug)}/${amount}?order_id=${encodeURIComponent(orderId)}`,
      expiredAt: p.expired_at || p.expiredAt || null,
      raw: p,
    };
  } catch (e) { throw apiError(e); }
}

// Cek status transaksi. Pakasir kirim api_key via query param (sesuai spek resmi).
async function checkStatus(orderId, amount) {
  const c = await getConfig();
  if (!c.slug || !c.api_key) throw new Error('Pakasir belum dikonfigurasi.');
  try {
    const { data } = await axios.get(`${BASE_URL}/api/transactiondetail`, {
      params: { project: c.slug, order_id: orderId, amount, api_key: c.api_key },
      timeout: TIMEOUT,
      headers: { 'User-Agent': 'wendi-bot-js/1.0' },
    });
    const t = data?.transaction || data || {};
    const st = String(t.status || '').toLowerCase();
    return {
      status: ['pending', 'completed', 'cancelled', 'expired'].includes(st) ? st : 'pending',
      raw: t,
    };
  } catch (e) { throw apiError(e); }
}

// Batalkan transaksi pending
async function cancelPayment(orderId, amount) {
  const c = await getConfig();
  if (!c.slug || !c.api_key) throw new Error('Pakasir belum dikonfigurasi.');
  try {
    const { data } = await axios.post(
      `${BASE_URL}/api/transactioncancel`,
      { project: c.slug, order_id: orderId, amount, api_key: c.api_key },
      { timeout: TIMEOUT, headers: { 'User-Agent': 'wendi-bot-js/1.0' } }
    );
    return { success: true, raw: data?.transaction || data };
  } catch (e) { throw apiError(e); }
}

// Tes koneksi: buat payment Rp1.000 lalu batalkan. Validasi full flow.
async function testConnection() {
  const c = await getConfig();
  if (!c.slug) return { success: false, message: '❌ Slug belum diisi.' };
  if (!c.api_key) return { success: false, message: '❌ API key belum diisi.' };
  const orderId = 'TEST-' + Date.now();
  const amount = 1000;
  try {
    const p = await createPayment(amount, orderId, 'qris');
    try { await cancelPayment(orderId, amount); } catch (_) {}
    return {
      success: true,
      message: `✅ <b>Koneksi OK!</b>\n🔗 Project: <code>${c.slug}</code>\n💰 Test Rp1.000 berhasil dibuat & dibatalkan.`,
      paymentUrl: p.paymentUrl,
    };
  } catch (e) {
    return { success: false, message: `❌ Tes gagal: ${e.message}` };
  }
}

module.exports = {
  BASE_URL,
  getConfig, setConfig, setEnabled, isReady, maskKey,
  createPayment, checkStatus, cancelPayment, testConnection,
};
