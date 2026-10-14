// ============================================================
// Modul PPOB — saldo, deposit QRIS, beli pulsa/paket via Digiflazz
// ============================================================
const crypto = require('crypto');
const axios = require('axios');
const QRCode = require('qrcode');
const config = require('../src/config');
const digi = require('../src/digiflazz');
const { run, get, all } = require('../src/db');

const refId = (prefix = 'TRX') =>
  `${prefix}${Date.now().toString(36).toUpperCase()}${crypto.randomBytes(3).toString('hex').toUpperCase()}`;

// ---------- Saldo ----------
async function getSaldo(telegramId) {
  const row = await get('SELECT saldo FROM users WHERE telegram_id = ?', [telegramId]);
  return row?.saldo || 0;
}

async function addSaldo(telegramId, amount) {
  await run(
    `INSERT INTO users (telegram_id, saldo) VALUES (?, ?)
     ON CONFLICT(telegram_id) DO UPDATE SET saldo = saldo + ?`,
    [telegramId, amount, amount]
  );
  return getSaldo(telegramId);
}

async function deductSaldo(telegramId, amount) {
  const saldo = await getSaldo(telegramId);
  if (saldo < amount) return { success: false, message: `❌ Saldo kurang. Saldo: ${digi.rp(saldo)}` };
  await run('UPDATE users SET saldo = saldo - ? WHERE telegram_id = ?', [amount, telegramId]);
  return { success: true, saldo: saldo - amount };
}

// ---------- Deposit via QRIS P2P Gateway ----------
async function createDeposit(telegramId, amount) {
  const { gatewayUrl, apiKey } = config.p2p;
  if (!apiKey) return { success: false, message: '❌ Gateway QRIS belum dikonfigurasi.' };
  const ref = refId('DEP');
  const { data } = await axios.post(
    `${gatewayUrl}/api/deposit`,
    { amount, ref_id: ref, telegram_id: telegramId },
    { headers: { 'X-API-Key': apiKey }, timeout: 20000 }
  ).catch(() => ({ data: {} }));
  if (!data?.qr_string && !data?.qr_url) {
    return { success: false, message: '❌ Gagal membuat QRIS deposit.' };
  }
  await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, status) VALUES (?,?,?,?,?)',
    [telegramId, 'deposit', amount, ref, 'pending']);
  const qrBuffer = data.qr_string
    ? await QRCode.toBuffer(data.qr_string, { width: 300 })
    : null;
  return { success: true, ref, amount, qrBuffer, qrUrl: data.qr_url };
}

// ---------- Beli produk ----------
async function buyProduct(telegramId, buyerSkuCode, customerNo, priceSell) {
  const cek = await deductSaldo(telegramId, priceSell);
  if (!cek.success) return cek;
  const ref = refId('PPOB');
  await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, status) VALUES (?,?,?,?,?)',
    [telegramId, 'ppob', priceSell, ref, 'pending']);
  try {
    const res = await digi.transaction(buyerSkuCode, customerNo, ref);
    const status = (res?.data?.status || '').toLowerCase();
    if (status === 'sukses' || status === 'success') {
      await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['success', ref]);
      return { success: true, message: `✅ Transaksi sukses!\nRef: <code>${ref}</code>\nSN: <code>${res.data.sn || '-'}</code>` };
    }
    if (status === 'pending') {
      return { success: true, pending: true, ref, message: `⏳ Transaksi pending.\nRef: <code>${ref}</code>\nCek status dengan /cekorder ${ref}` };
    }
    // gagal -> refund
    await addSaldo(telegramId, priceSell);
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['failed', ref]);
    return { success: false, message: `❌ Transaksi gagal: ${res?.data?.message || 'unknown'}. Saldo dikembalikan.` };
  } catch (e) {
    await addSaldo(telegramId, priceSell);
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['failed', ref]);
    return { success: false, message: `❌ Error: ${e.message}. Saldo dikembalikan.` };
  }
}

async function checkOrder(ref) {
  const tx = await get('SELECT * FROM transactions WHERE ref_id = ?', [ref]);
  if (!tx) return { success: false, message: '❌ Ref tidak ditemukan.' };
  if (tx.status !== 'pending') return { success: true, message: `📦 Ref <code>${ref}</code>\nStatus: <b>${tx.status}</b>` };
  try {
    const res = await digi.checkTransaction(ref);
    const status = (res?.data?.status || '').toLowerCase();
    const map = { sukses: 'success', success: 'success', gagal: 'failed', failed: 'failed' };
    const final = map[status] || 'pending';
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', [final, ref]);
    if (final === 'failed') await addSaldo(tx.telegram_id, tx.amount); // refund
    return { success: true, message: `📦 Ref <code>${ref}</code>\nStatus: <b>${final}</b>${final === 'failed' ? '\n💰 Saldo dikembalikan.' : ''}` };
  } catch (e) {
    return { success: false, message: `❌ Gagal cek: ${e.message}` };
  }
}

async function productList(category) {
  if (!digi.enabled()) return { success: false, message: '❌ Digiflazz belum dikonfigurasi.' };
  const res = await digi.priceList('prepaid', category ? { category } : {});
  const items = (res?.data || []).filter((p) => p.buyer_product_status && p.seller_product_status).slice(0, 30);
  if (!items.length) return { success: false, message: '❌ Produk tidak ditemukan.' };
  const lines = items.map((p, i) => `${i + 1}. <code>${p.buyer_sku_code}</code> — ${p.product_name}\n   ${digi.rp(p.price_sell)}`);
  return { success: true, message: `🛒 <b>Daftar Produk</b>\n\n${lines.join('\n')}\n\n<i>Beli: /beli KODE TUJUAN</i>`, items };
}

module.exports = { getSaldo, addSaldo, deductSaldo, createDeposit, buyProduct, checkOrder, productList, refId };
