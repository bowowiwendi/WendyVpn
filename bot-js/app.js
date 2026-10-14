// ============================================================
// 🤖 WENDI VPN BOT (@IdWendi_bot)
// Bot Telegram VPN + PPOB — Node.js + Telegraf
//
// Fitur:
//  • VPN: SSH, VMess, VLess, Trojan (+ mode CloudFront)
//  • Trial / Create / Renew / Akun Saya
//  • PPOB: deposit QRIS, saldo, beli pulsa/paket (Digiflazz)
//  • Cek kuota HP (Sidompul)
//  • Admin: broadcast, tambah saldo, statistik, auto-cleanup
// ============================================================
require('dotenv').config();
const fs = require('fs');
const path = require('path');

const { Telegraf, Markup } = require('telegraf');
const config = require('./src/config');
const { init: initDb } = require('./src/db');
const vpn = require('./modules/vpn');
const ppob = require('./modules/ppob');
const kuota = require('./modules/kuota');
const admin = require('./modules/admin');
const cleanup = require('./modules/cleanup');
const sewa = require('./modules/sewa');
const digi = require('./src/digiflazz');

if (!config.botToken) {
  console.error('❌ BOT_TOKEN belum diisi di .env');
  process.exit(1);
}

const bot = new Telegraf(config.botToken);
const sessions = new Map(); // chatId -> { step, data }
const lastMenus = new Map();
// Helper aman untuk answerCbQuery (thrown sync oleh Telegraf bila bukan callback_query)
const safeCb = async (ctx) => {
  try { await ctx.answerCbQuery(); } catch (e) { /* ignore */ }
};
// Helper tombol berwarna (Bot API 9.4+: primary=biru, success=hijau, danger=merah)
const sBtn = (text, data, style) => {
  const b = Markup.button.callback(text, data);
  if (style) b.style = style;
  return b;
};

 // userId -> messageId (menu bergambar terakhir)
const ASSETS_DIR = path.join(__dirname, 'assets');

// ---------- Helper: kirim menu bergambar (ala BotVPN2) ----------
async function sendMenuPhoto(ctx, imageFile, caption, keyboard) {
  const userId = ctx.from?.id;
  const chatId = ctx.chat?.id;
  const imgPath = path.join(ASSETS_DIR, imageFile);
  const replyMarkup = keyboard.reply_markup || keyboard;

  // hapus menu lama
  if (userId && lastMenus.has(userId)) {
    try { await ctx.telegram.deleteMessage(chatId, lastMenus.get(userId)); } catch (e) {}
    lastMenus.delete(userId);
  }

  // jika dari callback query, hapus pesan callback dulu
  if (ctx.updateType === 'callback_query' && ctx.callbackQuery?.message?.message_id) {
    try { await ctx.telegram.deleteMessage(chatId, ctx.callbackQuery.message.message_id); } catch (e) {}
  }

  let sent = null;
  try {
    if (fs.existsSync(imgPath)) {
      sent = await ctx.replyWithPhoto(
        { source: fs.createReadStream(imgPath) },
        { caption, parse_mode: 'HTML', reply_markup: replyMarkup }
      );
    } else {
      throw new Error('gambar tidak ada');
    }
  } catch (e) {
    // fallback ke teks biasa
    sent = await ctx.reply(caption, { parse_mode: 'HTML', reply_markup: replyMarkup });
  }
  if (userId && sent?.message_id) lastMenus.set(userId, sent.message_id);
  return sent;
}

// ---------- Helper ----------
const mainMenu = () =>
  Markup.inlineKeyboard([
    [sBtn('🟢 VPN Premium', 'menu_vpn', 'primary'), sBtn('☁️ VPN CloudFront', 'menu_cf', 'primary')],
    [sBtn('🟡 PPOB & Pulsa', 'menu_ppob', 'success'), sBtn('🔵 Cek Kuota', 'menu_kuota', 'primary')],
    [sBtn('🟣 Akun Saya', 'menu_akun', 'success'), sBtn('🟠 Statistik', 'menu_stat', 'primary')],
    [sBtn('💰 Sewa Script VPN', 'menu_sewa', 'success')],
  ]);

const backBtn = () => Markup.inlineKeyboard([[sBtn('🔙 Kembali', 'menu_main', 'danger')]]);

