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
const settings = require('./modules/settings');
// Grup wajib join & grup notifikasi — dikonfigurasi via panel admin (tabel bot_settings).
// Fallback ke nilai lama agar tidak blokir user bila belum dikonfigurasi.
const hcCache = new Map(); // userId_proto_username -> {proto, username, uuid, password}
const prodCache = new Map(); // userId -> {pageItems: [...], page}
const digi = require('./src/digiflazz');
const { esc } = require('./src/format');
const ppobLayout = require('./src/ppob-layout');

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
const mainMenu = (isAdmin = false, isReseller = false) => {
  const rows = [
    [sBtn('🛰️ VPN Premium', 'menu_vpn', 'primary'), sBtn('☁️ VPN CloudFront', 'menu_cf', 'primary')],
    [sBtn('💰 PPOB & Pulsa', 'menu_ppob', 'success'), sBtn('📊 Cek Kuota', 'menu_kuota', 'primary')],
    [sBtn('👤 Akun Saya', 'menu_akun', 'success'), sBtn('📈 Statistik', 'menu_stat', 'primary')],
    [sBtn('💰 Sewa Script VPN', 'menu_sewa', 'success')],
  ];
  if (isReseller) rows.push([sBtn('🏪 Panel Reseller', 'menu_reseller', 'success')]);
  if (isAdmin) rows.push([sBtn('🛠️ Panel Admin', 'adm_open', 'danger')]);
  return Markup.inlineKeyboard(rows);
};

const backBtn = () => Markup.inlineKeyboard([[sBtn('🔙 Kembali', 'menu_main', 'danger')]]);

// ---------- Panel Admin ----------
const adminPanel = () => Markup.inlineKeyboard([
  [sBtn('➕ Tambah Server', 'adm_addserver', 'success'), sBtn('❌ Hapus Server', 'adm_delserver', 'danger')],
  [sBtn('💲 Edit Harga', 'adm_editharga', 'primary'), sBtn('📝 Edit Nama', 'adm_editnama', 'primary')],
  [sBtn('💲 Harga VPN/Role', 'adm_vpnprices', 'primary'), sBtn('👥 Kelola Role', 'adm_roles', 'primary')],
  [sBtn('🌐 Edit Domain', 'adm_editdomain', 'primary'), sBtn('📋 List Server', 'adm_listserver', 'success')],
  [sBtn('💵 Tambah Saldo', 'adm_addsaldo', 'success'), sBtn('➖ Kurangi Saldo', 'adm_minsaldo', 'danger')],
  [sBtn('📊 Hasil Penjualan', 'adm_sales', 'primary'), sBtn('📑 Log Topup', 'adm_topuplog', 'primary')],
  [sBtn('📦 Backup DB', 'adm_backupdb', 'success'), sBtn('♻️ Restore DB', 'adm_restoredb', 'danger')],
  [sBtn('🧾 Setting Pakasir', 'adm_pakasir', 'primary'), sBtn('🎁 Bonus & Reseller', 'adm_bonus', 'success')],
  [sBtn('📢 Broadcast Grup', 'adm_bcast', 'primary'), sBtn('📣 Broadcast User', 'adm_bcastuser', 'primary')],
  [sBtn('🔔 Grup Notifikasi', 'adm_notifgrp', 'primary'), sBtn('🔒 Force Join', 'adm_forcejoin', 'primary')],
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
    [sBtn('🖥️ SSH', `${p}mk_ssh`, 'danger'), sBtn('📡 VMess', `${p}mk_vmess`, 'success')],
    [sBtn('⚡ VLess', `${p}mk_vless`, 'primary'), sBtn('🛡️ Trojan', `${p}mk_trojan`, 'success')],
    [sBtn('👻 Shadowsocks', `${p}mk_shadowsocks`, 'primary')],
    [sBtn('⚡ Zivpn UDP', `${p}mk_zivpn`, 'success')],
    [sBtn('💰 Topup Saldo', 'ppob_deposit', 'success')],
    [sBtn('🔙 Kembali', 'menu_main', 'danger')],
  ]);
};

// Cek apakah user sudah join channel & grup wajib (admin selalu lolos).
// Konfigurasi via panel admin (tabel bot_settings). Masing-masing bisa
// dikosongkan = tidak dicek. Return { ok, missing: [{id, url, label}] }.
async function checkForceJoin(ctx) {
  try {
    if (await admin.hasAdminAccess(ctx)) return { ok: true, missing: [] };
    const fj = await settings.getForceJoin();
    if (!fj.enabled) return { ok: true, missing: [] };
    const missing = [];
    const targets = [
      { id: fj.channelId, url: fj.channelUrl, label: 'Channel' },
      { id: fj.groupId, url: fj.groupUrl, label: 'Grup' },
    ];
    for (const t of targets) {
      if (!t.id) continue;
      try {
        const m = await ctx.telegram.getChatMember(t.id, ctx.from.id);
        if (!['member', 'administrator', 'creator'].includes(m.status)) {
          missing.push(t);
        }
      } catch (e) {
        // Bot bukan member / ID salah — lewati target ini agar tidak blokir semua user
        console.error('checkForceJoin error:', t.id, e.message);
      }
    }
    return { ok: missing.length === 0, missing };
  } catch (e) {
    console.error('checkForceJoin error:', e.message);
    return { ok: true, missing: [] };
  }
}

// Kompatibilitas: versi boolean sederhana (dipakai kode lama)
async function checkGroupMember(ctx) {
  const r = await checkForceJoin(ctx);
  return r.ok;
}

const ensureUser = async (ctx) => {
  const { run } = require('./src/db');
  await run('INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)',
    [ctx.from.id, ctx.from.username || ctx.from.first_name || '']);
};

// ---------- /start ----------
const WELCOME_CAPTION = (name, role = 'member') =>
`👋 Halo <b>${esc(name)}</b>! ${settings.roleBadge(role)}

🛰 <b>WENDI VPN BOT</b> 🛰
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:

<blockquote>🛰️ <b>VPN Premium</b> — SSH / VMess / VLess / Trojan
☁️ <b>VPN CloudFront</b> — trafik disamarkan HTTPS
💰 <b>PPOB & Pulsa</b> — isi pulsa, paket data, PLN
📊 <b>Cek Kuota</b> — cek kuota semua operator
💰 <b>Sewa Script</b> — lisensi script VPN</blockquote>
━━━━━━━━━━━━━━━━━━
<code>🌐 dikelola oleh Wendi Network</code>`;

bot.start(async (ctx) => {
  await ensureUser(ctx);
  await safeCb(ctx);
  const fj = await checkForceJoin(ctx);
  if (!fj.ok) {
    const rows = fj.missing.map((t) => [
      { text: `📢 Join ${t.label}`, url: t.url || `https://t.me/${String(t.id).replace('@', '')}` },
    ]);
    rows.push([{ text: '✅ Saya Sudah Gabung', callback_data: 'fj_verify' }]);
    return ctx.reply(
      '⚠️ <b>Wajib Join Dulu</b>\n\n' +
      'Untuk memakai bot ini, silakan join ' +
      fj.missing.map((t) => t.label).join(' & ') +
      ' kami dulu.\n\nSetelah join, tekan tombol <b>✅ Saya Sudah Gabung</b>.',
      { parse_mode: 'HTML', reply_markup: { inline_keyboard: rows } }
    );
  }
  await sendMenuPhoto(ctx, 'menu-utama.png',
    WELCOME_CAPTION(ctx.from.first_name || 'kawan', await ppob.getRole(ctx.from.id).catch(() => 'member')),
    mainMenu(await admin.hasAdminAccess(ctx), (await ppob.getRole(ctx.from.id).catch(() => 'member')) === 'reseller'));
});

// Verifikasi ulang force join setelah user tekan "Saya Sudah Gabung"
bot.action('fj_verify', async (ctx) => {
  await safeCb(ctx);
  const fj = await checkForceJoin(ctx);
  if (!fj.ok) {
    return ctx.reply('❌ Kamu belum join semua. Join dulu lalu tekan tombol verifikasi lagi.');
  }
  await sendMenuPhoto(ctx, 'menu-utama.png',
    WELCOME_CAPTION(ctx.from.first_name || 'kawan', await ppob.getRole(ctx.from.id).catch(() => 'member')),
    mainMenu(await admin.hasAdminAccess(ctx), (await ppob.getRole(ctx.from.id).catch(() => 'member')) === 'reseller'));
});

bot.action('menu_main', async (ctx) => {
  await safeCb(ctx);
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  await sendMenuPhoto(ctx, 'menu-utama.png',
    `🏠 <b>MENU UTAMA</b> ${settings.roleBadge(role)}
━━━━━━━━━━━━━━━━━━
Pilih layanan di bawah ini:`, mainMenu(await admin.hasAdminAccess(ctx), role === 'reseller'));
});

