// ============================================================
// Modul PPOB — saldo, deposit QRIS, beli pulsa/paket via Digiflazz
// ============================================================
const crypto = require('crypto');
const axios = require('axios');
const QRCode = require('qrcode');
const config = require('../src/config');
const digi = require('../src/digiflazz');
const { esc } = require('../src/format');
const { run, get, all, products: dbProducts } = require('../src/db');

// Harga jual = harga dasar Digiflazz (field `price`) + margin % dari config.
// (API Digiflazz TIDAK punya field `price_sell` — kode lama membaca field yang
//  tidak ada sehingga harga tampil Rp0 dan saldo user korup saat beli.)
function sellPriceOf(prod) {
  const base = Number(prod?.price || 0);
  const margin = Number(config.digiflazz?.margin || 0);
  return Math.ceil(base * (1 + margin / 100));
}

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
  const bonus = await applyTopupBonus(telegramId, amount).catch(() => 0);
  return { saldo: await getSaldo(telegramId), bonus };
}

// ---------- Role (admin / reseller / member) ----------
// Role valid: 'admin' (akses panel admin), 'reseller' (harga reseller),
// 'member' (default, harga normal). Admin utama (owner) tetap config.adminId.
const VALID_ROLES = ['admin', 'reseller', 'member'];

async function getRole(telegramId) {
  const row = await get('SELECT role FROM users WHERE telegram_id = ?', [telegramId]);
  const r = row?.role || 'member';
  return VALID_ROLES.includes(r) ? r : 'member';
}

async function setRole(telegramId, role) {
  if (!VALID_ROLES.includes(role)) {
    throw new Error(`Role tidak valid: ${role}. Pilih: ${VALID_ROLES.join(', ')}`);
  }
  await run(
    `INSERT INTO users (telegram_id, role) VALUES (?, ?)
     ON CONFLICT(telegram_id) DO UPDATE SET role = ?`,
    [telegramId, role, role]
  );
  return getRole(telegramId);
}

// ---------- Bonus Topup ----------
async function getBonusConfig() {
  const row = await get('SELECT min_topup, bonus_percent, enabled FROM bonus_config WHERE id = 1');
  return row || { min_topup: 0, bonus_percent: 0, enabled: 0 };
}

async function setBonusConfig(minTopup, percent) {
  const enabled = (Number(minTopup) > 0 && Number(percent) > 0) ? 1 : 0;
  await run('UPDATE bonus_config SET min_topup = ?, bonus_percent = ?, enabled = ? WHERE id = 1',
    [Number(minTopup) || 0, Number(percent) || 0, enabled]);
  return getBonusConfig();
}

async function applyTopupBonus(telegramId, amount) {
  const cfg = await getBonusConfig();
  if (!cfg.enabled || Number(amount) < Number(cfg.min_topup)) return 0;
  const bonus = Math.floor(Number(amount) * Number(cfg.bonus_percent) / 100);
  if (bonus > 0) {
    await run('UPDATE users SET saldo = saldo + ? WHERE telegram_id = ?', [bonus, telegramId]);
    await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, status) VALUES (?,?,?,?,?)',
      [telegramId, 'bonus', bonus, refId('BONUS'), 'success']).catch(() => {});
  }
  return bonus;
}

async function deductSaldo(telegramId, amount) {
  // Atomik: cek & potong dalam 1 query (anti race double-spend)
  const r = await run(
    'UPDATE users SET saldo = saldo - ? WHERE telegram_id = ? AND saldo >= ?',
    [amount, telegramId, amount]
  );
  if (!r.changes) {
    const saldo = await getSaldo(telegramId);
    return { success: false, message: `❌ <b>Saldo kurang.</b>\nSaldo kamu: <b>${digi.rp(saldo)}</b>` };
  }
  return { success: true, saldo: await getSaldo(telegramId) };
}

