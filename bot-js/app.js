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
// Grup wajib join & grup notifikasi
const GROUP_WAJIB = '@Wendi_VPN';
const GROUP_NOTIF = -1002068435369; // ID grup Wendi_VPN
const { init: initDb } = require('./src/db');
const vpn = require('./modules/vpn');
const ppob = require('./modules/ppob');
const kuota = require('./modules/kuota');
const admin = require('./modules/admin');
const cleanup = require('./modules/cleanup');
const sewa = require('./modules/sewa');
const hc = require('./modules/hc');
const hcCache = new Map(); // userId_proto_username -> {proto, username, uuid, password}
const prodCache = new Map(); // userId -> {pageItems: [...], page}
const digi = require('./src/digiflazz');
const { esc } = require('./src/format');

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
const mainMenu = (isAdmin = false) => {
  const rows = [
    [sBtn('🟢 VPN Premium', 'menu_vpn', 'primary'), sBtn('☁️ VPN CloudFront', 'menu_cf', 'primary')],
    [sBtn('🟡 PPOB & Pulsa', 'menu_ppob', 'success'), sBtn('🔵 Cek Kuota', 'menu_kuota', 'primary')],
    [sBtn('🟣 Akun Saya', 'menu_akun', 'success'), sBtn('🟠 Statistik', 'menu_stat', 'primary')],
    [sBtn('💰 Sewa Script VPN', 'menu_sewa', 'success')],
  ];
  if (isAdmin) rows.push([sBtn('🛠️ Panel Admin', 'adm_open', 'danger')]);
  return Markup.inlineKeyboard(rows);
};

const backBtn = () => Markup.inlineKeyboard([[sBtn('🔙 Kembali', 'menu_main', 'danger')]]);

// ---------- Panel Admin ----------
const adminPanel = () => Markup.inlineKeyboard([
  [sBtn('➕ Tambah Server', 'adm_addserver', 'success'), sBtn('❌ Hapus Server', 'adm_delserver', 'danger')],
  [sBtn('💲 Edit Harga', 'adm_editharga', 'primary'), sBtn('📝 Edit Nama', 'adm_editnama', 'primary')],
  [sBtn('🌐 Edit Domain', 'adm_editdomain', 'primary'), sBtn('📋 List Server', 'adm_listserver', 'success')],
  [sBtn('💵 Tambah Saldo', 'adm_addsaldo', 'success'), sBtn('➖ Kurangi Saldo', 'adm_minsaldo', 'danger')],
  [sBtn('📊 Hasil Penjualan', 'adm_sales', 'primary'), sBtn('📑 Log Topup', 'adm_topuplog', 'primary')],
  [sBtn('📦 Backup DB', 'adm_backupdb', 'success'), sBtn('♻️ Restore DB', 'adm_restoredb', 'danger')],
  [sBtn('🔙 Kembali', 'menu_main', 'danger')],
]);

// Helper: ambil daftar server
async function getServers() {
  const { all } = require('./src/db');
  return all('SELECT * FROM servers ORDER BY id');
}

const vpnMenu = (cf = false) => {
  const p = cf ? 'cf_' : '';
  return Markup.inlineKeyboard([
    [sBtn('🔴 SSH', `${p}mk_ssh`, 'danger'), sBtn('🟢 VMess', `${p}mk_vmess`, 'success')],
    [sBtn('🔵 VLess', `${p}mk_vless`, 'primary'), sBtn('🟡 Trojan', `${p}mk_trojan`, 'success')],
    [sBtn('🟣 Shadowsocks', `${p}mk_shadowsocks`, 'primary')],
    [sBtn('⚡ Zivpn UDP', `${p}mk_zivpn`, 'success')],
    [sBtn('💰 Topup Saldo', 'ppob_deposit', 'success')],
    [sBtn('🔙 Kembali', 'menu_main', 'danger')],
  ]);
};

// Cek apakah user sudah join grup wajib (admin selalu lolos)
async function checkGroupMember(ctx) {
  try {
    // Admin bypass - tidak perlu join
    if (await admin.isAdmin(ctx)) return true;
    const m = await ctx.telegram.getChatMember(GROUP_WAJIB, ctx.from.id);
    return ['member', 'administrator', 'creator'].includes(m.status);
  } catch (e) {
    // Jika bot bukan member grup / error API, anggap lolos agar tidak blokir semua user
    // (log error untuk debugging)
    console.error('checkGroupMember error:', e.message);
    return true;
  }
}

const ensureUser = async (ctx) => {
  const { run } = require('./src/db');
  await run('INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)',
    [ctx.from.id, ctx.from.username || ctx.from.first_name || '']);
};

// ---------- /start ----------
const WELCOME_CAPTION = (name) =>
`👋 Halo <b>${esc(name)}</b>!

🛰 <b>WENDI VPN BOT</b> 🛰
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:

<blockquote>🟢 <b>VPN Premium</b> — SSH / VMess / VLess / Trojan
☁️ <b>VPN CloudFront</b> — trafik disamarkan HTTPS
🟡 <b>PPOB & Pulsa</b> — isi pulsa, paket data, PLN
🔵 <b>Cek Kuota</b> — cek kuota semua operator
💰 <b>Sewa Script</b> — lisensi script VPN</blockquote>
━━━━━━━━━━━━━━━━━━
<code>🌐 dikelola oleh Wendi Network</code>`;

bot.start(async (ctx) => {
  await ensureUser(ctx);
  await safeCb(ctx);
  const joined = await checkGroupMember(ctx);
  if (!joined) {
    return ctx.reply(
      '⚠️ <b>Wajib Join Grup Dulu</b>\n\n' +
      'Untuk memakai bot ini, silakan join grup kami dulu.\n\n' +
      'Setelah join, ketik /start lagi.',
      {
        parse_mode: 'HTML',
        reply_markup: {
          inline_keyboard: [[{ text: '📢 Join Grup Wendi VPN', url: 'https://t.me/Wendi_VPN' }]]
        }
      }
    );
  }
  await sendMenuPhoto(ctx, 'menu-utama.png',
    WELCOME_CAPTION(ctx.from.first_name || 'kawan'), mainMenu(admin.isAdmin(ctx)));
});

bot.action('menu_main', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-utama.png',
    `🏠 <b>MENU UTAMA</b>
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:`, mainMenu(admin.isAdmin(ctx)));
});

// ---------- Menu VPN ----------
bot.action('menu_vpn', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-vpn.png',
    `🟢 <b>VPN PREMIUM</b>
━━━━━━━━━━━━━━━━━━
` +
    `<blockquote>🔴 <b>SSH</b> — cepat & stabil
` +
    `🟢 <b>VMess</b> — protokol V2Ray
` +
    `🔵 <b>VLess</b> — ringan & cepat
` +
    `🟡 <b>Trojan</b> — aman & anti-blokir
` +
    `🟣 <b>Shadowsocks</b> — simpel & cepat</blockquote>

` +
    `Pilih protokol di bawah ini:`, vpnMenu(false));
});

bot.action('menu_cf', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-cf.png',
    `☁️ <b>VPN via CLOUDFRONT</b>
━━━━━━━━━━━━━━━━━━
` +
    `<blockquote>☁ Trafik disamarkan sebagai <b>HTTPS CloudFront</b> —
` +
    `sulit dideteksi & diblokir.</blockquote>

` +
    `🔴 <b>SSH</b>  🟢 <b>VMess</b>
` +
    `🔵 <b>VLess</b>  🟡 <b>Trojan</b>

` +
    `Pilih protokol di bawah ini:`, vpnMenu(true));
});