// ---------- Menu VPN ----------
bot.action('menu_vpn', async (ctx) => {
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-vpn.png',
    `🛰️ <b>VPN PREMIUM</b>
━━━━━━━━━━━━━━━━━━
` +
    `<blockquote>🖥️ <b>SSH</b> — cepat & stabil
` +
    `📡 <b>VMess</b> — protokol V2Ray
` +
    `⚡ <b>VLess</b> — ringan & cepat
` +
    `🛡️ <b>Trojan</b> — aman & anti-blokir
` +
    `👻 <b>Shadowsocks</b> — simpel & cepat</blockquote>

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
    `🖥️ <b>SSH</b>  📡 <b>VMess</b>
` +
    `⚡ <b>VLess</b>  🛡️ <b>Trojan</b>

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

  // --- Session input slug Pakasir ---
  if (sess?.step === 'adm_pakasir_slug') {
    const slug = ctx.message.text.trim();
    sessions.delete(chatId);
    if (!slug) return ctx.reply('❌ Slug tidak boleh kosong.');
    const c = await pakasir.getConfig();
    await pakasir.setConfig(slug, c.api_key);
    // Hapus pesan berisi slug dari chat demi keamanan? Tidak — slug bersifat publik.
    return ctx.reply(`✅ Slug Pakasir disimpan: <code>${esc(slug)}</code>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // --- Session input API key Pakasir ---
  if (sess?.step === 'adm_pakasir_key') {
    const apiKey = ctx.message.text.trim();
    sessions.delete(chatId);
    if (!apiKey) return ctx.reply('❌ API key tidak boleh kosong.');
    const c = await pakasir.getConfig();
    await pakasir.setConfig(c.slug, apiKey);
    // Hapus pesan berisi API key dari chat demi keamanan
    try { await ctx.deleteMessage(ctx.message.message_id); } catch (_) {}
    return ctx.reply(`✅ API key Pakasir disimpan (<code>${pakasir.maskKey(apiKey)}</code>).`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // --- Session admin: set bonus topup (format: "min_topup persen") ---
  if (sess?.step === 'adm_bonus_input') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const parts = ctx.message.text.trim().split(/\s+/);
    const minTopup = Number((parts[0] || '').replace(/\D/g, ''));
    const persen = Number((parts[1] || '').replace(/\D/g, ''));
    sessions.delete(chatId);
    if (parts[0] === '0' || (!minTopup && !persen)) {
      await ppob.setBonusConfig(0, 0);
      return ctx.reply('✅ Bonus topup <b>dinonaktifkan</b>.', { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup });
    }
    if (!minTopup || !persen || persen > 100) {
      return ctx.reply('❌ Format salah. Contoh: <code>50000 10</code>', { parse_mode: 'HTML' });
    }
    const cfg = await ppob.setBonusConfig(minTopup, persen);
    return ctx.reply(
      `✅ <b>Bonus topup diaktifkan!</b>\n\nMin. topup: <b>${digi.rp(cfg.min_topup)}</b>\nBonus: <b>${cfg.bonus_percent}%</b>`,
      { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup }
    );
  }

  // --- Session admin: set minimal topup otomatis reseller ---
  if (sess?.step === 'adm_resset_input') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const nominal = Number(ctx.message.text.replace(/\D/g, ''));
    sessions.delete(chatId);
    await settings.setSetting('reseller_min_topup', String(nominal || 0));
    return ctx.reply(
      nominal > 0
        ? `✅ Min. topup otomatis reseller: <b>${digi.rp(nominal)}</b>\n\nUser yang total topup-nya mencapai nominal ini otomatis jadi 🏪 Reseller.`
        : `✅ Fitur otomatis reseller <b>dinonaktifkan</b>.`,
      { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup }
    );
  }

  // --- Session admin: tambah grup broadcast ---
  if (sess?.step === 'adm_bcast_add') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const chatIdIn = ctx.message.text.trim();
    sessions.delete(chatId);
    if (!/^-?\d+$/.test(chatIdIn)) return ctx.reply('❌ ID grup tidak valid. Contoh: <code>-1001234567890</code>', { parse_mode: 'HTML' });
    // Ambil judul grup (best effort)
    let title = '';
    try {
      const ch = await ctx.telegram.getChat(chatIdIn);
      title = ch.title || '';
    } catch (e) {
      return ctx.reply(`⚠️ Tidak bisa akses grup <code>${esc(chatIdIn)}</code>.\nPastikan bot sudah jadi <b>admin</b> di grup tersebut, lalu coba lagi.`, { parse_mode: 'HTML' });
    }
    await settings.addBroadcastGroup(chatIdIn, title);
    return ctx.reply(`✅ Grup <b>${esc(title || chatIdIn)}</b> ditambahkan ke daftar broadcast.`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // --- Session admin: tulis pesan broadcast ---
  if (sess?.step === 'adm_bcast_msg') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const pesan = ctx.message.text;
    sessions.delete(chatId);
    if (!pesan || pesan.length < 2) return ctx.reply('❌ Pesan terlalu pendek.');
    const groups = await settings.listBroadcastGroups();
    if (!groups.length) return ctx.reply('❌ Belum ada grup terdaftar.');
    await ctx.reply(`⏳ Mengirim broadcast ke ${groups.length} grup...`);
    let ok = 0, fail = 0;
    for (const g of groups) {
      try {
        await ctx.telegram.sendMessage(g.chat_id, `📢 <b>Pengumuman</b>\n\n${pesan}`, { parse_mode: 'HTML' });
        ok++;
      } catch (e) { fail++; }
      await new Promise((r) => setTimeout(r, 100));
    }
    notifGrup(bot, `📢 <b>Broadcast Grup</b>\n👤 Admin: ${ctx.from.username ? '@' + ctx.from.username : ctx.from.first_name}\n✅ Terkirim: ${ok} grup${fail ? `\n❌ Gagal: ${fail} grup` : ''}`);
    return ctx.reply(`✅ Broadcast selesai.\n📨 Terkirim: <b>${ok}</b> grup${fail ? `\n❌ Gagal: <b>${fail}</b> grup` : ''}`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // --- Session admin: tulis pesan broadcast user → konfirmasi ---
  if (sess?.step === 'adm_bcu_msg') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const pesan = ctx.message.text;
    const { target, tlabel } = sess.data || {};
    if (!pesan || pesan.length < 2) return ctx.reply('❌ Pesan terlalu pendek.');
    const { all } = require('./src/db');
    const rows = target === 'all'
      ? await all('SELECT telegram_id FROM users')
      : await all('SELECT telegram_id FROM users WHERE role = ?', [target]);
    const count = new Set(rows.map((r) => r.telegram_id).filter(Boolean)).size;
    if (!count) { sessions.delete(chatId); return ctx.reply('❌ Tidak ada user pada target ini.'); }
    sessions.set(chatId, { step: 'adm_bcu_confirm', data: { target, tlabel, pesan } });
    return ctx.reply(
      `📣 <b>Konfirmasi Broadcast</b>\n\n🎯 Target: <b>${tlabel}</b>\n👥 Penerima: <b>${count}</b> user\n\n<b>Isi pesan:</b>\n${pesan}\n\nKirim sekarang?`,
      {
        parse_mode: 'HTML',
        reply_markup: Markup.inlineKeyboard([
          [sBtn('✅ Ya, Kirim', 'adm_bcu_confirm', 'success'), sBtn('❌ Batal', 'adm_bcu_cancel', 'danger')],
        ]).reply_markup,
      }
    );
  }

  // --- Session admin: set grup notifikasi ---
  if (sess?.step === 'adm_notifgrp_input') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const gid = ctx.message.text.trim();
    sessions.delete(chatId);
    if (!/^-?\d+$/.test(gid)) return ctx.reply('❌ ID grup tidak valid. Contoh: <code>-1001234567890</code>', { parse_mode: 'HTML' });
    try {
      await ctx.telegram.sendMessage(gid, '🔔 <b>Grup notifikasi terhubung!</b>\n\nNotifikasi transaksi akan dikirim ke sini.', { parse_mode: 'HTML' });
    } catch (e) {
      return ctx.reply(`⚠️ Tidak bisa kirim pesan ke <code>${esc(gid)}</code>.\nPastikan bot sudah jadi <b>admin</b> di grup tersebut.`, { parse_mode: 'HTML' });
    }
    await settings.setSetting('notif_group_id', gid);
    return ctx.reply(`✅ Grup notifikasi diatur ke <code>${esc(gid)}</code>.`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // --- Session admin: set channel/grup force join (format: "ID | link") ---
  if (sess?.step === 'adm_fj_channel' || sess?.step === 'adm_fj_group') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const isChannel = sess.step === 'adm_fj_channel';
    const raw = ctx.message.text.trim();
    sessions.delete(chatId);
    const key = isChannel ? 'force_join_channel' : 'force_join_group';
    const label = isChannel ? 'Channel' : 'Grup';
    if (raw === '-') {
      await settings.setSetting(key + '_id', '');
      await settings.setSetting(key + '_url', '');
      return ctx.reply(`✅ ${label} wajib join <b>dikosongkan</b> (tidak dicek).`, {
        parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
      });
    }
    const [idPart, ...urlParts] = raw.split('|').map((s) => s.trim());
    const url = urlParts.join('|').trim();
    if (!idPart) return ctx.reply('❌ ID tidak boleh kosong.', { parse_mode: 'HTML' });
    await settings.setSetting(key + '_id', idPart);
    if (url) await settings.setSetting(key + '_url', url);
    return ctx.reply(
      `✅ ${label} wajib join diatur:\n🆔 ID: <code>${esc(idPart)}</code>\n🔗 Link: ${esc(url || '-')}`,
      { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup }
    );
  }

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
    const _r1 = await ppob.getRole(ctx.from.id).catch(() => 'member');
    const _p1 = await vpn.getVpnPrice(sess.proto, _r1);
    return ctx.reply(
      'Masukkan <b>durasi (hari)</b>\nHarga: <b>Rp' + _p1.toLocaleString('id-ID') + '/hari</b>\nSaldo kamu: <b>Rp' + (await ppob.getSaldo(ctx.from.id)).toLocaleString('id-ID') + '</b>',
      { parse_mode: 'HTML' }
    );
  }

  if (sess?.step === 'vpn_password') {
    const password = ctx.message.text.trim();
    if (password.length < 4) return ctx.reply('❌ Password minimal 4 karakter. Coba lagi:');
    sess.data.password = password;
    sess.step = 'vpn_days';
    const _r2 = await ppob.getRole(ctx.from.id).catch(() => 'member');
    const _p2 = await vpn.getVpnPrice(sess.proto, _r2);
    return ctx.reply(
      'Masukkan <b>durasi (hari)</b>\nHarga: <b>Rp' + _p2.toLocaleString('id-ID') + '/hari</b>\nSaldo kamu: <b>Rp' + (await ppob.getSaldo(ctx.from.id)).toLocaleString('id-ID') + '</b>',
      { parse_mode: 'HTML' }
    );
  }

  if (sess?.step === 'restore_db') {
    const doc = ctx.message.document;
    if (!doc || !doc.file_name.endsWith('.db')) {
      return ctx.reply('❌ Kirim file .db yang valid. Batalkan dengan /start');
    }
    if (!(await admin.hasAdminAccess(ctx))) {
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

  // --- Session cari produk PPOB: keyword ---
  if (sess?.step === 'ppob_cari') {
    const kw = ctx.message.text.trim();
    sessions.delete(chatId);
    if (!kw || kw.length < 2) {
      return ctx.reply('❌ Kata kunci minimal 2 karakter. Coba lagi dari menu PPOB.');
    }
    if (kw.length > 40) {
      return ctx.reply('❌ Kata kunci terlalu panjang (maks 40 karakter).');
    }
    return showProductList(ctx, 'cari:' + kw);
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
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    sess.data.nama = nama;
    sess.step = 'adm_addserver_domain';
    return ctx.reply(`➕ <b>Tambah Server</b>\n\nNama: <b>${esc(nama)}</b>\n\nKetik <b>domain server</b> (contoh: sg1.wendivpn.my.id):`, { parse_mode: 'HTML' });
  }

  // Tambah server: domain
  if (sess?.step === 'adm_addserver_domain') {
    const domain = ctx.message.text.trim();
    if (!domain || domain.length < 4) return ctx.reply('❌ Domain tidak valid. Coba lagi:');
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    sess.data.domain = domain;
    sess.step = 'adm_addserver_harga';
    return ctx.reply(`➕ <b>Tambah Server</b>\n\nNama: <b>${esc(sess.data.nama)}</b>\nDomain: <code>${esc(domain)}</code>\n\nKetik <b>harga per hari</b> (angka saja, contoh: 500):`, { parse_mode: 'HTML' });
  }

  // Tambah server: harga -> simpan
  if (sess?.step === 'adm_addserver_harga') {
    const harga = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
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
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
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
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
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
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    if (!domain || domain.length < 4) return ctx.reply('❌ Domain tidak valid. Coba lagi:');
    const { run } = require('./src/db');
    await run('UPDATE servers SET domain = ? WHERE id = ?', [domain, sess.data.serverId]);
    sessions.delete(chatId);
    return ctx.reply(`✅ Domain server diperbarui menjadi <code>${esc(domain)}</code>`, {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  }

  // Ubah harga VPN per role: ketik angka (Rp/hari)
  if (sess?.step === 'adm_price_input') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const harga = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    if (!Number.isFinite(harga) || harga < 0) return ctx.reply('❌ Harga tidak valid. Ketik angka saja (contoh: 500):');
    const { key, role } = sess.data;
    sessions.delete(chatId);
    try {
      await vpn.setVpnPrice(key, role, harga);
      return ctx.reply(
        `✅ <b>Harga diperbarui!</b>\n\n📦 Produk: <b>${esc(key)}</b>\n👤 Role: <b>${role}</b>\n💲 Harga baru: <b>Rp${harga.toLocaleString('id-ID')}/hari</b>`,
        { parse_mode: 'HTML' }
      );
    } catch (e) {
      return ctx.reply(`❌ ${esc(e.message)}`);
    }
  }

  // Ubah role user: ketik ID Telegram
  if (sess?.step === 'adm_role_id') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
    const uid = parseInt(ctx.message.text.replace(/\D/g, ''), 10);
    if (!uid) return ctx.reply('❌ ID tidak valid. Ketik angka saja:');
    sessions.delete(chatId);
    const cur = await ppob.getRole(uid).catch(() => 'member');
    return ctx.reply(
      `✏️ <b>Ubah Role User</b>\n\n🆔 ID: <code>${uid}</code>\n📌 Role saat ini: <b>${cur}</b>\n\nPilih role baru:`,
      {
        parse_mode: 'HTML',
        reply_markup: {
          inline_keyboard: [
            [sBtn('🛡️ Admin', `adm_roleset_${uid}_admin`, 'danger'), sBtn('🤝 Reseller', `adm_roleset_${uid}_reseller`, 'success')],
            [sBtn('👤 Member', `adm_roleset_${uid}_member`, 'primary')],
          ],
        },
      }
    );
  }

  // Tambah saldo: format "userId jumlah"
  if (sess?.step === 'adm_addsaldo_input') {
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
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
    if (!await admin.hasAdminAccess(ctx)) { sessions.delete(chatId); return ctx.reply('❌ Khusus admin.'); }
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
    if (!nominal || nominal < 10000) { sessions.delete(chatId); return ctx.reply('❌ Nominal minimal Rp10.000'); }
    // Jika Pakasir aktif → user pilih metode bayar dulu
    const pakasirReady = await pakasir.isReady().catch(() => false);
    if (pakasirReady) {
      sessions.set(chatId, { step: 'deposit_method', nominal });
      const kb = Markup.inlineKeyboard([
        [sBtn('💳 GoPay QRIS', 'dep_method_gopay', 'primary')],
        [sBtn('🧾 Pakasir (QRIS/VA)', 'dep_method_pakasir', 'success')],
        [sBtn('❌ Batal', 'menu_ppob', 'danger')],
      ]);
      return ctx.reply(
        `💰 <b>Deposit ${digi.rp(nominal)}</b>\n\nPilih metode pembayaran:`,
        { parse_mode: 'HTML', reply_markup: kb.reply_markup }
      );
    }
    // Pakasir belum aktif → langsung GoPay seperti sebelumnya
    sessions.delete(chatId);
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
  // Harga VPN per role (diatur admin di tabel vpn_prices; role admin = 0/modal)
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const perDay = await vpn.getVpnPrice(proto, role);
  const totalHarga = perDay * days;
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

// Kirim notifikasi transaksi ke grup (ID dikonfigurasi via panel admin;
// fallback ke GROUP_NOTIF bila belum dikonfigurasi)
async function notifGrup(bot, pesan) {
  try {
    const gid = (await settings.getNotifGroup().catch(() => '')) || GROUP_NOTIF;
    if (!gid) return;
    await bot.telegram.sendMessage(gid, pesan, { parse_mode: 'HTML', disable_web_page_preview: true });
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
  if (!await admin.hasAdminAccess(ctx)) return;
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
    text: `👤 <b>AKUN SAYA</b>\n━━━━━━━━━━━━━━━━━━\n📄 Halaman <b>${pg}</b> dari <b>${pages}</b>\n\n<blockquote>${lines.join('\n')}</blockquote>`,
    page: pg, pages, slice,
  };
}
bot.action('menu_akun', async (ctx) => {
  await safeCb(ctx);
  const rows = await vpn.myAccounts(ctx.from.id);
  if (!rows.length) {
    return sendMenuPhoto(ctx, 'menu-akun.png',
      `👤 <b>AKUN SAYA</b>\n━━━━━━━━━━━━━━━━━━\n\n📭 Kamu belum punya akun VPN.\nBuat dulu di menu VPN ya!`, backBtn());
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

// ============================================================
// ---------- Panel Reseller ----------
// ============================================================
const isResellerOrAdmin = async (ctx) => {
  if (await admin.hasAdminAccess(ctx)) return true;
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  return role === 'reseller';
};

const resellerPanel = () => Markup.inlineKeyboard([
  [sBtn('💰 Harga Modal Saya', 'rsl_prices', 'primary'), sBtn('➕ Buat Akun VPN', 'rsl_create', 'success')],
  [sBtn('📋 Riwayat Transaksi', 'rsl_history', 'primary'), sBtn('💳 Saldo Saya', 'rsl_saldo', 'success')],
  [sBtn('🔙 Kembali', 'menu_main', 'danger')],
]);

bot.action('menu_reseller', async (ctx) => {
  await safeCb(ctx);
  if (!await isResellerOrAdmin(ctx)) return ctx.reply('❌ Khusus reseller.');
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const saldo = await ppob.getSaldo(ctx.from.id).catch(() => 0);
  await ctx.reply(
    `🏪 <b>PANEL RESELLER</b> ${settings.roleBadge(role)}\n━━━━━━━━━━━━━━━━━━\n\n` +
    `💳 Saldo: <b>Rp${Number(saldo).toLocaleString('id-ID')}</b>\n\n` +
    `Pilih menu di bawah ini:`,
    { parse_mode: 'HTML', reply_markup: resellerPanel().reply_markup }
  );
});

// a. Harga modal reseller
bot.action('rsl_prices', async (ctx) => {
  await safeCb(ctx);
  if (!await isResellerOrAdmin(ctx)) return ctx.reply('❌ Khusus reseller.');
  const protos = ['ssh', 'vmess', 'vless', 'trojan', 'shadowsocks', 'zivpn'];
  const labels = { ssh: '🖥️ SSH', vmess: '📡 VMess', vless: '⚡ VLess', trojan: '🛡️ Trojan', shadowsocks: '👻 Shadowsocks', zivpn: '🚀 Zivpn UDP' };
  const lines = [];
  for (const p of protos) {
    const harga = await vpn.getVpnPrice(p, 'reseller');
    lines.push(`${labels[p]}: <b>Rp${Number(harga).toLocaleString('id-ID')}/hari</b>`);
  }
  await ctx.reply(
    `💰 <b>Harga Modal Reseller</b>\n━━━━━━━━━━━━━━━━━━\n\n${lines.join('\n')}\n\n<i>Harga per hari. Admin = Rp0 (modal).</i>`,
    { parse_mode: 'HTML', reply_markup: resellerPanel().reply_markup }
  );
});

// b. Buat akun VPN (pakai alur yang sudah ada — harga otomatis sesuai role)
bot.action('rsl_create', async (ctx) => {
  await safeCb(ctx);
  if (!await isResellerOrAdmin(ctx)) return ctx.reply('❌ Khusus reseller.');
  const saldo = await ppob.getSaldo(ctx.from.id).catch(() => 0);
  await ctx.reply(
    `➕ <b>Buat Akun VPN</b>\n━━━━━━━━━━━━━━━━━━\n\n` +
    `💳 Saldo kamu: <b>Rp${Number(saldo).toLocaleString('id-ID')}</b>\n` +
    `Harga sesuai tarif reseller.\n\nPilih protokol:`,
    { parse_mode: 'HTML', reply_markup: vpnMenu(false).reply_markup }
  );
});

// c. Riwayat transaksi reseller
bot.action('rsl_history', async (ctx) => {
  await safeCb(ctx);
  if (!await isResellerOrAdmin(ctx)) return ctx.reply('❌ Khusus reseller.');
  const { all } = require('./src/db');
  const rows = await all(
    'SELECT type, amount, status, created_at FROM transactions WHERE telegram_id = ? ORDER BY rowid DESC LIMIT 15',
    [ctx.from.id]
  ).catch(() => []);
  if (!rows.length) {
    return ctx.reply('📋 <b>Riwayat Transaksi</b>\n\n📭 Belum ada transaksi.', {
      parse_mode: 'HTML', reply_markup: resellerPanel().reply_markup,
    });
  }
  const lines = rows.map((r, i) => {
    const tgl = r.created_at ? new Date(r.created_at).toLocaleDateString('id-ID') : '-';
    return `${i + 1}. <code>${esc(r.type || '-')}</code> — Rp${Number(r.amount || 0).toLocaleString('id-ID')} (${esc(r.status || '-')}) <i>${tgl}</i>`;
  });
  await ctx.reply(
    `📋 <b>Riwayat Transaksi</b> (15 terakhir)\n━━━━━━━━━━━━━━━━━━\n\n${lines.join('\n')}`,
    { parse_mode: 'HTML', reply_markup: resellerPanel().reply_markup }
  );
});

// d. Saldo reseller
bot.action('rsl_saldo', async (ctx) => {
  await safeCb(ctx);
  if (!await isResellerOrAdmin(ctx)) return ctx.reply('❌ Khusus reseller.');
  const saldo = await ppob.getSaldo(ctx.from.id).catch(() => 0);
  await ctx.reply(
    `💳 <b>Saldo Saya</b>\n━━━━━━━━━━━━━━━━━━\n\n💰 Saldo: <b>Rp${Number(saldo).toLocaleString('id-ID')}</b>`,
    {
      parse_mode: 'HTML',
      reply_markup: Markup.inlineKeyboard([
        [sBtn('💰 Topup Saldo', 'ppob_deposit', 'success')],
        [sBtn('🔙 Kembali', 'menu_reseller', 'danger')],
      ]).reply_markup,
    }
  );
});

// ---------- Renew Akun ----------
bot.action(/^renew_(\d+)$/, async (ctx) => {
  await safeCb(ctx);
  const { get } = require('./src/db');
  const acc = await get('SELECT * FROM vpn_accounts WHERE id = ? AND telegram_id = ?', [ctx.match[1], ctx.from.id]);
  if (!acc) return ctx.reply('❌ Akun tidak ditemukan.');
  sessions.set(ctx.chat.id, { step: 'renew_days', accountId: acc.id });
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  const _rpDay = await vpn.getVpnPrice(acc.proto, role);
  await ctx.reply(
    `♻️ <b>Renew Akun</b>\n\n` +
    `F464 Username: <code>${esc(acc.username)}</code>\n` +
    `📅 Exp saat ini: <code>${esc(acc.expiry)}</code>\n\n` +
    `Harga: <b>Rp${_rpDay.toLocaleString('id-ID')}/hari</b> (${role})\n` +
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
  const totalHarga = (await vpn.getVpnPrice(acc.proto, role)) * days; // harga per role (admin = 0)
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
  const role = await ppob.getRole(ctx.from.id).catch(() => 'member');
  await sendMenuPhoto(ctx, 'menu-ppob.png',
    `🛒 <b>PPOB RIPZZSTORE</b>
Belanja kebutuhan digital otomatis — cepat, aman & 24 jam.

` +
    `👤 Role: <b>${settings.roleBadge(role)}</b>
` +
    `💰 Saldo: <b>${digi.rp(saldo)}</b>

` +
    `⚡ <i>Harga mengikuti role kamu.</i>
` +
    `Pilih kategori layanan:`,
    ppobCategoryKeyboard());
});

// Keyboard kategori PPOB (2 kolom, ala screenshot)
function ppobCategoryKeyboard() {
  const btns = ppobLayout.CATEGORY_BUTTONS || [];
  const rows = [];
  // Baris deposit di atas
  rows.push([sBtn('💰 Deposit / Top Up', 'ppob_deposit', 'success')]);
  for (let i = 0; i < btns.length; i += 2) {
    const row = [];
    for (let j = i; j < Math.min(i + 2, btns.length); j++) {
      const [group, label] = btns[j];
      row.push(sBtn(label, 'ppob_cat_' + group, j % 2 === 0 ? 'success' : 'primary'));
    }
    rows.push(row);
  }
  rows.push([sBtn('🔍 CARI PRODUK', 'ppob_cari', 'primary'), sBtn('⭐ POPULER', 'ppob_populer', 'danger')]);
  rows.push([sBtn('📱 Prabayar', 'ppob_prabayar', 'primary'), sBtn('🧾 Pascabayar', 'ppob_pascabayar', 'primary')]);
  rows.push([sBtn('📋 Cek Order', 'ppob_cekorder', 'primary'), sBtn('🏠 Menu Utama', 'menu_main', 'success')]);
  return Markup.inlineKeyboard(rows);
}

bot.action('ppob_deposit', async (ctx) => {
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'deposit_nominal' });
  const bonus = await ppob.getBonusConfig().catch(() => ({}));
  const bonusTxt = bonus?.enabled
    ? `\n🎁 <b>Bonus ${bonus.bonus_percent}%</b> untuk topup min. <b>${digi.rp(bonus.min_topup)}</b>!`
    : '';
  await ctx.reply(`💰 Kirim <b>nominal deposit</b> (min Rp10.000):${bonusTxt}`, { parse_mode: 'HTML' });
});

// User pilih metode deposit: GoPay QRIS (gateway sendiri)
bot.action('dep_method_gopay', async (ctx) => {
  await safeCb(ctx);
  const sess = sessions.get(ctx.chat.id);
  const nominal = sess?.nominal;
  sessions.delete(ctx.chat.id);
  if (!nominal) return ctx.reply('❌ Sesi kedaluwarsa, ulangi dari menu deposit.');
  await ctx.reply('⏳ Membuat QRIS...');
  const r = await ppob.createDeposit(ctx.from.id, nominal);
  if (!r.success) return ctx.reply(r.message);
  const caption = `💳 <b>Deposit ${digi.rp(nominal)}</b>\nRef: <code>${r.ref}</code>\n\nScan QRIS di atas untuk bayar. Saldo masuk otomatis setelah pembayaran terdeteksi.`;
  if (r.qrBuffer) return ctx.replyWithPhoto({ source: r.qrBuffer }, { caption, parse_mode: 'HTML' });
  return ctx.reply(caption + `\n${r.qrUrl || ''}`, { parse_mode: 'HTML' });
});

// User pilih metode deposit: Pakasir (QRIS/VA via pakasir.com)
bot.action('dep_method_pakasir', async (ctx) => {
  await safeCb(ctx);
  const sess = sessions.get(ctx.chat.id);
  const nominal = sess?.nominal;
  sessions.delete(ctx.chat.id);
  if (!nominal) return ctx.reply('❌ Sesi kedaluwarsa, ulangi dari menu deposit.');
  await ctx.reply('⏳ Membuat link pembayaran Pakasir...');
  const ref = ppob.refId('PKR');
  try {
    const p = await pakasir.createPayment(nominal, ref, 'qris');
    const { run } = require('./src/db');
    await run(
      `INSERT INTO transactions (telegram_id, type, amount, ref_id, payment_id, status, gateway)
       VALUES (?,?,?,?,?,?,?)`,
      [ctx.from.id, 'deposit', nominal, ref, p.orderId, 'pending', 'pakasir']
    );
    // QR dari QRIS string (pakai API QR publik)
    const qrImgUrl = `https://api.qrserver.com/v1/create-qr-code/?size=400x400&data=${encodeURIComponent(p.paymentNumber || p.paymentUrl)}`;
    const caption =
      `🧾 <b>Deposit via Pakasir ${digi.rp(nominal)}</b>\n` +
      `Ref: <code>${ref}</code>\n\n` +
      `Scan QR atau buka link bayar:\n${p.paymentUrl}\n\n` +
      `Saldo masuk otomatis setelah pembayaran terdeteksi.`;
    const kb = Markup.inlineKeyboard([
      [Markup.button.url('🔗 Buka Link Bayar', p.paymentUrl)],
      [sBtn('🔄 Cek Status', `dep_pkcheck_${ref}`, 'primary')],
    ]);
    // Pakai URL button bila valid, fallback ke tombol cek status saja
    try {
      await ctx.replyWithPhoto(qrImgUrl, { caption, parse_mode: 'HTML', reply_markup: kb.reply_markup });
    } catch (_) {
      await ctx.reply(caption, { parse_mode: 'HTML', reply_markup: kb.reply_markup });
    }
  } catch (e) {
    return ctx.reply(`❌ Gagal membuat pembayaran Pakasir: ${esc(e.message)}`);
  }
});

// Cek status manual deposit Pakasir
bot.action(/^dep_pkcheck_(.+)$/, async (ctx) => {
  await safeCb(ctx);
  const ref = ctx.match[1];
  const { get } = require('./src/db');
  const tx = await get(
    `SELECT amount, payment_id, status FROM transactions WHERE ref_id = ? AND gateway = 'pakasir'`,
    [ref]
  ).catch(() => null);
  if (!tx) return ctx.reply('❌ Transaksi tidak ditemukan.');
  if (tx.status !== 'pending') return ctx.reply(`ℹ️ Status transaksi: <b>${esc(tx.status)}</b>`, { parse_mode: 'HTML' });
  try {
    const s = await pakasir.checkStatus(tx.payment_id, tx.amount);
    if (s.status === 'completed') {
      return ctx.reply('✅ Pembayaran terdeteksi lunas! Saldo akan masuk otomatis (tunggu polling).');
    }
    const label = { pending: 'menunggu pembayaran', cancelled: 'dibatalkan', expired: 'kedaluwarsa' }[s.status] || s.status;
    return ctx.reply(`⏳ Status: <b>${label}</b>.`, { parse_mode: 'HTML' });
  } catch (e) {
    return ctx.reply(`❌ Gagal cek status: ${esc(e.message)}`);
  }
});

// Tampilkan daftar produk PPOB (dipakai tombol Beli & Daftar Produk)
async function showProductList(ctx, group, page = 1) {
  await safeCb(ctx);
  const r = await ppob.productList(group, page)
    .catch((e) => ({ success: false, message: `❌ ${esc(e.message)}` }));
  if (!r.success) { await ctx.reply(r.message, { parse_mode: 'HTML' }); return; }
  if (r.pageItems) prodCache.set(ctx.from.id, { pageItems: r.pageItems, page: r.page, group: group || '', _ts: Date.now() });
  const extra = { parse_mode: 'HTML', reply_markup: ppob.productKeyboard(r.page, r.pages, r.pageItems, group || '') };
  try { await ctx.editMessageText(r.message, extra); }
  catch (e) { await ctx.reply(r.message, extra); }
}

bot.action('ppob_beli', async (ctx) => {
  await showProductList(ctx, 'pulsa');
});

bot.action('ppob_produk', async (ctx) => {
  await showProductList(ctx, 'lainnya');
});

// Kategori PPOB (tombol grid): ppob_cat_<group>
bot.action(/^ppob_cat_([a-z0-9-]+)$/, async (ctx) => {
  await showProductList(ctx, ctx.match[1]);
});

// Prabayar / Pascabayar
bot.action('ppob_prabayar', async (ctx) => {
  await showProductList(ctx, 'prabayar');
});
bot.action('ppob_pascabayar', async (ctx) => {
  await showProductList(ctx, 'pascabayar');
});

// Produk populer
bot.action('ppob_populer', async (ctx) => {
  await showProductList(ctx, 'populer');
});

// Cari produk — minta keyword via session
bot.action('ppob_cari', async (ctx) => {
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'ppob_cari' });
  await ctx.reply('🔍 Kirim <b>kata kunci</b> produk yang dicari (contoh: <code>telkomsel 10</code>):', { parse_mode: 'HTML' });
});
bot.action(/^prod_page_([a-z0-9-: ]*?)_(\d+)$/, async (ctx) => {
  await showProductList(ctx, ctx.match[1] || undefined, parseInt(ctx.match[2], 10));
});