// ---------- Deposit via QRIS P2P Gateway ----------
async function createDeposit(telegramId, amount) {
  const { gatewayUrl, apiKey } = config.p2p;
  if (!apiKey) return { success: false, message: '❌ Gateway QRIS belum dikonfigurasi.' };
  // Idempoten: pakai ulang deposit pending <30 menit (anti QR ganda saat retry/timeout)
  const existing = await get(
    `SELECT ref_id, payment_id, amount FROM transactions
     WHERE telegram_id = ? AND type = 'deposit' AND status = 'pending'
       AND payment_id != '' AND created_at > datetime('now','-30 minutes')
     ORDER BY id DESC LIMIT 1`,
    [telegramId]).catch(() => null);
  let ref, paymentId;
  if (existing) {
    ref = existing.ref_id; paymentId = existing.payment_id; amount = existing.amount;
  } else {
    ref = refId('DEP');
    const { data } = await axios.post(
      `${gatewayUrl}/api/payments`,
      { amount, reference: ref },
      { headers: { 'X-API-Key': apiKey }, timeout: 20000 }
    ).catch(() => ({ data: {} }));
    if (!data?.id) {
      return { success: false, message: '❌ Gagal membuat QRIS deposit.' };
    }
    paymentId = data.id;
    await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, payment_id, status) VALUES (?,?,?,?,?,?)',
      [telegramId, 'deposit', amount, ref, paymentId, 'pending']);
  }
  const qrUrl = gatewayUrl + '/api/qr/' + paymentId + '.png';
  let qrBuffer = null;
  try {
    const qrRes = await axios.get(qrUrl, { responseType: 'arraybuffer', timeout: 20000,
      headers: { 'X-API-Key': apiKey } });
    qrBuffer = Buffer.from(qrRes.data);
  } catch (e) {}
  return { success: true, ref, amount, paymentId, qrBuffer, qrUrl };
}

// ---------- Beli produk ----------
async function buyProduct(telegramId, buyerSkuCode, customerNo, priceSell) {
  const cek = await deductSaldo(telegramId, priceSell);
  if (!cek.success) return cek;
  const ref = refId('PPOB');
  await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, sku, status) VALUES (?,?,?,?,?,?)',
    [telegramId, 'ppob', priceSell, ref, buyerSkuCode || '', 'pending']);
  try {
    const res = await digi.transaction({ sku: buyerSkuCode, customerNo, refId: ref });
    const status = (res?.status || '').toLowerCase();
    if (status === 'sukses' || status === 'success') {
      await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['success', ref]);
      return {
        success: true,
        message:
          `✅ <b>Transaksi Sukses!</b>\n` +
          `━━━━━━━━━━━━━━━━━━\n` +
          `<blockquote>📦 Produk: <code>${esc(buyerSkuCode)}</code>\n` +
          `📱 Tujuan: <code>${esc(customerNo)}</code>\n` +
          `💰 Harga: <b>${digi.rp(priceSell)}</b>\n` +
          `<blockquote>🧾 Ref: <code>${ref}</code>\n` +
          `🔑 SN: <code>${esc(res.sn || '-')}</code></blockquote>`,
      };
    }
    if (status === 'pending') {
      return {
        success: true,
        pending: true,
        ref,
        message:
          `⏳ <b>Transaksi Pending</b>\n` +
          `━━━━━━━━━━━━━━━━━━\n` +
          `🧾 Ref: <code>${ref}</code>\n\n` +
          `Cek status: <code>/cekorder ${ref}</code></blockquote>`,
      };
    }
    // gagal -> refund
    await addSaldo(telegramId, priceSell);
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['failed', ref]);
    return { success: false, message: `❌ <b>Transaksi gagal.</b>\n${esc(res?.message || 'unknown')}\n💰 Saldo dikembalikan.` };
  } catch (e) {
    await addSaldo(telegramId, priceSell);
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', ['failed', ref]);
    return { success: false, message: `❌ <b>Error:</b> ${esc(e.message)}\n💰 Saldo dikembalikan.` };
  }
}

async function checkOrder(ref) {
  const cleanRef = String(ref || '').trim().toUpperCase();
  const tx = await get('SELECT * FROM transactions WHERE ref_id = ?', [cleanRef]);
  if (!tx) return { success: false, message: '❌ Ref tidak ditemukan.', status: 'unknown' };
  if (tx.status !== 'pending') {
    return {
      success: true,
      status: tx.status,
      message:
        `📦 <b>Status Order</b>\n` +
        `━━━━━━━━━━━━━━━━━━\n` +
        `<blockquote>🧾 Ref: <code>${esc(cleanRef)}</code>\n` +
        `📌 Status: <b>${esc(tx.status)}</b>`,
    };
  }
  try {
    const res = await digi.checkTransaction(cleanRef);
    const status = (res?.status || '').toLowerCase();
    const map = { sukses: 'success', success: 'success', gagal: 'failed', failed: 'failed' };
    const final = map[status] || 'pending';
    await run('UPDATE transactions SET status = ? WHERE ref_id = ?', [final, cleanRef]);
    if (final === 'failed') await addSaldo(tx.telegram_id, tx.amount); // refund
    return {
      success: true,
      status: final,
      message:
        `📦 <b>Status Order</b>\n` +
        `━━━━━━━━━━━━━━━━━━\n` +
        `🧾 Ref: <code>${esc(cleanRef)}</code>\n` +
        `📌 Status: <b>${esc(final)}</b></blockquote>` +
        (final === 'failed' ? `\n💰 Saldo dikembalikan.` : ``),
    };
  } catch (e) {
    return { success: false, message: `❌ Gagal cek: ${esc(e.message)}` };
  }
}