const vpnMenu = (cf = false) => {
  const p = cf ? 'cf_' : '';
  return Markup.inlineKeyboard([
    [sBtn('🔴 SSH', `${p}mk_ssh`, 'danger'), sBtn('🟢 VMess', `${p}mk_vmess`, 'success')],
    [sBtn('🔵 VLess', `${p}mk_vless`, 'primary'), sBtn('🟡 Trojan', `${p}mk_trojan`, 'success')],
    [sBtn('🎁 Trial Gratis 1 Hari', `${p}mk_trial`, 'success')],
    [sBtn('🔙 Kembali', 'menu_main', 'danger')],
  ]);
};

const ensureUser = async (ctx) => {
  const { run } = require('./src/db');
  await run('INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)',
    [ctx.from.id, ctx.from.username || ctx.from.first_name || '']);
};

// ---------- /start ----------
const WELCOME_CAPTION = (name) =>
`👋 Halo <b>${name}</b>!

🛰 <b>WENDI VPN BOT</b> 🛰
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:

🟢 <b>VPN Premium</b> — SSH / VMess / VLess / Trojan
☁️ <b>VPN CloudFront</b> — trafik disamarkan HTTPS
🟡 <b>PPOB & Pulsa</b> — isi pulsa, paket data, PLN
🔵 <b>Cek Kuota</b> — cek kuota semua operator
💰 <b>Sewa Script</b> — lisensi script VPN
━━━━━━━━━━━━━━━━━━
<code>🌐 dikelola oleh Wendi Network</code>`;

bot.start(async (ctx) => {
  await ensureUser(ctx);
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-utama.png',
    WELCOME_CAPTION(ctx.from.first_name || 'kawan'), mainMenu());
});

bot.action('menu_main', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-utama.png',
    `🏠 <b>MENU UTAMA</b>
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:`, mainMenu());
});

// ---------- Menu VPN ----------
bot.action('menu_vpn', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-vpn.png',
    `🟢 <b>VPN PREMIUM</b>
━━━━━━━━━━━━━━━━━━
` +
    `🔴 <b>SSH</b> — cepat & stabil
` +
    `🟢 <b>VMess</b> — protokol V2Ray
` +
    `🔵 <b>VLess</b> — ringan & cepat
` +
    `🟡 <b>Trojan</b> — aman & anti-blokir

` +
    `Pilih protokol di bawah ini:`, vpnMenu(false));
});

bot.action('menu_cf', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-cf.png',
    `☁️ <b>VPN via CLOUDFRONT</b>
━━━━━━━━━━━━━━━━━━
` +
    `Trafik disamarkan sebagai <b>HTTPS CloudFront</b> —
` +
    `sulit dideteksi & diblokir.

` +
    `🔴 <b>SSH</b>  🟢 <b>VMess</b>
` +
    `🔵 <b>VLess</b>  🟡 <b>Trojan</b>

` +
    `Pilih protokol di bawah ini:`, vpnMenu(true));
});

// ---------- Buat akun VPN ----------
const PROTO_LABEL = { ssh: 'SSH', vmess: 'VMess', vless: 'VLess', trojan: 'Trojan' };

async function handleCreate(ctx, proto, viaCF) {
  const chatId = ctx.chat.id;
  sessions.set(chatId, { step: 'vpn_username', proto, viaCF });
  await ctx.reply(
    `✏️ <b>Buat Akun ${PROTO_LABEL[proto]}${viaCF ? ' (CloudFront)' : ''}</b>\n\n` +
      `Kirim <b>username</b> (3-20 karakter, huruf/angka):`,
    { parse_mode: 'HTML' }
  );
  await safeCb(ctx);
}

for (const proto of ['ssh', 'vmess', 'vless', 'trojan']) {
  bot.action(`mk_${proto}`, (ctx) => handleCreate(ctx, proto, false));
  bot.action(`cf_mk_${proto}`, (ctx) => handleCreate(ctx, proto, true));
}

bot.action('mk_trial', async (ctx) => {
  await safeCb(ctx);
  const username = 'trial' + Math.random().toString(36).slice(2, 7);
  const password = Math.random().toString(36).slice(2, 10);
  const r = await vpn.createSSH(username, password, 1, 1).catch((e) => ({ success: false, message: `❌ ${e.message}` }));
  if (r.success) {
    await vpn.saveAccount(ctx.from.id, 'ssh', username, r.expiry, 1, 0);
    r.message += `\n\n<i>🎁 Trial 1 hari. Upgrade untuk masa aktif lebih lama.</i>`;
  }
  await ctx.reply(r.message, { parse_mode: 'HTML' });
});