// Tombol beli produk PPOB
bot.action(/^prod_buy_([a-z0-9-: ]*?)_(\d+)_(\d+)$/, async (ctx) => {
  await safeCb(ctx);
  const page = parseInt(ctx.match[2], 10);
  const idx = parseInt(ctx.match[3], 10);
  const cached = prodCache.get(ctx.from.id);
  if (!cached || !cached.pageItems || cached.page !== page || (cached.group || '') !== (ctx.match[1] || '') || !cached.pageItems[idx]) {
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
  await showProductList(ctx, 'lainnya');
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
  if (await admin.hasAdminAccess(ctx)) {
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
  if (!await admin.hasAdminAccess(ctx)) return;
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
  if (!await admin.hasAdminAccess(ctx)) return;
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await sendMenuPhoto(ctx, 'menu-utama.png', '🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', adminPanel());
});

bot.command('admin', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) return ctx.reply('❌ Khusus admin.');
  await safeCb(ctx).catch(() => {});
  await sendMenuPhoto(ctx, 'menu-utama.png',
    '🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:',
    adminPanel());
});

// ---------- Kelola Server ----------
// Tambah server: nama -> domain -> harga (ketik manual dari keyboard)
bot.action('adm_addserver', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_addserver_nama', data: {} });
  await ctx.reply('➕ <b>Tambah Server</b>\n\nKetik <b>nama server</b>:', { parse_mode: 'HTML' });
});