// ---------- Buat akun VPN ----------
const PROTO_LABEL = { ssh: 'SSH', vmess: 'VMess', vless: 'VLess', trojan: 'Trojan', shadowsocks: 'Shadowsocks', zivpn: 'Zivpn UDP' };

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

for (const proto of ['ssh', 'vmess', 'vless', 'trojan', 'shadowsocks', 'zivpn']) {
  bot.action(`mk_${proto}`, (ctx) => handleCreate(ctx, proto, false));
  bot.action(`cf_mk_${proto}`, (ctx) => handleCreate(ctx, proto, true));
}

bot.action('mk_trial', async (ctx) => {
  await safeCb(ctx);
  await ctx.reply('❌ Trial gratis sudah dinonaktifkan.');
});

bot.action('cf_mk_trial', async (ctx) => {
  await safeCb(ctx);
  await ctx.reply('❌ Trial gratis sudah dinonaktifkan.');
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
    if (sess.proto === 'ssh' || sess.proto === 'zivpn') {
      sess.data = { username };
      sess.step = 'vpn_password';
      return ctx.reply('Kirim <b>password</b> untuk akun SSH:', { parse_mode: 'HTML' });
    }
    sess.data = { username };
    sess.step = 'vpn_days';
    return ctx.reply(
      'Masukkan <b>durasi (hari)</b>\nHarga: <b>Rp500/hari</b>\nSaldo kamu: <b>Rp' + (await ppob.getSaldo(ctx.from.id)).toLocaleString('id-ID') + '</b>',
      { parse_mode: 'HTML' }
    );
  }

  if (sess?.step === 'vpn_password') {
    const password = ctx.message.text.trim();
    if (password.length < 4) return ctx.reply('❌ Password minimal 4 karakter. Coba lagi:');
    sess.data.password = password;
    sess.step = 'vpn_days';
    return ctx.reply(
      'Masukkan <b>durasi (hari)</b>\nHarga: <b>Rp500/hari</b>\nSaldo kamu: <b>Rp' + (await ppob.getSaldo(ctx.from.id)).toLocaleString('id-ID') + '</b>',
      { parse_mode: 'HTML' }
    );
  }

  if (sess?.step === 'restore_db') {
    const doc = ctx.message.document;
    if (!doc || !doc.file_name.endsWith('.db')) {
      return ctx.reply('❌ Kirim file .db yang valid. Batalkan dengan /start');
    }
    if (!(await admin.isAdmin(ctx))) {
      sessions.delete(ctx.chat.id);
      return ctx.reply('❌ Khusus admin.');
    }
    try {
      const fs = require('fs');
      const path = require('path');
      const link = await ctx.telegram.getFileLink(doc.file_id);
      const https = require('https');
      const dbPath = path.join(__dirname, 'data', 'bot.db');
      const tmpPath = dbPath + '.restore-tmp';
      await new Promise((resolve, reject) => {
        https.get(link.href, (res) => {
          const ws = fs.createWriteStream(tmpPath);
          res.pipe(ws);
          ws.on('finish', resolve);
          ws.on('error', reject);
        }).on('error', reject);
      });
      fs.copyFileSync(tmpPath, dbPath);
      fs.unlinkSync(tmpPath);
      sessions.delete(ctx.chat.id);
      await ctx.reply('✅ Database berhasil di-restore. Bot restart...');
      setTimeout(() => process.exit(0), 1500); // pm2 akan restart otomatis
    } catch (e) {
      sessions.delete(ctx.chat.id);
      await ctx.reply(`❌ Restore gagal: ${e.message}`);
    }
    return;
  }

  if (sess?.step === 'vpn_days') {
    const days = parseInt(ctx.message.text.trim(), 10);
    if (isNaN(days) || days < 1 || days > 365) {
      return ctx.reply('❌ Durasi tidak valid (1-365 hari). Coba lagi:');
    }
    const username = sess.data.username;
    const password = sess.data.password || '';
    return finishCreateVpn(ctx, sess, username, password, days);
  }

  // --- Session renew akun ---
  if (sess?.step === 'renew_days') {
    const days = parseInt(ctx.message.text.trim(), 10);
    if (isNaN(days) || days < 1 || days > 365) {
      return ctx.reply('❌ Durasi tidak valid (1-365 hari). Coba lagi:');
    }
    return finishRenew(ctx, sess.accountId, days);
  }

  // --- Session cek kuota ---
  if (sess?.step === 'kuota_nomor') {
    sessions.delete(chatId);
    const r = await kuota.cekKuota(ctx.message.text.trim());
    return ctx.reply(r.message, { parse_mode: 'HTML' });
  }

  // --- Session beli PPOB: tujuan (tombol daftar produk ATAU input kode manual) ---
  if (sess?.step === 'ppob_tujuan') {
    const tujuan = ctx.message.text.trim();
    if (!tujuan || tujuan.length < 5) {
      return ctx.reply('❌ Nomor tujuan tidak valid. Coba lagi:');
    }
    const d = sess.data || {};
    sessions.delete(chatId);
    await ctx.reply('⏳ Memproses pembelian...');
    let sku = d.sku, price = d.price, productName = d.productName;
    if (!sku && d.kode) {
      // Alur input kode manual: cari produk & harga dari daftar
      const list = await ppob.productList().catch(() => ({ items: [] }));
      const prod = (list.items || []).find((p) => p.buyer_sku_code.toUpperCase() === String(d.kode).toUpperCase());
      if (!prod) return ctx.reply('❌ Kode produk tidak ditemukan. Lihat /produk');
      sku = prod.buyer_sku_code; price = prod.price_sell; productName = prod.product_name;
    }
    if (!sku) return ctx.reply('❌ Data produk tidak lengkap. Ulangi dari menu PPOB.');
    const r = await ppob.buyProduct(ctx.from.id, sku, tujuan, price);
    if (r.success) {
      const uname = ctx.from.username ? '@' + ctx.from.username : ctx.from.first_name;
      notifGrup(bot, `🛒 <b>Pembelian PPOB</b>\n👤 ${uname}\n📦 ${productName || sku}\n📱 ${tujuan}\n💰 Rp${Number(price).toLocaleString('id-ID')}`);
    }
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
    const r = await sewa.createSewaOrder(ctx.from.id, username, ip, days).catch((e) => ({ success: false, message: `❌ ${esc(e.message)}` }));
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




  // ============================================================
  // --- Session PANEL ADMIN ---
  // ============================================================
  // Tambah server: nama
  if (sess?.step === 'adm_addserver_nama') {
    const nama = ctx.message.text.trim();
    if (!nama || nama.length < 2) return ctx.reply('❌ Nama terlalu pendek. Coba lagi:');
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    sess.data.nama = nama;
    sess.step = 'adm_addserver_domain';
    return ctx.reply(`➕ <b>Tambah Server</b>\n\nNama: <b>${esc(nama)}</b>\n\nKetik <b>domain server</b> (contoh: sg1.wendivpn.my.id):`, { parse_mode: 'HTML' });
  }

  // Tambah server: domain
  if (sess?.step === 'adm_addserver_domain') {
    const domain = ctx.message.text.trim();
    if (!domain || domain.length < 4) return ctx.reply('❌ Domain tidak valid. Coba lagi:');
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    sess.data.domain = domain;
    sess.step = 'adm_addserver_harga';
    return ctx.reply(`➕ <b>Tambah Server</b>\n\nNama: <b>${esc(sess.data.nama)}</b>\nDomain: <code>${esc(domain)}</code>\n\nKetik <b>harga per hari</b> (angka saja, contoh: 500):`, { parse_mode: 'HTML' });
  }

  // Tambah server: harga -> simpan
  if (sess?.step === 'adm_addserver_harga') {
    const harga = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    if (!harga || harga < 0) return ctx.reply('❌ Harga tidak valid. Ketik angka saja (contoh: 500):');
    const { run } = require('./src/db');
    const r = await run('INSERT INTO servers (nama, domain, harga) VALUES (?,?,?)',
      [sess.data.nama, sess.data.domain, harga]);
    sessions.delete(chatId);
    return ctx.reply(
      `✅ <b>Server ditambahkan!</b>\n\n🆔 ID: <code>${r.id}</code>\n📝 Nama: <b>${esc(sess.data.nama)}</b>\n🌐 Domain: <code>${esc(sess.data.domain)}</code>\n💲 Harga: <b>Rp${harga.toLocaleString('id-ID')}/hari</b>`,
      { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup }
    );
  }

  // Edit harga: ketik harga baru dari keyboard
  if (sess?.step === 'adm_editharga_input') {
    const harga = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    if (!harga || harga < 0) return ctx.reply('❌ Harga tidak valid. Ketik angka saja (contoh: 500):');
    const { run, get } = require('./src/db');
    await run('UPDATE servers SET harga = ? WHERE id = ?', [harga, sess.data.serverId]);
    const s = await get('SELECT * FROM servers WHERE id = ?', [sess.data.serverId]);
    sessions.delete(chatId);
    return ctx.reply(
      `✅ <b>Harga diperbarui!</b>\n\n📝 Server: <b>${esc(s.nama)}</b>\n💲 Harga baru: <b>Rp${Number(s.harga).toLocaleString('id-ID')}/hari</b>`,
      { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup }
    );
  }

  // Edit nama: ketik nama baru
  if (sess?.step === 'adm_editnama_input') {
    const nama = ctx.message.text.trim();
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    if (!nama || nama.length < 2) return ctx.reply('❌ Nama terlalu pendek. Coba lagi:');
    const { run } = require('./src/db');
    await run('UPDATE servers SET nama = ? WHERE id = ?', [nama, sess.data.serverId]);
    sessions.delete(chatId);
    return ctx.reply(`✅ Nama server diperbarui menjadi <b>${esc(nama)}</b>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // Edit domain: ketik domain baru
  if (sess?.step === 'adm_editdomain_input') {
    const domain = ctx.message.text.trim();
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    if (!domain || domain.length < 4) return ctx.reply('❌ Domain tidak valid. Coba lagi:');
    const { run } = require('./src/db');
    await run('UPDATE servers SET domain = ? WHERE id = ?', [domain, sess.data.serverId]);
    sessions.delete(chatId);
    return ctx.reply(`✅ Domain server diperbarui menjadi <code>${esc(domain)}</code>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // Tambah saldo: format "userId jumlah"
  if (sess?.step === 'adm_addsaldo_input') {
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const parts = ctx.message.text.trim().split(/\s+/);
    const uid = Number(parts[0]);
    const amt = Number((parts[1] || '').replace(/\D/g, ''));
    if (!uid || !amt || amt <= 0) return ctx.reply('❌ Format salah. Contoh: <code>123456 50000</code>', { parse_mode: 'HTML' });
    const s = await ppob.addSaldo(uid, amt);
    sessions.delete(chatId);
    notifGrup(bot, `💰 <b>Topup Saldo</b>\n👤 ID: <code>${uid}</code>\n💵 Rp${amt.toLocaleString('id-ID')}\n✅ Saldo baru: Rp${Number(s).toLocaleString('id-ID')}`);
    return ctx.reply(`✅ Saldo user <code>${uid}</code> ditambah Rp${amt.toLocaleString('id-ID')}.\nSaldo baru: <b>${digi.rp(s)}</b>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // Kurangi saldo: format "userId jumlah"
  if (sess?.step === 'adm_minsaldo_input') {
    if (!admin.isAdmin(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const parts = ctx.message.text.trim().split(/\s+/);
    const uid = Number(parts[0]);
    const amt = Number((parts[1] || '').replace(/\D/g, ''));
    if (!uid || !amt || amt <= 0) return ctx.reply('❌ Format salah. Contoh: <code>123456 10000</code>', { parse_mode: 'HTML' });
    const cur = await ppob.getSaldo(uid);
    if (cur < amt) { sessions.delete(chatId); return ctx.reply(`❌ Saldo user <code>${uid}</code> hanya ${digi.rp(cur)}, tidak bisa dikurangi Rp${amt.toLocaleString('id-ID')}.`, { parse_mode: 'HTML' }); }
    const { run } = require('./src/db');
    await run('UPDATE users SET saldo = saldo - ? WHERE telegram_id = ?', [amt, uid]);
    const s = await ppob.getSaldo(uid);
    sessions.delete(chatId);
    return ctx.reply(`✅ Saldo user <code>${uid}</code> dikurangi Rp${amt.toLocaleString('id-ID')}.\nSaldo baru: <b>${digi.rp(s)}</b>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
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

async function finishCreateVpn(ctx, sess, username, password = '', days = 30) {
  sessions.delete(ctx.chat.id);
  const { proto, viaCF } = sess;
  // Diskon reseller 10%
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const isReseller = role === 'reseller';
  const totalHarga = Math.round(500 * days * (isReseller ? 0.9 : 1));
  // Cek saldo
  const saldo = await ppob.getSaldo(ctx.from.id);
  if (saldo < totalHarga) {
    return ctx.reply(
      `❌ <b>Saldo tidak cukup.</b>\n` +
      `💰 Harga (${days} hari): <b>Rp${totalHarga.toLocaleString('id-ID')}</b>\n` +
      `💳 Saldo kamu: <b>Rp${saldo.toLocaleString('id-ID')}</b>\n\n` +
      `Silakan topup dulu via menu <b>💰 Saldo</b>.`,
      { parse_mode: 'HTML' }
    );
  }
  await ctx.reply('⏳ Membuat akun...');
  let r;
  try {
    if (proto === 'ssh') {
      r = viaCF
        ? vpn.cfSSHInfo(username, password, days)
        : await vpn.createSSH(username, password, days, 1);
      // Untuk mode CF, akun SSH tetap dibuat di server dulu
      if (viaCF && r.success) await vpn.createSSH(username, password, days, 1).catch(() => {});
    } else if (proto === 'vmess') r = await vpn.createVMess(username, days, viaCF);
    else if (proto === 'vless') r = await vpn.createVLess(username, days, viaCF);
    else if (proto === 'shadowsocks') r = await vpn.createShadowsocks(username, days, viaCF);
    else if (proto === 'zivpn') r = await vpn.createZivpn(username, password, days);
    else r = await vpn.createTrojan(username, days, viaCF);
  } catch (e) {
    r = { success: false, message: `❌ Error: ${esc(e.message)}` };
  }
  // Potong saldo jika berhasil
  if (r.success) {
    await ppob.deductSaldo(ctx.from.id, totalHarga);
    const { run } = require('./src/db');
    await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, status) VALUES (?,?,?,?,?)',
      [ctx.from.id, 'vpn_' + proto, totalHarga, 'VPN' + Date.now().toString(36).toUpperCase(), 'success']).catch(() => {});
    // Notif ke grup
    const uname = ctx.from.username ? '@' + ctx.from.username : ctx.from.first_name;
    notifGrup(bot, `🛒 <b>Pembelian VPN</b>\n👤 ${uname}\n📦 ${proto.toUpperCase()}${viaCF ? ' (CF)' : ''} - ${days} hari\n💰 Rp${totalHarga.toLocaleString('id-ID')}`);
  }
  if (r.success) await vpn.saveAccount(ctx.from.id, proto, username, r.expiry, 0, viaCF ? 1 : 0);
  // Tombol download .hc jika berhasil dan HC tersedia
  let extra = { parse_mode: 'HTML' };
  if (r.success && hc.hcEnabled() && ['vmess', 'vless', 'trojan', 'ssh'].includes(proto)) {
    const cacheKey = ctx.from.id + '_' + proto + '_' + username;
    hcCache.set(cacheKey, {
      proto, username,
      uuid: r.uuid || '', password: r.password || '',
      domain: viaCF ? config.cloudfront.domain : config.vpn.domain,
    });
    // Hapus cache lama (max 100 entri)
    if (hcCache.size > 100) {
      const firstKey = hcCache.keys().next().value;
      hcCache.delete(firstKey);
    }
    extra.reply_markup = {
      inline_keyboard: [[
        { text: '📱 Download .hc', callback_data: 'hc_dl_' + cacheKey }
      ]]
    };
  }
  await ctx.reply(r.message, extra);
}

// Kirim notifikasi transaksi ke grup
async function notifGrup(bot, pesan) {
  try {
    await bot.telegram.sendMessage(GROUP_NOTIF, pesan, { parse_mode: 'HTML', disable_web_page_preview: true });
  } catch (e) { /* abaikan jika gagal */ }
}

// ---------- Download .hc ----------
bot.action(/^hc_dl_(.+)$/, async (ctx) => {
  await safeCb(ctx);
  const cacheKey = ctx.match[1];
  const info = hcCache.get(cacheKey);
  if (!info) {
    await ctx.reply('❌ Data akun tidak ditemukan. Buat akun baru dulu.');
    return;
  }
  // Tanya pilih config
  await ctx.reply('Pilih config untuk file .hc:', {
    reply_markup: {
      inline_keyboard: [
        [{ text: '📱 Default', callback_data: 'hc_go_default_' + cacheKey }],
        [{ text: '📚 XL EDUKASI', callback_data: 'hc_go_xl_edukasi_' + cacheKey }],
      ]
    }
  });
});

bot.action(/^hc_go_(default|xl_edukasi)_(.+)$/, async (ctx) => {
  await safeCb(ctx);
  const preset = ctx.match[1];
  const cacheKey = ctx.match[2];
  const info = hcCache.get(cacheKey);
  if (!info) {
    await ctx.reply('❌ Data akun tidak ditemukan. Buat akun baru dulu.');
    return;
  }
  await ctx.reply('⏳ Membuat file .hc...');
  const res = await hc.generateHC({
    service: info.proto,
    username: info.username,
    uuid: info.uuid,
password: info.password,
    domain: info.domain,
    preset: preset,
  });
  if (!res.success) {
    await ctx.reply('❌ ' + res.message, { parse_mode: 'HTML' });
    return;
  }
  await ctx.replyWithDocument(
    { source: res.buffer, filename: res.filename },
    { caption: '📱 File <b>' + res.filename + '</b> untuk <code>' + info.username + '</code>',
      parse_mode: 'HTML' }
  );
});

// ---------- Menu Sewa Script ----------
bot.action('menu_sewa', async (ctx) => {
  await safeCb(ctx);
  const orders = await sewa.mySewaOrders(ctx.from.id).catch(() => []);
  const orderList = Array.isArray(orders) ? orders : [];
  const aktif = orderList.filter((o) => o && o.status === 'fulfilled');
  const lines = aktif.slice(0, 3).map((o) =>
    `• <code>${esc(o.username)}</code> (<code>${esc(o.ip)}</code>) — ${o.days} hari${o.expiry ? ` s/d ${o.expiry}` : ''}`
  );
  await sendMenuPhoto(ctx, 'menu-sewa.png',
    `💰 <b>SEWA SCRIPT VPN</b>\n━━━━━━━━━━━━━━━━━━\n\n` +
    `📦 <b>Daftar Paket:</b>\n<blockquote>${sewa.packageListText()}</blockquote>\n\n` +
    (lines.length ? `📋 <b>Sewamu (aktif):</b>\n<blockquote>${lines.join('\n')}</blockquote>\n\n` : ``) +
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
    `${i + 1}. <code>${esc(o.username || '-')}</code> (<code>${esc(o.ip || '-')}</code>)\n` +
    `   📦 ${o.days} hari — ${stMap[o.status] || esc(o.status)}${o.expiry ? ` s/d ${o.expiry}` : ''}`
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
      `✅ <b>Pembayaran diterima!</b>\n\nLisensi <code>${esc(order.username)}</code> (<code>${esc(order.ip)}</code>) ` +
      `sedang diproses. Kamu akan dapat notifikasi saat aktif.`,
      { parse_mode: 'HTML' }
    );
  }
  await ctx.reply(`⏳ Belum ada pembayaran terdeteksi (status: <code>${esc(st)}</code>).\nScan QRIS dulu, lalu tekan tombol cek lagi.`, { parse_mode: 'HTML' });
});

// ---------- Admin: daftar sewa ----------
bot.command('sewalist', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const { all } = require('./src/db');
  const rows = await all(`SELECT * FROM sewa_orders ORDER BY id DESC LIMIT 15`).catch(() => []);
  const orderRows = Array.isArray(rows) ? rows : [];
  if (!orderRows.length) return ctx.reply('📭 Belum ada order sewa.');
  const lines = orderRows.map((o, i) =>
    `${i + 1}. <code>${o.username || '-'}</code> ${o.ip || '-'} — ${o.days}hr [${esc(o.status)}]`
  );
  await ctx.reply(`💰 <b>Order Sewa Terakhir</b>\n\n${lines.join('\n')}`, { parse_mode: 'HTML' });
});


// ---------- Akun Saya (dengan paginasi) ----------
const AKUN_PER_PAGE = 10;
function akunKeyboard(page, pages, slice = []) {
  const row = [];
  if (page > 1) row.push({ text: '◀️ Prev', callback_data: `akun_page_${page - 1}` });
  if (page < pages) row.push({ text: 'Next ▶️', callback_data: `akun_page_${page + 1}` });
  const kb = [];
  if (row.length) kb.push(row);
  // Tombol renew per akun (2 kolom)
  for (let i = 0; i < slice.length; i += 2) {
    const r = [];
    for (let j = i; j < Math.min(i + 2, slice.length); j++) {
      const a = slice[j];
      r.push({ text: `♻️ ${a.username}`.slice(0, 30), callback_data: `renew_${a.id}` });
    }
    kb.push(r);
  }
  kb.push([{ text: '🔙 Kembali', callback_data: 'menu_main' }]);
  return { inline_keyboard: kb };
}
function akunPageText(rows, page) {
  const pages = Math.max(1, Math.ceil(rows.length / AKUN_PER_PAGE));
  const pg = Math.min(Math.max(1, Number(page) || 1), pages);
  const slice = rows.slice((pg - 1) * AKUN_PER_PAGE, pg * AKUN_PER_PAGE);
  const lines = slice.map((a, i) => {
    const n = (pg - 1) * AKUN_PER_PAGE + i + 1;
    return `${n}. <b>${esc(a.proto.toUpperCase())}</b> <code>${esc(a.username)}</code>\n   📅 Exp: ${esc(a.expiry)}${a.via_cf ? ' ☁️CF' : ''}${a.is_trial ? ' 🎁trial' : ''}`;
  });
  return {
    text: `🟣 <b>AKUN SAYA</b>\n━━━━━━━━━━━━━━━━━━\n📄 Halaman <b>${pg}</b> dari <b>${pages}</b>\n\n<blockquote>${lines.join('\n')}</blockquote>`,
    page: pg, pages, slice,
  };
}
bot.action('menu_akun', async (ctx) => {
  await safeCb(ctx);
  const rows = await vpn.myAccounts(ctx.from.id);
  if (!rows.length) {
    return sendMenuPhoto(ctx, 'menu-akun.png',
      `🟣 <b>AKUN SAYA</b>\n━━━━━━━━━━━━━━━━━━\n\n📭 Kamu belum punya akun VPN.\nBuat dulu di menu VPN ya!`, backBtn());
  }
  const { text, page, pages, slice } = akunPageText(rows, 1);
  await sendMenuPhoto(ctx, 'menu-akun.png', text, { reply_markup: akunKeyboard(page, pages, slice) });
});
bot.action(/^akun_page_(\d+)$/, async (ctx) => {
  await safeCb(ctx);
  const rows = await vpn.myAccounts(ctx.from.id);
  if (!rows.length) return;
  const { text, page, pages, slice } = akunPageText(rows, parseInt(ctx.match[1], 10));
  const extra = { parse_mode: 'HTML', reply_markup: akunKeyboard(page, pages, slice) };
  try { await ctx.editMessageCaption(text, extra); }
  catch (e1) {
    try { await ctx.editMessageText(text, extra); }
    catch (e2) { await ctx.reply(text, extra); }
  }
});

// ---------- Renew Akun ----------
bot.action(/^renew_(\d+)$/, async (ctx) => {
  await safeCb(ctx);
  const { get } = require('./src/db');
  const acc = await get('SELECT * FROM vpn_accounts WHERE id = ? AND telegram_id = ?', [ctx.match[1], ctx.from.id]);
  if (!acc) return ctx.reply('❌ Akun tidak ditemukan.');
  sessions.set(ctx.chat.id, { step: 'renew_days', accountId: acc.id });
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const disc = role === 'reseller' ? ' (diskon 10% reseller)' : '';
  await ctx.reply(
    `♻️ <b>Renew Akun</b>\n\n` +
    `F464 Username: <code>${esc(acc.username)}</code>\n` +
    `📅 Exp saat ini: <code>${esc(acc.expiry)}</code>\n\n` +
    `Harga: <b>Rp500/hari</b>${disc}\n` +
    `Kirim <b>durasi perpanjangan (hari)</b>:`,
    { parse_mode: 'HTML' }
  );
});

async function finishRenew(ctx, accountId, days) {
  sessions.delete(ctx.chat.id);
  const { get, run } = require('./src/db');
  const acc = await get('SELECT * FROM vpn_accounts WHERE id = ? AND telegram_id = ?', [accountId, ctx.from.id]);
  if (!acc) return ctx.reply('❌ Akun tidak ditemukan.');
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const totalHarga = Math.round(500 * days * (role === 'reseller' ? 0.9 : 1));
  const saldo = await ppob.getSaldo(ctx.from.id);
  if (saldo < totalHarga) {
    return ctx.reply(
      `❌ <b>Saldo tidak cukup.</b>\n` +
      `💰 Harga (${days} hari): <b>Rp${totalHarga.toLocaleString('id-ID')}</b>\n` +
      `💳 Saldo kamu: <b>Rp${saldo.toLocaleString('id-ID')}</b>`,
      { parse_mode: 'HTML' }
    );
  }
  // Hitung expiry baru: tambah hari ke expiry saat ini (atau dari sekarang jika sudah lewat)
  const now = new Date();
  const cur = new Date(acc.expiry + 'T00:00:00');
  const base = (cur > now) ? cur : now;
  base.setDate(base.getDate() + days);
  const newExpiry = base.toISOString().slice(0, 10);
  await ctx.reply('⏳ Memperpanjang akun...');
  // Coba API renew (best effort)
  try {
    const axios = require('axios');
    const config = require('./src/config');
    await axios.get(`${config.vpn.apiBase}/renew`, {
      params: { auth: config.vpn.apiAuth, proto: acc.proto, user: acc.username, exp: days },
      timeout: 25000,
    }).catch(() => {});
  } catch (e) {}
  await run('UPDATE vpn_accounts SET expiry = ? WHERE id = ?', [newExpiry, accountId]);
  await ppob.deductSaldo(ctx.from.id, totalHarga);
  await run('INSERT INTO transactions (telegram_id, type, amount, ref_id, status) VALUES (?,?,?,?,?)',
    [ctx.from.id, 'renew_' + acc.proto, totalHarga, 'RNW' + Date.now().toString(36).toUpperCase(), 'success']).catch(() => {});
  const uname = ctx.from.username ? '@' + ctx.from.username : ctx.from.first_name;
  notifGrup(bot, `♻️ <b>Renew VPN</b>\n👤 ${uname}\n📦 ${acc.proto.toUpperCase()} <code>${esc(acc.username)}</code>\n📅 +${days} hari → ${newExpiry}\n💰 Rp${totalHarga.toLocaleString('id-ID')}`);
  await ctx.reply(
    `✅ <b>Akun diperpanjang!</b>\n\n` +
    `F464 Username: <code>${esc(acc.username)}</code>\n` +
    `📅 Exp baru: <code>${newExpiry}</code> (+${days} hari)\n` +
    `💰 Biaya: <b>Rp${totalHarga.toLocaleString('id-ID')}</b>`,
    { parse_mode: 'HTML' }
  );
}

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
    `<blockquote>🟢 <b>Deposit</b> — top up saldo via QRIS
` +
    `🛒 <b>Beli</b> — pulsa, paket data, token PLN
` +
    `📦 <b>Cek Order</b> — lacak transaksimu</blockquote>

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

// Tampilkan daftar produk PPOB (dipakai tombol Beli & Daftar Produk)
async function showProductList(ctx, page) {
  await safeCb(ctx);
  const r = await ppob.productList(undefined, page)
    .catch((e) => ({ success: false, message: `❌ ${esc(e.message)}` }));
  if (!r.success) { await ctx.reply(r.message, { parse_mode: 'HTML' }); return; }
  if (r.pageItems) prodCache.set(ctx.from.id, { pageItems: r.pageItems, page: r.page });
  const extra = { parse_mode: 'HTML', reply_markup: ppob.productKeyboard(r.page, r.pages, r.pageItems) };
  try { await ctx.editMessageText(r.message, extra); }
  catch (e) { await ctx.reply(r.message, extra); }
}

bot.action('ppob_beli', async (ctx) => {
  await showProductList(ctx);
});

bot.action('ppob_produk', async (ctx) => {
  await showProductList(ctx);
});
bot.action(/^prod_page_(\d+)$/, async (ctx) => {
  await showProductList(ctx, parseInt(ctx.match[1], 10));
});

// Tombol beli produk PPOB
bot.action(/^prod_buy_(\d+)_(\d+)$/, async (ctx) => {
  await safeCb(ctx);
  const page = parseInt(ctx.match[1], 10);
  const idx = parseInt(ctx.match[2], 10);
  const cached = prodCache.get(ctx.from.id);
  if (!cached || !cached.pageItems || cached.page !== page || !cached.pageItems[idx]) {
    await ctx.reply('❌ Produk tidak ditemukan / halaman kadaluarsa. Buka daftar produk lagi.');
    return;
  }
  const p = cached.pageItems[idx];
  sessions.set(ctx.chat.id, {
    step: 'ppob_tujuan',
    data: { sku: p.buyer_sku_code, price: p.price_sell, productName: p.product_name },
  });
  const spec = digi.destinationSpec(p.category, p.brand);
  await ctx.reply(
    '🛒 <b>' + esc(p.product_name) + '</b>\n' +
    '💰 Harga: <b>' + digi.rp(p.price_sell) + '</b>\n\n' +
    'Kirim <b>' + esc(spec.label) + '</b> (contoh: <code>' + esc(spec.placeholder) + '</code>):',
    { parse_mode: 'HTML' }
  );
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
  const r = await ppob.productList().catch((e) => ({ success: false, message: `❌ ${esc(e.message)}` }));
  if (!r.success) return ctx.reply(r.message, { parse_mode: 'HTML' });
  if (r.success && r.pageItems) prodCache.set(ctx.from.id, { pageItems: r.pageItems, page: r.page });
  await ctx.reply(r.message, { parse_mode: 'HTML', reply_markup: ppob.productKeyboard(r.page, r.pages, r.pageItems) });
});

bot.command('beli', async (ctx) => {
  const [, kode, tujuan] = ctx.message.text.split(' ');
  if (!kode || !tujuan) return ctx.reply('Contoh: <code>/beli TLKM5 083153170199</code>', { parse_mode: 'HTML' });
  const list = await ppob.productList().catch(() => ({ items: [] }));
  const prodItems = Array.isArray(list.items) ? list.items : [];
  const prod = prodItems.find((p) => p && p.buyer_sku_code && p.buyer_sku_code.toUpperCase() === kode.toUpperCase());
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
    try { await ctx.telegram.sendMessage(id, `📢 <b>Pengumuman</b>\n\n${esc(text)}`, { parse_mode: 'HTML' }); ok++; }
    catch { /* skip blocked */ }
    await new Promise((r) => setTimeout(r, 50));
  }
  await ctx.reply(`✅ Broadcast terkirim ke ${ok}/${ids.length} user.`);
});

bot.command('addsaldo', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const [, uid, amt] = ctx.message.text.split(' ');
  if (!uid || !amt) return ctx.reply('Contoh: <code>/addsaldo 123456 50000</code>', { parse_mode: 'HTML' });
  const r = await ppob.addSaldo(Number(uid), Number(amt));
  const bonusTxt = r.bonus > 0 ? `\n🎁 Bonus: Rp${Number(r.bonus).toLocaleString('id-ID')}` : '';
  notifGrup(bot, `💰 <b>Topup Saldo</b>\n👤 ID: <code>${uid}</code>\n💵 Rp${Number(amt).toLocaleString('id-ID')}${bonusTxt}\n✅ Saldo baru: Rp${Number(r.saldo).toLocaleString('id-ID')}`);
  await ctx.reply(`✅ Saldo user <code>${uid}</code> kini ${digi.rp(r.saldo)}${r.bonus > 0 ? ` (termasuk bonus ${digi.rp(r.bonus)})` : ''}`, { parse_mode: 'HTML' });
});

// ============================================================
// PANEL ADMIN — /admin + semua handler tombol
// ============================================================
bot.action('adm_open', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-utama.png', '🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', adminPanel());
});

bot.command('admin', async (ctx) => {
  if (!admin.isAdmin(ctx)) return ctx.reply('❌ Khusus admin.');
  await safeCb(ctx).catch(() => {});
  await sendMenuPhoto(ctx, 'menu-utama.png',
    '🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:',
    adminPanel());
});

// ---------- Kelola Server ----------
// Tambah server: nama -> domain -> harga (ketik manual dari keyboard)
bot.action('adm_addserver', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_addserver_nama', data: {} });
  await ctx.reply('➕ <b>Tambah Server</b>\n\nKetik <b>nama server</b>:', { parse_mode: 'HTML' });
});

// Hapus server: tampilkan daftar dengan tombol hapus
bot.action('adm_delserver', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await getServers();
  if (!rows.length) return ctx.reply('❌ Belum ada server. Tambah dulu via ➕ Tambah Server.');
  const kb = rows.map((s) => [sBtn(`❌ ${s.nama} (Rp${Number(s.harga).toLocaleString('id-ID')}/hari)`, `adm_delserver_${s.id}`, 'danger')]);
  kb.push([sBtn('🔙 Kembali', 'adm_back', 'danger')]);
  await ctx.reply('❌ <b>Hapus Server</b>\n\nPilih server yang akan dihapus:', {
    parse_mode: 'HTML', reply_markup: { inline_keyboard: kb },
  });
});

bot.action(/^adm_delserver_(\d+)$/, async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const id = parseInt(ctx.match[1], 10);
  const { run } = require('./src/db');
  const r = await run('DELETE FROM servers WHERE id = ?', [id]);
  await ctx.reply(r.changes > 0 ? `✅ Server ID <code>${id}</code> dihapus.` : '⚠️ Server tidak ditemukan.', { parse_mode: 'HTML' });
});

// Edit harga: pilih server -> ketik harga baru dari keyboard
bot.action('adm_editharga', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await getServers();
  if (!rows.length) return ctx.reply('❌ Belum ada server. Tambah dulu via ➕ Tambah Server.');
  const kb = rows.map((s) => [sBtn(`💲 ${s.nama} (Rp${Number(s.harga).toLocaleString('id-ID')}/hari)`, `adm_editharga_${s.id}`, 'primary')]);
  kb.push([sBtn('🔙 Kembali', 'adm_back', 'danger')]);
  await ctx.reply('💲 <b>Edit Harga Server</b>\n\nPilih server:', {
    parse_mode: 'HTML', reply_markup: { inline_keyboard: kb },
  });
});

bot.action(/^adm_editharga_(\d+)$/, async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const id = parseInt(ctx.match[1], 10);
  const { get } = require('./src/db');
  const s = await get('SELECT * FROM servers WHERE id = ?', [id]);
  if (!s) return ctx.reply('⚠️ Server tidak ditemukan.');
  sessions.set(ctx.chat.id, { step: 'adm_editharga_input', data: { serverId: id } });
  await ctx.reply(
    `💲 <b>Edit Harga</b>\n\nServer: <b>${esc(s.nama)}</b>\nHarga saat ini: <b>Rp${Number(s.harga).toLocaleString('id-ID')}/hari</b>\n\nKetik <b>harga baru per hari</b> (angka saja, contoh: 500):`,
    { parse_mode: 'HTML' }
  );
});

// Edit nama: pilih server -> ketik nama baru
bot.action('adm_editnama', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await getServers();
  if (!rows.length) return ctx.reply('❌ Belum ada server. Tambah dulu via ➕ Tambah Server.');
  const kb = rows.map((s) => [sBtn(`📝 ${s.nama}`, `adm_editnama_${s.id}`, 'primary')]);
  kb.push([sBtn('🔙 Kembali', 'adm_back', 'danger')]);
  await ctx.reply('📝 <b>Edit Nama Server</b>\n\nPilih server:', {
    parse_mode: 'HTML', reply_markup: { inline_keyboard: kb },
  });
});

bot.action(/^adm_editnama_(\d+)$/, async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const id = parseInt(ctx.match[1], 10);
  const { get } = require('./src/db');
  const s = await get('SELECT * FROM servers WHERE id = ?', [id]);
  if (!s) return ctx.reply('⚠️ Server tidak ditemukan.');
  sessions.set(ctx.chat.id, { step: 'adm_editnama_input', data: { serverId: id } });
  await ctx.reply(`📝 <b>Edit Nama</b>\n\nNama saat ini: <b>${esc(s.nama)}</b>\n\nKetik <b>nama baru</b>:`, { parse_mode: 'HTML' });
});

// Edit domain: pilih server -> ketik domain baru
bot.action('adm_editdomain', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await getServers();
  if (!rows.length) return ctx.reply('❌ Belum ada server. Tambah dulu via ➕ Tambah Server.');
  const kb = rows.map((s) => [sBtn(`🌐 ${s.nama}`, `adm_editdomain_${s.id}`, 'primary')]);
  kb.push([sBtn('🔙 Kembali', 'adm_back', 'danger')]);
  await ctx.reply('🌐 <b>Edit Domain Server</b>\n\nPilih server:', {
    parse_mode: 'HTML', reply_markup: { inline_keyboard: kb },
  });
});

bot.action(/^adm_editdomain_(\d+)$/, async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const id = parseInt(ctx.match[1], 10);
  const { get } = require('./src/db');
  const s = await get('SELECT * FROM servers WHERE id = ?', [id]);
  if (!s) return ctx.reply('⚠️ Server tidak ditemukan.');
  sessions.set(ctx.chat.id, { step: 'adm_editdomain_input', data: { serverId: id } });
  await ctx.reply(`🌐 <b>Edit Domain</b>\n\nServer: <b>${esc(s.nama)}</b>\nDomain saat ini: <code>${esc(s.domain || '-')}</code>\n\nKetik <b>domain baru</b>:`, { parse_mode: 'HTML' });
});

// List server
bot.action('adm_listserver', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await getServers();
  if (!rows.length) return ctx.reply('❌ Belum ada server. Tambah dulu via ➕ Tambah Server.');
  const lines = rows.map((s, i) =>
    `${i + 1}. <b>${esc(s.nama)}</b>\n   🆔 ID: <code>${s.id}</code>\n   🌐 Domain: <code>${esc(s.domain || '-')}</code>\n   💲 Harga: <b>Rp${Number(s.harga).toLocaleString('id-ID')}/hari</b>`
  );
  await ctx.reply(`📋 <b>Daftar Server (${rows.length})</b>\n\n${lines.join('\n\n')}`, {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[sBtn('🔙 Kembali ke Panel', 'adm_back', 'danger')]] },
  });
});

// Kembali ke panel admin
bot.action('adm_back', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  try {
    await ctx.editMessageText('🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  } catch (e) {
    await ctx.reply('🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup });
  }
});

// ---------- Keuangan ----------
// Tambah saldo: ketik "userId jumlah" dari keyboard
bot.action('adm_addsaldo', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_addsaldo_input', data: {} });
  await ctx.reply('💵 <b>Tambah Saldo</b>\n\nKetik dengan format:\n<code>userId jumlah</code>\nContoh: <code>123456 50000</code>', { parse_mode: 'HTML' });
});

// Kurangi saldo: ketik "userId jumlah" dari keyboard
bot.action('adm_minsaldo', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_minsaldo_input', data: {} });
  await ctx.reply('➖ <b>Kurangi Saldo</b>\n\nKetik dengan format:\n<code>userId jumlah</code>\nContoh: <code>123456 10000</code>', { parse_mode: 'HTML' });
});

// Hasil penjualan
bot.action('adm_sales', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const { get, all } = require('./src/db');
  const total = await get("SELECT COUNT(*) c, COALESCE(SUM(amount),0) s FROM transactions WHERE status = 'success'");
  const byType = await all("SELECT type, COUNT(*) c, COALESCE(SUM(amount),0) s FROM transactions WHERE status = 'success' GROUP BY type");
  const lines = byType.map((t) => `• <code>${esc(t.type)}</code>: ${t.c}x = <b>Rp${Number(t.s).toLocaleString('id-ID')}</b>`);
  await ctx.reply(
    `📊 <b>Hasil Penjualan</b>\n\n` +
    `🧾 Total transaksi sukses: <b>${total.c}</b>\n` +
    `💰 Total omzet: <b>Rp${Number(total.s).toLocaleString('id-ID')}</b>\n\n` +
    (lines.join('\n') || '—'),
    {
      parse_mode: 'HTML',
      reply_markup: { inline_keyboard: [[sBtn('🔙 Kembali ke Panel', 'adm_back', 'danger')]] },
    }
  );
});

// Log topup (10 terakhir)
bot.action('adm_topuplog', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const { all } = require('./src/db');
  const rows = await all("SELECT telegram_id, amount, ref_id, status, created_at FROM transactions WHERE type = 'deposit' ORDER BY id DESC LIMIT 10");
  if (!rows.length) return ctx.reply('📑 Belum ada log topup.');
  const lines = rows.map((r, i) =>
    `${i + 1}. 👤 <code>${r.telegram_id}</code> — <b>Rp${Number(r.amount).toLocaleString('id-ID')}</b>\n   ${r.status === 'success' ? '✅' : r.status === 'pending' ? '⏳' : '❌'} <code>${esc(r.ref_id)}</code> • ${esc(r.created_at || '')}`
  );
  await ctx.reply(`📑 <b>Log Topup (10 terakhir)</b>\n\n${lines.join('\n\n')}`, {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[sBtn('🔙 Kembali ke Panel', 'adm_back', 'danger')]] },
  });
});

// ---------- Lainnya ----------
// Backup DB via tombol (pakai logika yang sama dengan /backupdb)
bot.action('adm_backupdb', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const dbPath = path.join(__dirname, 'data', 'bot.db');
  const backupDir = path.join(__dirname, 'data', 'backups');
  if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const backupPath = path.join(backupDir, `bot-backup-${ts}.db`);
  try {
    fs.copyFileSync(dbPath, backupPath);
    await ctx.replyWithDocument({ source: backupPath }, { caption: `✅ Backup database berhasil.\n📁 ${path.basename(backupPath)}` });
  } catch (e) {
    await ctx.reply(`❌ Backup gagal: ${esc(e.message)}`);
  }
});

// Restore DB via tombol (pakai session yang sama dengan /restoredb)
bot.action('adm_restoredb', async (ctx) => {
  if (!admin.isAdmin(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await ctx.reply(
    '⚠️ <b>Restore Database</b>\n\n' +
    'Kirim file <b>.db</b> backup sebagai dokumen ke chat ini untuk restore.\n' +
    'Bot akan restart setelah restore.',
    { parse_mode: 'HTML' }
  );
  sessions.set(ctx.chat.id, { step: 'restore_db' });
});

// ---------- Reseller ----------
bot.command('setreseller', async (ctx) => {
  if (!admin.isAdmin(ctx)) return ctx.reply('❌ Khusus admin.');
  const uid = ctx.message.text.split(' ')[1];
  if (!uid) return ctx.reply('Contoh: <code>/setreseller 123456</code>', { parse_mode: 'HTML' });
  await ppob.setRole(Number(uid), 'reseller');
  await ctx.reply(`✅ User <code>${uid}</code> kini <b>RESELLER</b> (diskon 10% VPN).`, { parse_mode: 'HTML' });
});

bot.command('unsetreseller', async (ctx) => {
  if (!admin.isAdmin(ctx)) return ctx.reply('❌ Khusus admin.');
  const uid = ctx.message.text.split(' ')[1];
  if (!uid) return ctx.reply('Contoh: <code>/unsetreseller 123456</code>', { parse_mode: 'HTML' });
  await ppob.setRole(Number(uid), 'member');
  await ctx.reply(`✅ User <code>${uid}</code> dikembalikan jadi <b>member</b>.`, { parse_mode: 'HTML' });
});

// ---------- Bonus Topup ----------
bot.command('setbonus', async (ctx) => {
  if (!admin.isAdmin(ctx)) return ctx.reply('❌ Khusus admin.');
  const [, min, persen] = ctx.message.text.split(' ');
  if (!min || !persen) {
    const cfg = await ppob.getBonusConfig();
    return ctx.reply(
      `🎁 <b>Bonus Topup</b>\n\n` +
      `Status: ${cfg.enabled ? '✅ Aktif' : '❌ Nonaktif'}\n` +
      `Min. topup: <b>Rp${Number(cfg.min_topup).toLocaleString('id-ID')}</b>\n` +
      `Bonus: <b>${cfg.bonus_percent}%</b>\n\n` +
      `Atur: <code>/setbonus 50000 10</code>\nNonaktifkan: <code>/setbonus 0 0</code>`,
      { parse_mode: 'HTML' }
    );
  }
  const cfg = await ppob.setBonusConfig(min, persen);
  await ctx.reply(
    `✅ Bonus topup ${cfg.enabled ? 'diaktifkan' : 'dinonaktifkan'}.\n` +
    `Min. topup: <b>Rp${Number(cfg.min_topup).toLocaleString('id-ID')}</b>\n` +
    `Bonus: <b>${cfg.bonus_percent}%</b>`,
    { parse_mode: 'HTML' }
  );
});

bot.command('cleanup', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  const dry = ctx.message.text.includes('dry');
  if (dry) {
    const r = await cleanup.dryRun();
    const e = r.expired.map((a) => `• <code>${esc(a.proto)}/${esc(a.username)}</code> exp ${esc(a.expiry)}`).join('\n') || '—';
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

// ---------- Poller deposit QRIS: kredit saldo otomatis tiap 30 detik ----------
// Deposit yang sudah dibayar di gateway (status paid/success/settled) dikreditkan
// ke saldo user. Klaim atomik: hanya transaksi yang masih 'pending' yang diproses.
setInterval(async () => {
  try {
    const { all, run } = require('./src/db');
    const pending = await all(
      `SELECT telegram_id, amount, ref_id, payment_id FROM transactions
       WHERE type = 'deposit' AND status = 'pending' AND payment_id != ''
         AND created_at > datetime('now','-1 day')`
    ).catch(() => []);
    if (!pending.length) return;
    const { gatewayUrl, apiKey } = config.p2p;
    if (!apiKey) return;
    const axios = require('axios');
    for (const tx of pending) {
      try {
        const { data } = await axios.get(
          `${gatewayUrl}/api/payments/${encodeURIComponent(tx.payment_id)}`,
          { headers: { 'X-API-Key': apiKey }, timeout: 15000 }
        ).catch(() => ({ data: {} }));
        const st = String(data?.status || '').toLowerCase();
        if (!['paid', 'success', 'settled'].includes(st)) continue;
        const r = await run(
          `UPDATE transactions SET status = 'success' WHERE ref_id = ? AND status = 'pending'`,
          [tx.ref_id]
        );
        if (!r.changes) continue; // sudah diproses (anti dobel kredit)
        const s = await ppob.addSaldo(tx.telegram_id, tx.amount);
        await bot.telegram.sendMessage(
          tx.telegram_id,
          `✅ <b>Deposit diterima!</b>\n💰 <b>${digi.rp(tx.amount)}</b> masuk ke saldo kamu.` +
          `\n🧾 Ref: <code>${esc(tx.ref_id)}</code>` +
          `\n💳 Saldo sekarang: <b>${digi.rp(s.saldo)}</b>`,
          { parse_mode: 'HTML' }
        ).catch(() => {});
        console.log(`[deposit] ${tx.ref_id} lunas → saldo +${tx.amount} (tg:${tx.telegram_id})`);
      } catch (e) {
        console.error('[deposit] cek gagal:', tx.ref_id, e.message);
      }
    }
  } catch (e) {
    console.error('[deposit] poller error:', e.message);
  }
}, 30 * 1000);

// ---------- Poller order PPOB pending: cek status otomatis tiap 60 detik ----------
// Order yang masih 'pending' di Digiflazz dicek ulang otomatis; bila sukses user
// dapat notif, bila gagal saldo dikembalikan (lewat ppob.checkOrder).
setInterval(async () => {
  try {
    const { all } = require('./src/db');
    const pending = await all(
      `SELECT ref_id, telegram_id FROM transactions
       WHERE type = 'ppob' AND status = 'pending'
         AND created_at > datetime('now','-2 hours')`
    ).catch(() => []);
    if (!pending.length) return;
    for (const tx of pending) {
      try {
        const r = await ppob.checkOrder(tx.ref_id);
        if (r.status === 'success') {
          await bot.telegram.sendMessage(
            tx.telegram_id,
            `✅ <b>Transaksi PPOB sukses!</b>\n🧾 Ref: <code>${esc(tx.ref_id)}</code>`,
            { parse_mode: 'HTML' }
          ).catch(() => {});
        } else if (r.status === 'failed') {
          await bot.telegram.sendMessage(
            tx.telegram_id,
            `❌ <b>Transaksi PPOB gagal.</b>\n🧾 Ref: <code>${esc(tx.ref_id)}</code>\n💰 Saldo dikembalikan.`,
            { parse_mode: 'HTML' }
          ).catch(() => {});
        }
      } catch (e) { /* lanjut ke order berikutnya */ }
    }
  } catch (e) {
    console.error('[ppob] poller error:', e.message);
  }
}, 60 * 1000);

// ---------- Auto-sync produk Digiflazz (cache lokal, anti rate-limit) ----------
(async () => {
  try {
    const cached = require('./src/db').products();
    const intervalMs = (config.syncMinutes || 60) * 60 * 1000;
    if (!cached.lastSync || Date.now() - cached.lastSync > intervalMs) {
      console.log('[digiflazz] sync produk awal...');
      await digi.sync().catch((e) => console.error('[digiflazz] sync awal gagal:', e.message));
    }
  } catch (e) { console.error('[digiflazz] cek cache gagal:', e.message); }
})();
setInterval(async () => {
  try {
    await digi.sync();
    console.log('[digiflazz] auto-sync produk OK', new Date().toISOString());
  } catch (e) { console.error('[digiflazz] auto-sync produk gagal:', e.message); }
}, (config.syncMinutes || 60) * 60 * 1000);

bot.command('syncproduk', async (ctx) => {
  if (!admin.isAdmin(ctx)) return;
  await ctx.reply('⏳ Sinkronisasi produk Digiflazz...');
  try {
    const out = await digi.sync();
    const n = (out.list_prepaid || []).length;
    await ctx.reply(`✅ Sinkronisasi selesai.\n📦 ${n} produk prabayar dimuat.`);
  } catch (e) {
    await ctx.reply(`❌ Gagal sync: ${esc(e.message)}`);
  }
});

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
  await 
// ---------- Backup & Restore Database (admin) ----------
bot.command('riwayat', async (ctx) => {
  await ensureUser(ctx);
  const msg = await ppob.getHistory(ctx.from.id, 10);
  await ctx.reply(msg, { parse_mode: 'HTML' });
});

bot.command('backupdb', async (ctx) => {
  if (!(await admin.isAdmin(ctx))) return ctx.reply('❌ Khusus admin.');
  const fs = require('fs');
  const path = require('path');
  const dbPath = path.join(__dirname, 'data', 'bot.db');
  const backupDir = path.join(__dirname, 'data', 'backups');
  if (!fs.existsSync(backupDir)) fs.mkdirSync(backupDir, { recursive: true });
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const backupPath = path.join(backupDir, `bot-backup-${ts}.db`);
  try {
    fs.copyFileSync(dbPath, backupPath);
    await ctx.replyWithDocument({ source: backupPath }, { caption: `✅ Backup database berhasil.\n📁 ${path.basename(backupPath)}` });
  } catch (e) {
    await ctx.reply(`❌ Backup gagal: ${e.message}`);
  }
});

bot.command('restoredb', async (ctx) => {
  if (!(await admin.isAdmin(ctx))) return ctx.reply('❌ Khusus admin.');
  await ctx.reply(
    '⚠️ <b>Restore Database</b>\n\n' +
    'Kirim file <b>.db</b> backup sebagai dokumen ke chat ini untuk restore.\n' +
    'Bot akan restart setelah restore.',
    { parse_mode: 'HTML' }
  );
  sessions.set(ctx.chat.id, { step: 'restore_db' });
});

bot.launch();
  console.log('🤖 Bot Wendi berjalan (@IdWendi_bot)');
})();

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