bot.action('cf_mk_trial', async (ctx) => {
  await safeCb(ctx);
  const username = 'trial' + Math.random().toString(36).slice(2, 7);
  const password = Math.random().toString(36).slice(2, 10);
  // Trial CF: buat akun SSH biasa lalu tampilkan info CF
  const r = await vpn.createSSH(username, password, 1, 1).catch(() => ({ success: false }));
  const info = vpn.cfSSHInfo(username, password, 1);
  if (info.success) {
    await vpn.saveAccount(ctx.from.id, 'ssh', username, info.expiry, 1, 1);
    info.message += `\n\n<i>🎁 Trial 1 hari via CloudFront.</i>`;
  }
  await ctx.reply(info.message, { parse_mode: 'HTML' });
});

// ---------- Terima input teks (session) ----------
bot.on('text', async (ctx) => {
  const chatId = ctx.chat.id;
  const sess = sessions.get(chatId);

  // --- Session buat akun VPN ---
  if (sess?.step === 'vpn_username') {
    const username = ctx.message.text.trim();
    if (!vpn.validUser(username)) {
      return ctx.reply('❌ Username tidak valid (3-20 karakter, huruf/angka). Coba lagi:');
    }
    if (sess.proto === 'ssh') {
      sess.data = { username };
      sess.step = 'vpn_password';
      return ctx.reply('Kirim <b>password</b> untuk akun SSH:', { parse_mode: 'HTML' });
    }
    return finishCreateVpn(ctx, sess, username);
  }

  if (sess?.step === 'vpn_password') {
    const password = ctx.message.text.trim();
    if (password.length < 4) return ctx.reply('❌ Password minimal 4 karakter. Coba lagi:');
    return finishCreateVpn(ctx, sess, sess.data.username, password);
  }

  // --- Session cek kuota ---
  if (sess?.step === 'kuota_nomor') {
    sessions.delete(chatId);
    const r = await kuota.cekKuota(ctx.message.text.trim());
    return ctx.reply(r.message, { parse_mode: 'HTML' });
  }

  // --- Session sewa: username lisensi ---
  if (sess?.step === 'sewa_username') {
    const username = ctx.message.text.trim();
    if (!sewa.validUsername(username)) {
      return ctx.reply('❌ Username tidak valid (3-20 karakter, huruf/angka). Coba lagi:');
    }
    sess.data = { username };
    sess.step = 'sewa_ip';
    return ctx.reply('Kirim <b>IP VPS</b> kamu (contoh: 103.150.116.158):', { parse_mode: 'HTML' });
  }

  if (sess?.step === 'sewa_ip') {
    const ip = ctx.message.text.trim();
    if (!sewa.validIp(ip)) {
      return ctx.reply('❌ IP tidak valid. Contoh: 103.150.116.158\nCoba lagi:');
    }
    const { days, data } = sess;
    const { username } = data;
    sessions.delete(chatId);
    await ctx.reply('⏳ Membuat QRIS pembayaran...');
    const r = await sewa.createSewaOrder(ctx.from.id, username, ip, days).catch((e) => ({ success: false, message: `❌ ${e.message}` }));
    if (!r.success) return ctx.reply(r.message);
    const caption =
      `💰 <b>Sewa Script ${r.days} Hari</b>\n` +
      `👤 Username: <code>${r.username}</code>\n` +
      `🖥️ IP VPS: <code>${r.ip}</code>\n` +
      `💵 Bayar: <b>${digi.rp(r.uniqueAmount || r.amount)}</b>\n` +
      `Ref: <code>${r.ref}</code>\n\n` +
      `Scan QRIS di atas untuk bayar, lalu tekan tombol cek di bawah.`;
    const kb = Markup.inlineKeyboard([[sBtn('✅ Cek Pembayaran', `sewa_cek_${r.ref}`, 'success')]]);
    if (r.qrBuffer) return ctx.replyWithPhoto({ source: r.qrBuffer }, { caption, parse_mode: 'HTML', reply_markup: kb.reply_markup });
    return ctx.reply(caption + `\n${r.qrUrl || ''}`, { parse_mode: 'HTML', reply_markup: kb.reply_markup });
  }


  // --- Session beli PPOB: kode produk ---
  if (sess?.step === 'ppob_kode') {
    sess.data.kode = ctx.message.text.trim().toUpperCase();
    sess.step = 'ppob_tujuan';
    return ctx.reply('Kirim <b>nomor tujuan</b>:', { parse_mode: 'HTML' });
  }

  if (sess?.step === 'ppob_tujuan') {
    const tujuan = ctx.message.text.trim();
    const { kode } = sess.data;
    sessions.delete(chatId);
    await ctx.reply('⏳ Memproses transaksi...');
    // Cari harga dari daftar terakhir (disederhanakan: pakai priceList)
    const list = await ppob.productList().catch(() => ({ items: [] }));
    const prod = (list.items || []).find((p) => p.buyer_sku_code.toUpperCase() === kode);
    if (!prod) return ctx.reply('❌ Kode produk tidak ditemukan. Lihat /produk');
    const r = await ppob.buyProduct(ctx.from.id, kode, tujuan, prod.price_sell);
    return ctx.reply(r.message, { parse_mode: 'HTML' });
  }

  // --- Session deposit nominal ---
  if (sess?.step === 'deposit_nominal') {
    const nominal = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    sessions.delete(chatId);
    if (!nominal || nominal < 10000) return ctx.reply('❌ Nominal minimal Rp10.000');
    await ctx.reply('⏳ Membuat QRIS...');
    const r = await ppob.createDeposit(ctx.from.id, nominal);
    if (!r.success) return ctx.reply(r.message);
    const caption = `💳 <b>Deposit ${digi.rp(nominal)}</b>\nRef: <code>${r.ref}</code>\n\nScan QRIS di atas untuk bayar. Saldo masuk otomatis setelah pembayaran terdeteksi.`;
    if (r.qrBuffer) return ctx.replyWithPhoto({ source: r.qrBuffer }, { caption, parse_mode: 'HTML' });
    return ctx.reply(caption + `\n${r.qrUrl || ''}`, { parse_mode: 'HTML' });
  }
});