// Hapus server: tampilkan daftar dengan tombol hapus
bot.action('adm_delserver', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const id = parseInt(ctx.match[1], 10);
  const { run } = require('./src/db');
  const r = await run('DELETE FROM servers WHERE id = ?', [id]);
  await ctx.reply(r.changes > 0 ? `✅ Server ID <code>${id}</code> dihapus.` : '⚠️ Server tidak ditemukan.', { parse_mode: 'HTML' });
});

// Edit harga: pilih server -> ketik harga baru dari keyboard
bot.action('adm_editharga', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  try {
    await ctx.editMessageText('🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', {
      parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
    });
  } catch (e) {
    await ctx.reply('🛠️ <b>PANEL ADMIN</b>\n\nPilih menu:', { parse_mode: 'HTML', reply_markup: adminPanel().reply_markup });
  }
});

// ---------- Harga VPN per Role ----------
// Admin mengatur harga Rp/hari per produk VPN untuk role member & reseller.
// Semua role melihat produk yang sama; role 'admin' beli dengan harga 0 (modal).
bot.action('adm_vpnprices', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const rows = await vpn.listVpnPrices().catch(() => []);
  const byKey = {};
  for (const r of rows) {
    byKey[r.product_key] = byKey[r.product_key] || {};
    byKey[r.product_key][r.role] = r.price;
  }
  const rp = (n) => 'Rp' + Number(n).toLocaleString('id-ID');
  const lines = vpn.VPN_PRODUCTS.map((p) => {
    const m = byKey[p.key]?.member ?? vpn.DEFAULT_VPN_PRICE.member;
    const r = byKey[p.key]?.reseller ?? vpn.DEFAULT_VPN_PRICE.reseller;
    return `• <b>${p.label}</b> — member: <b>${rp(m)}/hari</b>, reseller: <b>${rp(r)}/hari</b>`;
  });
  const btns = vpn.VPN_PRODUCTS.map((p) => [sBtn(`✏️ ${p.label}`, `adm_price_${p.key}`, 'primary')]);
  btns.push([sBtn('🔙 Kembali ke Panel', 'adm_back', 'danger')]);
  await ctx.reply(
    `💲 <b>Harga VPN per Role</b>\n\n${lines.join('\n')}\n\nPilih produk untuk ubah harga:`,
    { parse_mode: 'HTML', reply_markup: { inline_keyboard: btns } }
  );
});