// ---------- Daftar produk (dengan paginasi) ----------
const PROD_PER_PAGE = 10;

// Kategori khusus menu "Pulsa & Paket Data" (legacy, dipertahankan)
const PULSA_CATS = ['pulsa', 'data'];

// Pemetaan tombol kategori → filter produk.
// Prioritas: field `category` Digiflazz; fallback: keyword di category/brand/product_name.
const norm = (s) => String(s || '').toLowerCase();
const hasKw = (p, ...kws) => {
  const hay = `${p.category || ''} ${p.brand || ''} ${p.product_name || ''}`.toLowerCase();
  return kws.some((k) => hay.includes(k));
};
const CATEGORY_GROUPS = {
  'perdana':   { title: '📱 <b>Perdana</b>',        match: (p) => hasKw(p, 'perdana', 'aktivasi perdana') },
  'voucher':   { title: '🎫 <b>Voucher</b>',        match: (p) => norm(p.category) === 'voucher' || hasKw(p, 'voucher') },
  'kuota':     { title: '📶 <b>Kuota / Paket Data</b>', match: (p) => ['data'].includes(norm(p.category)) || hasKw(p, 'kuota', 'paket data', 'internet') },
  'e-money':   { title: '💳 <b>E-Money</b>',        match: (p) => norm(p.category) === 'e-money' || hasKw(p, 'e-money', 'emoney', 'e money', 'ovo', 'gopay', 'dana', 'shopeepay', 'linkaja') },
  'game':      { title: '🎮 <b>Game</b>',           match: (p) => ['games', 'game'].includes(norm(p.category)) || hasKw(p, 'game', 'games', 'mobile legend', 'free fire', 'pubg', 'diamond', 'voucher game') },
  'gas':       { title: '🔥 <b>Gas</b>',            match: (p) => norm(p.category) === 'gas' || hasKw(p, 'gas') },
  'masa-aktif':{ title: '📅 <b>Masa Aktif</b>',     match: (p) => hasKw(p, 'masa aktif', 'masaaktif', 'perpanjangan masa') },
  'sms-telp':  { title: '📞 <b>SMS & Telp</b>',     match: (p) => hasKw(p, 'sms', 'telpon', 'telepon', 'paket sms', 'nelpon') },
  'pln':       { title: '⚡ <b>PLN</b>',            match: (p) => norm(p.category) === 'pln' || hasKw(p, 'pln', 'token listrik', 'listrik') },
  'pulsa':     { title: '📱 <b>Pulsa</b>',          match: (p) => norm(p.category) === 'pulsa' || hasKw(p, 'pulsa') },
  'tv':        { title: '📺 <b>TV</b>',             match: (p) => norm(p.category) === 'tv' || hasKw(p, 'tv', 'k vision', 'nex parabola', 'transvision') },
};
// Urutan tombol kategori di menu (2 kolom)
const CATEGORY_ORDER = [
  ['perdana', 'voucher'],
  ['kuota', 'e-money'],
  ['game', 'gas'],
  ['masa-aktif', 'sms-telp'],
  ['pln', 'pulsa'],
  ['tv', 'voucher'],
];
// Label tombol kategori (boleh dioverride via ppob-layout.js)
const CATEGORY_LABELS = {
  'perdana': 'Perdana', 'voucher': 'Voucher', 'kuota': 'Kuota', 'e-money': 'E-Money',
  'game': 'Game', 'gas': 'Gas', 'masa-aktif': 'Masa Aktif', 'sms-telp': 'SMS & Telp',
  'pln': 'PLN', 'pulsa': 'Pulsa', 'tv': 'TV',
};