async function finishCreateVpn(ctx, sess, username, password = '') {
  sessions.delete(ctx.chat.id);
  const { proto, viaCF } = sess;
  await ctx.reply('⏳ Membuat akun...');
  let r;
  try {
    if (proto === 'ssh') {
      r = viaCF
        ? vpn.cfSSHInfo(username, password, 30)
        : await vpn.createSSH(username, password, 30, 1);
      // Untuk mode CF, akun SSH tetap dibuat di server dulu
      if (viaCF && r.success) await vpn.createSSH(username, password, 30, 1).catch(() => {});
    } else if (proto === 'vmess') r = await vpn.createVMess(username, 30, viaCF);
    else if (proto === 'vless') r = await vpn.createVLess(username, 30, viaCF);
    else r = await vpn.createTrojan(username, 30, viaCF);
  } catch (e) {
    r = { success: false, message: `❌ Error: ${e.message}` };
  }
  if (r.success) await vpn.saveAccount(ctx.from.id, proto, username, r.expiry, 0, viaCF ? 1 : 0);
  await ctx.reply(r.message, { parse_mode: 'HTML' });
}

// ---------- Menu Sewa Script ----------
bot.action('menu_sewa', async (ctx) => {
  await safeCb(ctx);
  const orders = await sewa.mySewaOrders(ctx.from.id).catch(() => []);
  const aktif = orders.filter((o) => o.status === 'fulfilled');
  const lines = aktif.slice(0, 3).map((o) =>
    `• <code>${o.username}</code> (${o.ip}) — ${o.days} hari${o.expiry ? ` s/d ${o.expiry}` : ''}`
  );
  await sendMenuPhoto(ctx, 'menu-sewa.png',
    `💰 <b>SEWA SCRIPT VPN</b>\n━━━━━━━━━━━━━━━━━━\n\n` +
    `📦 <b>Daftar Paket:</b>\n${sewa.packageListText()}\n\n` +
    (lines.length ? `📋 <b>Sewamu (aktif):</b>\n${lines.join('\n')}\n\n` : ``) +
    `Pilih paket di bawah ini:`,
    Markup.inlineKeyboard([
      [sBtn('📦 30 Hari', 'sewa_pkg_30', 'primary'), sBtn('📦 60 Hari', 'sewa_pkg_60', 'primary')],
      [sBtn('📦 90 Hari', 'sewa_pkg_90', 'primary')],
      [sBtn('📋 Status Sewaku', 'sewa_status', 'success')],
      [sBtn('🔙 Kembali', 'menu_main', 'danger')],
    ]));
});