bot.action(/^adm_price_([a-z]+)$/, async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const key = ctx.match[1];
  const prod = vpn.VPN_PRODUCTS.find((p) => p.key === key);
  if (!prod) return ctx.reply('❌ Produk tidak dikenal.');
  await ctx.reply(
    `💲 <b>Ubah Harga: ${prod.label}</b>\n\nPilih role yang harganya mau diubah:`,
    {
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: [
          [sBtn('👤 Member', `adm_pricerole_${key}_member`, 'primary'), sBtn('🤝 Reseller', `adm_pricerole_${key}_reseller`, 'success')],
          [sBtn('🔙 Kembali', 'adm_vpnprices', 'danger')],
        ],
      },
    }
  );
});

bot.action(/^adm_pricerole_([a-z]+)_(member|reseller)$/, async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const key = ctx.match[1];
  const role = ctx.match[2];
  const cur = await vpn.getVpnPrice(key, role);
  sessions.set(ctx.chat.id, { step: 'adm_price_input', data: { key, role } });
  await ctx.reply(
    `💲 <b>Ubah Harga VPN</b>\n\n📦 Produk: <b>${esc(key)}</b>\n👤 Role: <b>${role}</b>\n📌 Harga saat ini: <b>Rp${Number(cur).toLocaleString('id-ID')}/hari</b>\n\nKetik <b>harga baru per hari</b> (angka saja, contoh: 500):`,
    { parse_mode: 'HTML' }
  );
});