async function productList(group, page = 1, opts = {}) {
  // group: nama kategori (lihat CATEGORY_GROUPS), 'pulsa' (legacy: pulsa+data),
  //   'lainnya', 'prabayar', 'pascabayar', 'populer', 'cari:<keyword>', atau kosong = semua
  if (!digi.enabled()) return { success: false, message: '❌ Digiflazz belum dikonfigurasi.' };
  // Baca dari cache lokal — API Digiflazz membatasi pengecekan pricelist,
  // jadi JANGAN panggil API setiap buka daftar produk (dulu selalu error limit).
  const cached = dbProducts();
  const g = String(group || '').toLowerCase();

  // Tentukan sumber daftar: prabayar vs pascabayar
  const usePasca = g === 'pascabayar';
  let rawList = usePasca ? (cached.list_pasca || []) : (cached.list_prepaid || []);
  const stale = !cached.lastSync || Date.now() - cached.lastSync > 6 * 3600 * 1000;
  if (!rawList.length || stale) {
    // Sync di background; pakai cache lama sementara bila ada
    digi.sync().catch(() => {});
    if (!rawList.length) {
      const fresh = dbProducts();
      rawList = usePasca ? (fresh.list_pasca || []) : (fresh.list_prepaid || []);
      if (!rawList.length) return { success: false, message: '⏳ Sinkronisasi produk berjalan, coba lagi 1 menit.' };
    }
  }

  let items = (Array.isArray(rawList) ? rawList : [])
    .filter((p) => p && p.buyer_product_status && p.seller_product_status);

  // Filter kategori
  if (g === 'pulsa') {
    items = items.filter((p) => PULSA_CATS.includes(norm(p.category)));
  } else if (g === 'lainnya') {
    items = items.filter((p) => !PULSA_CATS.includes(norm(p.category)));
  } else if (g === 'prabayar') {
    // sudah dari list_prepaid — tidak perlu filter tambahan
  } else if (g === 'pascabayar') {
    // sudah dari list_pasca — tidak perlu filter tambahan
  } else if (g === 'populer') {
    items = await popularItems(items);
  } else if (g.startsWith('cari:')) {
    const kw = g.slice(5).trim();
    items = searchItems(items, kw);
  } else if (CATEGORY_GROUPS[g]) {
    const m = CATEGORY_GROUPS[g].match;
    items = items.filter((p) => m(p));
  }
  // else: kosong = semua

  items = items
    .slice(0, 100)
    .map((p) => { p.price_sell = sellPriceOf(p); return p; });
  if (!items.length) return { success: false, message: '❌ Produk tidak ditemukan.' };
  const total = items.length;
  const pages = Math.max(1, Math.ceil(total / PROD_PER_PAGE));
  const pg = Math.min(Math.max(1, Number(page) || 1), pages);
  const slice = items.slice((pg - 1) * PROD_PER_PAGE, pg * PROD_PER_PAGE);
  const lines = slice.map((p, i) => {
    const n = (pg - 1) * PROD_PER_PAGE + i + 1;
    return `${n}. <code>${esc(p.buyer_sku_code)}</code> — ${esc(p.product_name)}\n   💰 ${digi.rp(p.price_sell)}`;
  });
  const grpDef = CATEGORY_GROUPS[g];
  const title = grpDef ? grpDef.title
    : g === 'pulsa' ? '📱 <b>Pulsa & Paket Data</b>'
    : g === 'lainnya' ? '🛍️ <b>Produk Lainnya</b>'
    : g === 'prabayar' ? '🔵 <b>Prabayar</b>'
    : g === 'pascabayar' ? '🟣 <b>Pascabayar</b>'
    : g === 'populer' ? '🔥 <b>Produk Populer</b>'
    : g.startsWith('cari:') ? `🔍 <b>Hasil: ${esc(g.slice(5))}</b>`
    : `🛒 <b>Daftar Produk</b>`;
  const message =
    `${title}\n` +
    `📄 Halaman <b>${pg}</b> dari <b>${pages}</b> • ${total} produk\n` +
    `━━━━━━━━━━━━━━━━━━\n\n<blockquote>${lines.join('\n')}</blockquote>\n\n` +
    `<i>Tap tombol 🛒 di bawah untuk beli</i>`;
  return { success: true, message, items, pageItems: slice, page: pg, pages, total };
}