for (const d of [30, 60, 90]) {
  bot.action(`sewa_pkg_${d}`, async (ctx) => {
    await safeCb(ctx);
    const pkg = sewa.PACKAGES.find((p) => p.days === d);
    sessions.set(ctx.chat.id, { step: 'sewa_username', days: d });
    await ctx.reply(
      `💰 <b>Sewa Script — ${d} Hari</b>\n` +
      `💵 Harga: <b>${digi.rp(pkg.price)}</b>\n\n` +
      `Kirim <b>username lisensi</b> (3-20 karakter, huruf/angka):`,
      { parse_mode: 'HTML' }
    );
  });
}

bot.action('sewa_status', async (ctx) => {
  await safeCb(ctx);
  const orders = await sewa.mySewaOrders(ctx.from.id).catch(() => []);
  if (!orders.length) {
    return ctx.reply('📭 Kamu belum pernah sewa script.', { parse_mode: 'HTML' });
  }
  const stMap = { pending: '⏳ menunggu bayar', paid: '✅ lunas, aktivasi segera', fulfilled: '🟢 aktif', failed: '❌ gagal' };
  const lines = orders.map((o, i) =>
    `${i + 1}. <code>${o.username || '-'}</code> (${o.ip || '-'})\n` +
    `   📦 ${o.days} hari — ${stMap[o.status] || o.status}${o.expiry ? ` s/d ${o.expiry}` : ''}`
  );
  await ctx.reply(`💰 <b>Status Sewa Script</b>\n━━━━━━━━━━━━━━━━━━\n\n${lines.join('\n')}`, { parse_mode: 'HTML' });
});

// Cek pembayaran sewa: sewa_cek_<ref>
bot.action(/^sewa_cek_(.+)$/, async (ctx) => {
  await safeCb(ctx);
  const ref = ctx.match[1];
  const order = await sewa.getSewaOrder(ref).catch(() => null);
  if (!order) return ctx.reply('❌ Order tidak ditemukan.');
  if (order.status === 'fulfilled') return ctx.reply('✅ Lisensimu sudah aktif!');
  if (order.status === 'paid') return ctx.reply('✅ Sudah lunas! Lisensi sedang diproses, tunggu notifikasi.');
  const st = await sewa.checkSewaPayment(order.payment_id).catch(() => 'unknown');
  if (st === 'paid' || st === 'success' || st === 'settled') {
    await sewa.markSewaPaid(ref);
    return ctx.reply(
      `✅ <b>Pembayaran diterima!</b>\n\nLisensi <code>${order.username}</code> (${order.ip}) ` +
      `sedang diproses. Kamu akan dapat notifikasi saat aktif.`,
      { parse_mode: 'HTML' }
    );
  }
  await ctx.reply(`⏳ Belum ada pembayaran terdeteksi (status: ${st}).\nScan QRIS dulu, lalu tekan tombol cek lagi.`);
});

// ---------- Admin: daftar sewa ----------
bot.command('sewalist', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const { all } = require('./src/db');
  const rows = await all(`SELECT * FROM sewa_orders ORDER BY id DESC LIMIT 15`).catch(() => []);
  if (!rows.length) return ctx.reply('📭 Belum ada order sewa.');
  const lines = rows.map((o, i) =>
    `${i + 1}. <code>${o.username || '-'}</code> ${o.ip || '-'} — ${o.days}hr [${o.status}]`
  );
  await ctx.reply(`💰 <b>Order Sewa Terakhir</b>\n\n${lines.join('\n')}`, { parse_mode: 'HTML' });
});


// ---------- Akun Saya ----------
bot.action('menu_akun', async (ctx) => {
  await safeCb(ctx);
  const rows = await vpn.myAccounts(ctx.from.id);
  if (!rows.length) {
    return sendMenuPhoto(ctx, 'menu-akun.png',
      `🟣 <b>AKUN SAYA</b>
━━━━━━━━━━━━━━━━━━

📭 Kamu belum punya akun VPN.
Buat dulu di menu VPN ya!`, backBtn());
  }
  const lines = rows.map((a, i) =>
    `${i + 1}. <b>${a.proto.toUpperCase()}</b> <code>${a.username}</code>\n   📅 Exp: ${a.expiry}${a.via_cf ? ' ☁️CF' : ''}${a.is_trial ? ' 🎁trial' : ''}`
  );
  await sendMenuPhoto(ctx, 'menu-akun.png',
    `🟣 <b>AKUN SAYA</b>
━━━━━━━━━━━━━━━━━━

${lines.join('\n')}`, backBtn());
});