// ---------- Kelola Role ----------
bot.action('adm_roles', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const counts = await admin.countUsersByRole().catch(() => []);
  const c = {};
  for (const r of counts) c[r.role] = r.c;
  await ctx.reply(
    `👥 <b>Kelola Role User</b>\n\n` +
    `🛡️ Admin: <b>${c.admin || 0}</b>\n` +
    `🤝 Reseller: <b>${c.reseller || 0}</b>\n` +
    `👤 Member: <b>${c.member || 0}</b>\n\n` +
    `Pilih aksi:`,
    {
      parse_mode: 'HTML',
      reply_markup: {
        inline_keyboard: [
          [sBtn('📋 List Admin', 'adm_rolelist_admin', 'primary'), sBtn('📋 List Reseller', 'adm_rolelist_reseller', 'success')],
          [sBtn('📋 List Member', 'adm_rolelist_member', 'primary'), sBtn('✏️ Ubah Role User', 'adm_roleset', 'danger')],
          [sBtn('🔙 Kembali ke Panel', 'adm_back', 'danger')],
        ],
      },
    }
  );
});

bot.action(/^adm_rolelist_(admin|reseller|member)$/, async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const role = ctx.match[1];
  const rows = await admin.listUsersByRole(role, 30);
  if (!rows.length) {
    return ctx.reply(`📭 Belum ada user dengan role <b>${role}</b>.`, {
      parse_mode: 'HTML',
      reply_markup: { inline_keyboard: [[sBtn('🔙 Kembali', 'adm_roles', 'danger')]] },
    });
  }
  const lines = rows.map((u, i) =>
    `${i + 1}. <code>${u.telegram_id}</code> ${esc(u.username || '-')}` +
    (role !== 'admin' ? ` — Rp${Number(u.saldo || 0).toLocaleString('id-ID')}` : '')
  );
  await ctx.reply(`👥 <b>Daftar ${role} (${rows.length})</b>\n\n${lines.join('\n')}`, {
    parse_mode: 'HTML',
    reply_markup: { inline_keyboard: [[sBtn('🔙 Kembali', 'adm_roles', 'danger')]] },
  });
});

bot.action('adm_roleset', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_role_id', data: {} });
  await ctx.reply(
    `✏️ <b>Ubah Role User</b>\n\nKetik <b>ID Telegram</b> user yang mau diubah rolenya (angka saja):`,
    { parse_mode: 'HTML' }
  );
});

bot.action(/^adm_roleset_(\d+)_(admin|reseller|member)$/, async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const uid = Number(ctx.match[1]);
  const role = ctx.match[2];
  // Owner tidak bisa diturunkan rolenya — akses owner selalu via config.adminId
  if (uid === config.adminId && role !== 'admin') {
    return ctx.reply('❌ Tidak bisa mengubah role owner.');
  }
  try {
    await ppob.setRole(uid, role);
    await ctx.reply(`✅ Role user <code>${uid}</code> diubah menjadi <b>${role}</b>.`, { parse_mode: 'HTML' });
  } catch (e) {
    await ctx.reply(`❌ ${esc(e.message)}`);
  }
});

// ---------- Keuangan ----------
// Tambah saldo: ketik "userId jumlah" dari keyboard
bot.action('adm_addsaldo', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_addsaldo_input', data: {} });
  await ctx.reply('💵 <b>Tambah Saldo</b>\n\nKetik dengan format:\n<code>userId jumlah</code>\nContoh: <code>123456 50000</code>', { parse_mode: 'HTML' });
});

// Kurangi saldo: ketik "userId jumlah" dari keyboard
bot.action('adm_minsaldo', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_minsaldo_input', data: {} });
  await ctx.reply('➖ <b>Kurangi Saldo</b>\n\nKetik dengan format:\n<code>userId jumlah</code>\nContoh: <code>123456 10000</code>', { parse_mode: 'HTML' });
});

// Hasil penjualan
bot.action('adm_sales', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
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
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await ctx.reply(
    '⚠️ <b>Restore Database</b>\n\n' +
    'Kirim file <b>.db</b> backup sebagai dokumen ke chat ini untuk restore.\n' +
    'Bot akan restart setelah restore.',
    { parse_mode: 'HTML' }
  );
  sessions.set(ctx.chat.id, { step: 'restore_db' });
});

// ---------- Setting Pakasir ----------
const pakasir = require('./modules/pakasir');

async function showPakasirPanel(ctx) {
  const c = await pakasir.getConfig();
  const status = c.enabled && c.slug && c.api_key ? '🟢 Aktif' : (c.slug && c.api_key ? '🟡 Terisi (nonaktif)' : '🔴 Belum dikonfigurasi');
  const text =
    `🧾 <b>Setting Pakasir</b>\n\n` +
    `Status: <b>${status}</b>\n` +
    `🔗 Slug: <code>${esc(c.slug || '(kosong)')}</code>\n` +
    `🔑 API Key: <code>${pakasir.maskKey(c.api_key)}</code>\n\n` +
    `Pakasir = metode bayar kedua (selain GoPay QRIS).\n` +
    `User bisa pilih saat deposit bila sudah aktif.`;
  const kb = Markup.inlineKeyboard([
    [sBtn('🔗 Set Slug', 'adm_pakasir_slug', 'primary'), sBtn('🔑 Set API Key', 'adm_pakasir_key', 'primary')],
    [sBtn('🧪 Tes Koneksi', 'adm_pakasir_test', 'success'), sBtn(c.enabled ? '⏸️ Nonaktifkan' : '▶️ Aktifkan', 'adm_pakasir_toggle', c.enabled ? 'danger' : 'success')],
    [sBtn('🔙 Kembali', 'adm_open', 'danger')],
  ]);
  await ctx.reply(text, { parse_mode: 'HTML', reply_markup: kb.reply_markup });
}

bot.action('adm_pakasir', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await showPakasirPanel(ctx);
});

bot.action('adm_pakasir_slug', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_pakasir_slug' });
  await ctx.reply('🔗 Kirim <b>slug project Pakasir</b> (lihat di halaman detail project pakasir.com):', { parse_mode: 'HTML' });
});

bot.action('adm_pakasir_key', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_pakasir_key' });
  await ctx.reply('🔑 Kirim <b>API key Pakasir</b> (lihat di halaman detail project pakasir.com):', { parse_mode: 'HTML' });
});

bot.action('adm_pakasir_test', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await ctx.reply('⏳ Mengetes koneksi ke Pakasir...');
  const r = await pakasir.testConnection();
  await ctx.reply(r.message, { parse_mode: 'HTML' });
});

bot.action('adm_pakasir_toggle', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const c = await pakasir.getConfig();
  if (!c.slug || !c.api_key) {
    return ctx.reply('❌ Isi slug & API key dulu sebelum mengaktifkan.');
  }
  await pakasir.setEnabled(!c.enabled);
  await ctx.reply(`✅ Pakasir ${!c.enabled ? '<b>diaktifkan</b>' : '<b>dinonaktifkan</b>'}.`, { parse_mode: 'HTML' });
  await showPakasirPanel(ctx);
});

// ============================================================
// ---------- Bonus Topup & Minimal Topup Reseller ----------
// ============================================================
async function showBonusPanel(ctx) {
  const cfg = await ppob.getBonusConfig();
  const minRes = await settings.getResellerMinTopup();
  const text =
    `🎁 <b>Bonus Topup & Reseller</b>\n\n` +
    `<b>Bonus Topup:</b> ${cfg.enabled ? '✅ Aktif' : '❌ Nonaktif'}\n` +
    `• Min. topup: <b>${digi.rp(cfg.min_topup)}</b>\n` +
    `• Bonus: <b>${cfg.bonus_percent}%</b>\n\n` +
    `<b>Otomatis jadi Reseller:</b>\n` +
    `• Min. total topup: <b>${minRes > 0 ? digi.rp(minRes) : '(nonaktif)'}</b>\n` +
    (minRes > 0 ? `User yang total topup-nya mencapai nominal ini otomatis naik jadi 🏪 Reseller.\n` : ``);
  const kb = Markup.inlineKeyboard([
    [sBtn('🎁 Set Bonus', 'adm_bonus_set', 'success'), sBtn(cfg.enabled ? '⏸️ Matikan Bonus' : '▶️ Nyalakan Bonus', 'adm_bonus_toggle', cfg.enabled ? 'danger' : 'success')],
    [sBtn('🏪 Set Min. Topup Reseller', 'adm_resset', 'primary')],
    [sBtn('🔙 Kembali', 'adm_open', 'danger')],
  ]);
  await ctx.reply(text, { parse_mode: 'HTML', reply_markup: kb.reply_markup });
}