// Cari produk berdasar keyword di nama/sku/brand
function searchItems(items, keyword) {
  const kw = String(keyword || '').toLowerCase().trim();
  if (!kw) return [];
  const parts = kw.split(/\s+/);
  return items.filter((p) => {
    const hay = `${p.product_name || ''} ${p.buyer_sku_code || ''} ${p.brand || ''} ${p.category || ''}`.toLowerCase();
    return parts.every((w) => hay.includes(w));
  });
}

// Produk populer: urut berdasar jumlah pembelian sukses di transactions.sku
async function popularItems(items) {
  try {
    const rows = await all(
      `SELECT sku, COUNT(*) AS cnt FROM transactions
       WHERE type = 'ppob' AND status = 'success' AND sku IS NOT NULL AND sku != ''
       GROUP BY sku ORDER BY cnt DESC LIMIT 20`
    ).catch(() => []);
    if (!rows || !rows.length) return items.slice(0, 10); // fallback
    const rank = new Map(rows.map((r, i) => [String(r.sku), rows.length - i]));
    const bySku = new Map(items.map((p) => [String(p.buyer_sku_code), p]));
    const ranked = [];
    for (const [sku] of rank) {
      if (bySku.has(sku)) ranked.push(bySku.get(sku));
    }
    // Tambah sisa produk agar daftar tetap penuh bila data sedikit
    for (const p of items) {
      if (ranked.length >= 20) break;
      if (!ranked.includes(p)) ranked.push(p);
    }
    return ranked;
  } catch (e) {
    return items.slice(0, 10);
  }
}

// Keyboard produk: tombol beli per produk + paginasi (format reply_markup mentah)
function productKeyboard(page, pages, items, group) {
  const g = group || '';
  const kb = [];
  // Tombol beli per produk (2 kolom)
  if (Array.isArray(items)) {
    for (let i = 0; i < items.length; i += 2) {
      const row = [];
      for (let j = i; j < Math.min(i + 2, items.length); j++) {
        const p = items[j];
        const label = ('🛒 ' + p.product_name).slice(0, 30);
        row.push({ text: label, callback_data: 'prod_buy_' + g + '_' + page + '_' + j });
      }
      kb.push(row);
    }
  }
  const nav = [];
  if (page > 1) nav.push({ text: '◀️ Prev', callback_data: `prod_page_${g}_${page - 1}` });
  if (page < pages) nav.push({ text: 'Next ▶️', callback_data: `prod_page_${g}_${page + 1}` });
  if (nav.length) kb.push(nav);
  kb.push([{ text: '🔙 Kembali', callback_data: 'menu_ppob' }]);
  return { inline_keyboard: kb };
}

// ---------- Riwayat transaksi ----------
const TYPE_LABEL = {
  deposit: '💰 Deposit',
  ppob: '🛒 PPOB',
  vpn: '🔑 VPN',
  sewa: '📦 Sewa',
};

const STATUS_ICON = {
  success: '✅',
  pending: '⏳',
  failed: '❌',
};

async function getHistory(telegramId, limit = 10) {
  const lim = Math.min(Math.max(1, Number(limit) || 10), 30);
  const rows = await all(
    'SELECT type, amount, ref_id, status, created_at FROM transactions WHERE telegram_id = ? ORDER BY id DESC LIMIT ?',
    [telegramId, lim]
  );
  if (!rows.length) {
    return { success: true, message: '📋 <b>Riwayat Transaksi</b>\n\n<i>Belum ada transaksi.</i>' };
  }
  const lines = rows.map((t) => {
    const icon = STATUS_ICON[t.status] || '•';
    const label = TYPE_LABEL[t.type] || t.type || '-';
    return `${icon} ${label} — <b>${digi.rp(t.amount || 0)}</b>\n   <code>${esc(t.ref_id || '-')}</code> • ${esc(t.status || '-')}`;
  });
  return {
    success: true,
    message:
      `📋 <b>Riwayat Transaksi</b> (${rows.length})\n` +
      `━━━━━━━━━━━━━━━━━━\n<blockquote>${lines.join('\n\n')}</blockquote>`,
  };
}

module.exports = { getSaldo, addSaldo, deductSaldo, createDeposit, buyProduct, checkOrder, productList, productKeyboard, refId, getHistory, getRole, setRole, VALID_ROLES, getBonusConfig, setBonusConfig, applyTopupBonus, CATEGORY_GROUPS, CATEGORY_ORDER, CATEGORY_LABELS, searchItems };