// ---------- Menu PPOB ----------
bot.action('menu_ppob', async (ctx) => {
  await safeCb(ctx);
  const saldo = await ppob.getSaldo(ctx.from.id);
  await sendMenuPhoto(ctx, 'menu-ppob.png',
    `🟡 <b>PPOB & PULSA</b>
━━━━━━━━━━━━━━━━━━
` +
    `💰 Saldo: <b>${digi.rp(saldo)}</b>

` +
    `🟢 <b>Deposit</b> — top up saldo via QRIS
` +
    `🛒 <b>Beli</b> — pulsa, paket data, token PLN
` +
    `📦 <b>Cek Order</b> — lacak transaksimu

` +
    `Pilih layanan:`,
    Markup.inlineKeyboard([
      [sBtn('🟢 Deposit / Top Up', 'ppob_deposit', 'success'), sBtn('🛒 Beli Pulsa/Paket', 'ppob_beli', 'primary')],
      [sBtn('🔵 Cek Order', 'ppob_cekorder', 'primary'), sBtn('🟣 Daftar Produk', 'ppob_produk', 'success')],
      [sBtn('🔙 Kembali', 'menu_main', 'danger')],
    ]));
});

bot.action('ppob_deposit', async (ctx) => {
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'deposit_nominal' });
  await ctx.reply('💰 Kirim <b>nominal deposit</b> (min Rp10.000):', { parse_mode: 'HTML' });
});

bot.action('ppob_beli', async (ctx) => {
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'ppob_kode', data: {} });
  await ctx.reply('🛒 Kirim <b>kode produk</b> (lihat /produk):', { parse_mode: 'HTML' });
});

bot.action('ppob_produk', async (ctx) => {
  await safeCb(ctx);
  const r = await ppob.productList().catch((e) => ({ success: false, message: `❌ ${e.message}` }));
  await ctx.reply(r.message.slice(0, 4000), { parse_mode: 'HTML' });
});

bot.action('ppob_cekorder', async (ctx) => {
  await safeCb(ctx);
  await ctx.reply('📦 Kirim <b>ref order</b> dengan perintah:\n<code>/cekorder REFID</code>', { parse_mode: 'HTML' });
});

bot.command('cekorder', async (ctx) => {
  const ref = ctx.message.text.split(' ')[1];
  if (!ref) return ctx.reply('Contoh: <code>/cekorder PPOBABC123</code>', { parse_mode: 'HTML' });
  const r = await ppob.checkOrder(ref.trim().toUpperCase());
  await ctx.reply(r.message, { parse_mode: 'HTML' });
});

bot.command('saldo', async (ctx) => {
  const s = await ppob.getSaldo(ctx.from.id);
  await ctx.reply(`💰 Saldo kamu: <b>${digi.rp(s)}</b>`, { parse_mode: 'HTML' });
});

bot.command('produk', async (ctx) => {
  const r = await ppob.productList().catch((e) => ({ success: false, message: `❌ ${e.message}` }));
  await ctx.reply(r.message.slice(0, 4000), { parse_mode: 'HTML' });
});

bot.command('beli', async (ctx) => {
  const [, kode, tujuan] = ctx.message.text.split(' ');
  if (!kode || !tujuan) return ctx.reply('Contoh: <code>/beli TLKM5 083153170199</code>', { parse_mode: 'HTML' });
  const list = await ppob.productList().catch(() => ({ items: [] }));
  const prod = (list.items || []).find((p) => p.buyer_sku_code.toUpperCase() === kode.toUpperCase());
  if (!prod) return ctx.reply('❌ Kode produk tidak ditemukan. Lihat /produk');
  await ctx.reply('⏳ Memproses...');
  const r = await ppob.buyProduct(ctx.from.id, kode.toUpperCase(), tujuan, prod.price_sell);
  await ctx.reply(r.message, { parse_mode: 'HTML' });
});

// ---------- Cek Kuota ----------
bot.action('menu_kuota', async (ctx) => {
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'kuota_nomor' });
  await ctx.reply('📡 Kirim <b>nomor HP</b> (contoh: 083153170199):', { parse_mode: 'HTML' });
});