bot.action('adm_bonus', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await showBonusPanel(ctx);
});

bot.action('adm_bonus_set', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_bonus_input', data: {} });
  await ctx.reply(
    `🎁 <b>Set Bonus Topup</b>\n\nKetik dengan format:\n<code>min_topup persen</code>\nContoh: <code>50000 10</code> (topup min 50rb dapat bonus 10%)\n\nKetik <code>0 0</code> untuk menonaktifkan.`,
    { parse_mode: 'HTML' }
  );
});

bot.action('adm_bonus_toggle', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const cfg = await ppob.getBonusConfig();
  if (cfg.enabled) {
    await ppob.setBonusConfig(0, 0);
    await ctx.reply('✅ Bonus topup <b>dinonaktifkan</b>.', { parse_mode: 'HTML' });
  } else {
    if (!cfg.min_topup || !cfg.bonus_percent) {
      return ctx.reply('❌ Set dulu nominal & persen bonus via tombol 🎁 Set Bonus.');
    }
    await ppob.setBonusConfig(cfg.min_topup, cfg.bonus_percent);
    await ctx.reply('✅ Bonus topup <b>diaktifkan</b>.', { parse_mode: 'HTML' });
  }
  await showBonusPanel(ctx);
});

bot.action('adm_resset', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_resset_input', data: {} });
  await ctx.reply(
    `🏪 <b>Min. Topup Otomatis Reseller</b>\n\nKetik <b>nominal rupiah</b> (angka saja).\nContoh: <code>500000</code>\n\nUser yang total topup sukses-nya mencapai nominal ini otomatis jadi Reseller.\nKetik <code>0</code> untuk menonaktifkan.`,
    { parse_mode: 'HTML' }
  );
});

// ============================================================
// ---------- Broadcast ke Grup ----------
// ============================================================
async function showBcastPanel(ctx) {
  const groups = await settings.listBroadcastGroups();
  const lines = groups.length
    ? groups.map((g, i) => `${i + 1}. <code>${esc(g.chat_id)}</code>${g.title ? ` — ${esc(g.title)}` : ''}`).join('\n')
    : '<i>Belum ada grup terdaftar.</i>';
  const kb = [
    [sBtn('➕ Tambah Grup', 'adm_bcast_add', 'success'), sBtn('❌ Hapus Grup', 'adm_bcast_del', 'danger')],
    [sBtn('📝 Tulis & Kirim Broadcast', 'adm_bcast_send', 'primary')],
    [sBtn('🔙 Kembali', 'adm_open', 'danger')],
  ];
  await ctx.reply(
    `📢 <b>Broadcast ke Grup</b>\n\n<b>Grup terdaftar (${groups.length}):</b>\n${lines}`,
    { parse_mode: 'HTML', reply_markup: Markup.inlineKeyboard(kb).reply_markup }
  );
}

bot.action('adm_bcast', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await showBcastPanel(ctx);
});

bot.action('adm_bcast_add', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_bcast_add', data: {} });
  await ctx.reply(
    `➕ <b>Tambah Grup Broadcast</b>\n\nKetik <b>ID grup</b> (contoh: <code>-1001234567890</code>).\n` +
    `Cara dapat ID: tambahkan bot ke grup, lalu forward pesan dari grup ke @userinfobot.\n\n` +
    `Bot harus jadi <b>admin</b> di grup tersebut agar bisa kirim pesan.`,
    { parse_mode: 'HTML' }
  );
});

bot.action('adm_bcast_del', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const groups = await settings.listBroadcastGroups();
  if (!groups.length) return ctx.reply('❌ Belum ada grup terdaftar.');
  const kb = groups.map((g) => [sBtn(`❌ ${g.title || g.chat_id}`, `adm_bcastdel_${g.id}`, 'danger')]);
  kb.push([sBtn('🔙 Kembali', 'adm_bcast', 'danger')]);
  await ctx.reply('❌ <b>Hapus Grup Broadcast</b>\n\nPilih grup:', {
    parse_mode: 'HTML', reply_markup: { inline_keyboard: kb },
  });
});

bot.action(/^adm_bcastdel_(\d+)$/, async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const ok = await settings.delBroadcastGroup(ctx.match[1]);
  await ctx.reply(ok ? '✅ Grup dihapus dari daftar broadcast.' : '⚠️ Grup tidak ditemukan.');
  await showBcastPanel(ctx);
});

bot.action('adm_bcast_send', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const groups = await settings.listBroadcastGroups();
  if (!groups.length) return ctx.reply('❌ Belum ada grup terdaftar. Tambah dulu via ➕ Tambah Grup.');
  sessions.set(ctx.chat.id, { step: 'adm_bcast_msg', data: {} });
  await ctx.reply(
    `📝 <b>Tulis Pesan Broadcast</b>\n\nKetik pesan yang akan dikirim ke <b>${groups.length} grup</b>.\n` +
    `Mendukung format HTML sederhana (&lt;b&gt;, &lt;i&gt;, &lt;code&gt;).`,
    { parse_mode: 'HTML' }
  );
});

// ============================================================
// ---------- Broadcast ke User ----------
// ============================================================
bot.action('adm_bcastuser', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const kb = [
    [sBtn('👥 Semua User', 'adm_bcu_t_all', 'primary')],
    [sBtn('👤 Hanya Member', 'adm_bcu_t_member', 'success'), sBtn('🏪 Hanya Reseller', 'adm_bcu_t_reseller', 'success')],
    [sBtn('🔙 Kembali', 'adm_open', 'danger')],
  ];
  await ctx.reply(
    `📣 <b>Broadcast ke User</b>\n\nPilih target penerima:`,
    { parse_mode: 'HTML', reply_markup: Markup.inlineKeyboard(kb).reply_markup }
  );
});

for (const [tkey, tlabel] of [['all', 'Semua User'], ['member', 'Member'], ['reseller', 'Reseller']]) {
  bot.action(`adm_bcu_t_${tkey}`, async (ctx) => {
    if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
    await safeCb(ctx);
    sessions.set(ctx.chat.id, { step: 'adm_bcu_msg', data: { target: tkey, tlabel } });
    await ctx.reply(
      `📝 <b>Tulis Pesan Broadcast</b>\n\nTarget: <b>${tlabel}</b>\n\nKetik pesan yang akan dikirim.\nMendukung format HTML sederhana (&lt;b&gt;, &lt;i&gt;, &lt;code&gt;).`,
      { parse_mode: 'HTML' }
    );
  });
}

bot.action('adm_bcu_confirm', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const sess = sessions.get(ctx.chat.id);
  if (!sess || sess.step !== 'adm_bcu_confirm') return ctx.reply('❌ Sesi kedaluwarsa. Ulangi dari awal.');
  const { target, tlabel, pesan } = sess.data;
  sessions.delete(ctx.chat.id);
  const { all } = require('./src/db');
  const rows = target === 'all'
    ? await all('SELECT telegram_id FROM users')
    : await all('SELECT telegram_id FROM users WHERE role = ?', [target]);
  const ids = [...new Set(rows.map((r) => r.telegram_id).filter(Boolean))];
  if (!ids.length) return ctx.reply('❌ Tidak ada user pada target ini.');
  await ctx.reply(`⏳ Mengirim broadcast ke ${ids.length} user (${tlabel})...`);
  let ok = 0, fail = 0;
  for (const uid of ids) {
    try {
      await ctx.telegram.sendMessage(uid, `📢 <b>Pengumuman</b>\n\n${pesan}`, { parse_mode: 'HTML' });
      ok++;
    } catch (e) { fail++; }
    await new Promise((r) => setTimeout(r, 50));
  }
  console.log(`[bcast-user] target=${target} ok=${ok} fail=${fail}`);
  notifGrup(bot, `📣 <b>Broadcast User</b>\n👤 Admin: ${ctx.from.username ? '@' + ctx.from.username : ctx.from.first_name}\n🎯 Target: ${tlabel}\n✅ Terkirim: ${ok} user${fail ? `\n❌ Gagal: ${fail} user` : ''}`);
  return ctx.reply(`✅ Broadcast selesai.\n🎯 Target: <b>${tlabel}</b>\n📨 Terkirim: <b>${ok}</b> user${fail ? `\n❌ Gagal: <b>${fail}</b> user` : ''}`, {
    parse_mode: 'HTML', reply_markup: adminPanel().reply_markup,
  });
});

bot.action('adm_bcu_cancel', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.delete(ctx.chat.id);
  await ctx.reply('❌ Broadcast dibatalkan.', { reply_markup: adminPanel().reply_markup });
});

// ============================================================
// ---------- Grup Notifikasi Transaksi ----------
// ============================================================
bot.action('adm_notifgrp', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const cur = await settings.getNotifGroup();
  sessions.set(ctx.chat.id, { step: 'adm_notifgrp_input', data: {} });
  await ctx.reply(
    `🔔 <b>Grup Notifikasi Transaksi</b>\n\n` +
    `ID saat ini: <code>${esc(cur || '(belum diatur)')}</code>\n\n` +
    `Semua notifikasi (deposit, pembelian VPN/PPOB, topup) dikirim ke grup ini.\n` +
    `Bot harus jadi <b>admin</b> di grup tersebut.\n\n` +
    `Ketik <b>ID grup baru</b> (contoh: <code>-1001234567890</code>), atau kirim pesan dari grup yang sudah ada.`,
    { parse_mode: 'HTML' }
  );
});

// ============================================================
// ---------- Force Join Channel & Grup ----------
// ============================================================
async function showForceJoinPanel(ctx) {
  const fj = await settings.getForceJoin();
  const text =
    `🔒 <b>Force Join</b>\n\n` +
    `Status: <b>${fj.enabled ? '✅ Aktif' : '❌ Nonaktif'}</b>\n\n` +
    `📢 Channel: <code>${esc(fj.channelId || '(kosong)')}</code>\n` +
    `🔗 Link: ${esc(fj.channelUrl || '-')}\n\n` +
    `👥 Grup: <code>${esc(fj.groupId || '(kosong)')}</code>\n` +
    `🔗 Link: ${esc(fj.groupUrl || '-')}\n\n` +
    `<i>User baru wajib join sebelum bisa pakai bot. Admin selalu lolos.</i>`;
  const kb = Markup.inlineKeyboard([
    [sBtn('📢 Set Channel', 'adm_fj_channel', 'primary'), sBtn('👥 Set Grup', 'adm_fj_group', 'primary')],
    [sBtn(fj.enabled ? '⏸️ Nonaktifkan' : '▶️ Aktifkan', 'adm_fj_toggle', fj.enabled ? 'danger' : 'success')],
    [sBtn('🔙 Kembali', 'adm_open', 'danger')],
  ]);
  await ctx.reply(text, { parse_mode: 'HTML', reply_markup: kb.reply_markup });
}

bot.action('adm_forcejoin', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  await showForceJoinPanel(ctx);
});

bot.action('adm_fj_channel', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_fj_channel', data: {} });
  await ctx.reply(
    `📢 <b>Set Channel Wajib Join</b>\n\nKetik dengan format:\n<code>ID | link_undangan</code>\n` +
    `Contoh: <code>@Wendi_Channel | https://t.me/Wendi_Channel</code>\n\n` +
    `Kosongkan ID (ketik <code>-</code>) untuk menonaktifkan cek channel.`,
    { parse_mode: 'HTML' }
  );
});

bot.action('adm_fj_group', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  sessions.set(ctx.chat.id, { step: 'adm_fj_group', data: {} });
  await ctx.reply(
    `👥 <b>Set Grup Wajib Join</b>\n\nKetik dengan format:\n<code>ID | link_undangan</code>\n` +
    `Contoh: <code>-1001234567890 | https://t.me/Wendi_VPN</code>\n\n` +
    `Kosongkan ID (ketik <code>-</code>) untuk menonaktifkan cek grup.`,
    { parse_mode: 'HTML' }
  );
});

bot.action('adm_fj_toggle', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) { await safeCb(ctx); return; }
  await safeCb(ctx);
  const fj = await settings.getForceJoin();
  await settings.setSetting('force_join_enabled', fj.enabled ? '0' : '1');
  await ctx.reply(`✅ Force join <b>${fj.enabled ? 'dinonaktifkan' : 'diaktifkan'}</b>.`, { parse_mode: 'HTML' });
  await showForceJoinPanel(ctx);
});

// ---------- Reseller ----------
bot.command('setreseller', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) return ctx.reply('❌ Khusus admin.');
  const uid = ctx.message.text.split(' ')[1];
  if (!uid) return ctx.reply('Contoh: <code>/setreseller 123456</code>', { parse_mode: 'HTML' });
  await ppob.setRole(Number(uid), 'reseller');
  await ctx.reply(`✅ User <code>${uid}</code> kini <b>RESELLER</b> (diskon 10% VPN).`, { parse_mode: 'HTML' });
});

bot.command('unsetreseller', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) return ctx.reply('❌ Khusus admin.');
  const uid = ctx.message.text.split(' ')[1];
  if (!uid) return ctx.reply('Contoh: <code>/unsetreseller 123456</code>', { parse_mode: 'HTML' });
  await ppob.setRole(Number(uid), 'member');
  await ctx.reply(`✅ User <code>${uid}</code> dikembalikan jadi <b>member</b>.`, { parse_mode: 'HTML' });
});

// ---------- Bonus Topup ----------
bot.command('setbonus', async (ctx) => {
  if (!await admin.hasAdminAccess(ctx)) return ctx.reply('❌ Khusus admin.');
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
  if (!await admin.hasAdminAccess(ctx)) return;
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
// Deposit yang sudah dibayar di gateway (status paid/success/settled/completed)
// dikreditkan ke saldo user. Klaim atomik: hanya transaksi yang masih 'pending'
// yang diproses. Mendukung 2 gateway: gopay (P2P sendiri) & pakasir.
setInterval(async () => {
  try {
    const { all, run } = require('./src/db');
    const pending = await all(
      `SELECT telegram_id, amount, ref_id, payment_id, gateway FROM transactions
       WHERE type = 'deposit' AND status = 'pending' AND payment_id != ''
         AND created_at > datetime('now','-1 day')`
    ).catch(() => []);
    if (!pending.length) return;
    const { gatewayUrl, apiKey } = config.p2p;
    const axios = require('axios');
    const pakasirReady = await pakasir.isReady().catch(() => false);
    for (const tx of pending) {
      try {
        const gw = tx.gateway || 'gopay';
        let isPaid = false;
        if (gw === 'pakasir') {
          if (!pakasirReady) continue;
          const s = await pakasir.checkStatus(tx.payment_id, tx.amount).catch(() => null);
          if (!s) continue;
          if (s.status === 'completed') isPaid = true;
          else if (s.status === 'expired' || s.status === 'cancelled') {
            await run(`UPDATE transactions SET status = ? WHERE ref_id = ? AND status = 'pending'`,
              [s.status, tx.ref_id]);
            continue;
          } else continue; // masih pending
        } else {
          if (!apiKey) continue;
          const { data } = await axios.get(
            `${gatewayUrl}/api/payments/${encodeURIComponent(tx.payment_id)}`,
            { headers: { 'X-API-Key': apiKey }, timeout: 15000 }
          ).catch(() => ({ data: {} }));
          const st = String(data?.status || '').toLowerCase();
          if (!['paid', 'success', 'settled'].includes(st)) continue;
          isPaid = true;
        }
        if (!isPaid) continue;
        const r = await run(
          `UPDATE transactions SET status = 'success' WHERE ref_id = ? AND status = 'pending'`,
          [tx.ref_id]
        );
        if (!r.changes) continue; // sudah diproses (anti dobel kredit)
        const s = await ppob.addSaldo(tx.telegram_id, tx.amount);
        // Otomatis jadi reseller bila total topup mencapai batas (diatur admin)
        try {
          const minRes = await settings.getResellerMinTopup();
          if (minRes > 0) {
            const curRole = await ppob.getRole(tx.telegram_id).catch(() => 'member');
            if (curRole === 'member') {
              const tot = await get(
                `SELECT COALESCE(SUM(amount),0) AS t FROM transactions
                 WHERE telegram_id = ? AND type = 'deposit' AND status = 'success'`,
                [tx.telegram_id]
              ).catch(() => ({ t: 0 }));
              if (Number(tot?.t || 0) >= minRes) {
                await ppob.setRole(tx.telegram_id, 'reseller');
                await bot.telegram.sendMessage(
                  tx.telegram_id,
                  `🏪 <b>Selamat! Kamu kini RESELLER</b>\n\nTotal topup kamu mencapai <b>${digi.rp(minRes)}</b>.\nNikmati harga khusus reseller untuk VPN!`,
                  { parse_mode: 'HTML' }
                ).catch(() => {});
                notifGrup(bot, `🏪 <b>User naik jadi Reseller</b>\n👤 ID: <code>${tx.telegram_id}</code>\n💰 Total topup: <b>${digi.rp(tot.t)}</b>`);
              }
            }
          }
        } catch (e) { console.error('[deposit] auto-reseller error:', e.message); }
        await bot.telegram.sendMessage(
          tx.telegram_id,
          `✅ <b>Deposit diterima!</b>\n💰 <b>${digi.rp(tx.amount)}</b> masuk ke saldo kamu.` +
          `\n🧾 Ref: <code>${esc(tx.ref_id)}</code>` +
          `\n💳 Saldo sekarang: <b>${digi.rp(s.saldo)}</b>`,
          { parse_mode: 'HTML' }
        ).catch(() => {});
        console.log(`[deposit] ${tx.ref_id} lunas (${gw}) → saldo +${tx.amount} (tg:${tx.telegram_id})`);
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
  if (!await admin.hasAdminAccess(ctx)) return;
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
  await vpn.seedVpnPrices().catch((e) => console.error('seed vpn prices:', e.message));
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
  if (!(await admin.hasAdminAccess(ctx))) return ctx.reply('❌ Khusus admin.');
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
  if (!(await admin.hasAdminAccess(ctx))) return ctx.reply('❌ Khusus admin.');
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