// ---------- Statistik (admin lihat global, user lihat ringkas) ----------
bot.action('menu_stat', async (ctx) => {
  await safeCb(ctx);
  if (admin.isAdmin(ctx)) {
    const s = await admin.statistik();
    return sendMenuPhoto(ctx, 'menu-stat.png',
      `🟠 <b>STATISTIK SERVER</b>
━━━━━━━━━━━━━━━━━━

${s}`, backBtn());
  }
  const rows = await vpn.myAccounts(ctx.from.id);
  await sendMenuPhoto(ctx, 'menu-stat.png',
    `🟠 <b>STATISTIK</b>
━━━━━━━━━━━━━━━━━━

📊 Kamu punya <b>${rows.length}</b> akun VPN aktif.`, backBtn());
});

// ---------- Admin commands ----------
bot.command('broadcast', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const text = ctx.message.text.replace('/broadcast', '').trim();
  if (!text) return ctx.reply('Contoh: /broadcast Halo semua!');
  const ids = await admin.broadcastList();
  let ok = 0;
  for (const id of ids) {
    try { await ctx.telegram.sendMessage(id, `📢 <b>Pengumuman</b>\n\n${text}`, { parse_mode: 'HTML' }); ok++; }
    catch { /* skip blocked */ }
    await new Promise((r) => setTimeout(r, 50));
  }
  await ctx.reply(`✅ Broadcast terkirim ke ${ok}/${ids.length} user.`);
});

bot.command('addsaldo', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const [, uid, amt] = ctx.message.text.split(' ');
  if (!uid || !amt) return ctx.reply('Contoh: <code>/addsaldo 123456 50000</code>', { parse_mode: 'HTML' });
  const s = await ppob.addSaldo(Number(uid), Number(amt));
  await ctx.reply(`✅ Saldo user <code>${uid}</code> kini ${digi.rp(s)}`, { parse_mode: 'HTML' });
});

bot.command('cleanup', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const dry = ctx.message.text.includes('dry');
  if (dry) {
    const r = await cleanup.dryRun();
    const e = r.expired.map((a) => `• ${a.proto}/${a.username} exp ${a.expiry}`).join('\n') || '—';
    return ctx.reply(`🧹 <b>DRY RUN</b>\n\nKadaluarsa:\n${e}\n\nTrial menumpuk: ${r.oldTrials.length}`, { parse_mode: 'HTML' });
  }
  await ctx.reply('🧹 Membersihkan...');
  const t = await cleanup.cleanupOldTrials();
  const x = await cleanup.cleanupExpired(async (acc) => {
    try {
      await ctx.telegram.sendMessage(acc.telegram_id,
        `⏰ Akun <b>${acc.proto}/${acc.username}</b> telah kadaluarsa dan dihapus.`, { parse_mode: 'HTML' });
    } catch { /* ignore */ }
  });
  await ctx.reply(`✅ Selesai.\n🗑️ Trial menumpuk: ${t.deleted}\n⏰ Kadaluarsa: ${x.deleted} (notif: ${x.notified})`);
});

// ---------- Auto-cleanup harian (cron dalam proses) ----------
setInterval(async () => {
  try {
    await cleanup.cleanupOldTrials();
    await cleanup.cleanupExpired(async (acc) => {
      try {
        await bot.telegram.sendMessage(acc.telegram_id,
          `⏰ Akun <b>${acc.proto}/${acc.username}</b> telah kadaluarsa dan dihapus.`, { parse_mode: 'HTML' });
      } catch { /* ignore */ }
    });
    console.log('[cleanup] auto-cleanup jalan', new Date().toISOString());
  } catch (e) {
    console.error('[cleanup] error:', e.message);
  }
}, 24 * 60 * 60 * 1000); // tiap 24 jam

// ---------- Error handler ----------
bot.catch((err, ctx) => {
  console.error('Bot error:', err.message);
  ctx?.reply?.('❌ Terjadi kesalahan. Coba lagi.').catch(() => {});
});

// ---------- Start ----------
(async () => {
  await initDb();
  await sewa.initTable().catch((e) => console.error('sewa table:', e.message));
  console.log('✅ Database siap');
  await bot.launch();
  console.log('🤖 Bot Wendi berjalan (@IdWendi_bot)');
})();

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
