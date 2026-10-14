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

const { Telegraf, Markup } = require('telegraf');
const config = require('./src/config');
const { init: initDb } = require('./src/db');
const vpn = require('./modules/vpn');
const ppob = require('./modules/ppob');
const kuota = require('./modules/kuota');
const admin = require('./modules/admin');
const cleanup = require('./modules/cleanup');
const digi = require('./src/digiflazz');

if (!config.botToken) {
  console.error('❌ BOT_TOKEN belum diisi di .env');
  process.exit(1);
}

const bot = new Telegraf(config.botToken);
const sessions = new Map(); // chatId -> { step, data }

// ---------- Helper ----------
const mainMenu = () =>
  Markup.inlineKeyboard([
    [Markup.button.callback('🌐 VPN Premium', 'menu_vpn'), Markup.button.callback('🌐 VPN via CloudFront', 'menu_cf')],
    [Markup.button.callback('💳 PPOB / Pulsa', 'menu_ppob'), Markup.button.callback('📡 Cek Kuota', 'menu_kuota')],
    [Markup.button.callback('👤 Akun Saya', 'menu_akun'), Markup.button.callback('📊 Statistik', 'menu_stat')],
  ]);

const backBtn = () => Markup.inlineKeyboard([[Markup.button.callback('🔙 Kembali', 'menu_main')]]);

const vpnMenu = (cf = false) => {
  const p = cf ? 'cf_' : '';
  return Markup.inlineKeyboard([
    [Markup.button.callback('🔑 SSH', `${p}mk_ssh`), Markup.button.callback('💠 VMess', `${p}mk_vmess`)],
    [Markup.button.callback('⚡ VLess', `${p}mk_vless`), Markup.button.callback('🛡️ Trojan', `${p}mk_trojan`)],
    [Markup.button.callback('🎁 Trial', `${p}mk_trial`)],
    [Markup.button.callback('🔙 Kembali', 'menu_main')],
  ]);
};

const ensureUser = async (ctx) => {
  const { run } = require('./src/db');
  await run('INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)',
    [ctx.from.id, ctx.from.username || ctx.from.first_name || '']);
};

// ---------- /start ----------
bot.start(async (ctx) => {
  await ensureUser(ctx);
  await ctx.reply(
    `👋 Halo <b>${ctx.from.first_name || 'kawan'}</b>!\n\n` +
      `Selamat datang di <b>Wendi VPN Bot</b>.\nPilih layanan di bawah ini:`,
    { parse_mode: 'HTML', ...mainMenu() }
  );
});

bot.action('menu_main', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  await ctx.editMessageText('🏠 <b>Menu Utama</b>\nPilih layanan:', { parse_mode: 'HTML', ...mainMenu() }).catch(() => {});
});

// ---------- Menu VPN ----------
bot.action('menu_vpn', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  await ctx.editMessageText('🌐 <b>Menu VPN Premium</b>\nPilih protokol:', { parse_mode: 'HTML', ...vpnMenu(false) }).catch(() => {});
});

bot.action('menu_cf', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  await ctx.editMessageText(
    '☁️ <b>VPN via CloudFront</b>\nTrafik disamarkan sebagai HTTPS CloudFront.\nPilih protokol:',
    { parse_mode: 'HTML', ...vpnMenu(true) }
  ).catch(() => {});
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
  await ctx.answerCbQuery().catch(() => {});
}

for (const proto of ['ssh', 'vmess', 'vless', 'trojan']) {
  bot.action(`mk_${proto}`, (ctx) => handleCreate(ctx, proto, false));
  bot.action(`cf_mk_${proto}`, (ctx) => handleCreate(ctx, proto, true));
}

bot.action('mk_trial', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
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
  await ctx.answerCbQuery().catch(() => {});
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

// ---------- Akun Saya ----------
bot.action('menu_akun', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  const rows = await vpn.myAccounts(ctx.from.id);
  if (!rows.length) return ctx.reply('📭 Kamu belum punya akun VPN.', backBtn());
  const lines = rows.map((a, i) =>
    `${i + 1}. <b>${a.proto.toUpperCase()}</b> <code>${a.username}</code>\n   Exp: ${a.expiry}${a.via_cf ? ' ☁️CF' : ''}${a.is_trial ? ' 🎁trial' : ''}`
  );
  await ctx.editMessageText(`👤 <b>Akun Saya</b>\n\n${lines.join('\n')}`, { parse_mode: 'HTML', ...backBtn() }).catch(() =>
    ctx.reply(`👤 <b>Akun Saya</b>\n\n${lines.join('\n')}`, { parse_mode: 'HTML', ...backBtn() })
  );
});

// ---------- Menu PPOB ----------
bot.action('menu_ppob', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  const saldo = await ppob.getSaldo(ctx.from.id);
  await ctx.editMessageText(
    `💳 <b>Menu PPOB</b>\nSaldo: <b>${digi.rp(saldo)}</b>\n\nPilih:`,
    {
      parse_mode: 'HTML',
      ...Markup.inlineKeyboard([
        [Markup.button.callback('💰 Deposit / Top Up', 'ppob_deposit'), Markup.button.callback('🛒 Beli Pulsa/Paket', 'ppob_beli')],
        [Markup.button.callback('📦 Cek Order', 'ppob_cekorder'), Markup.button.callback('📋 Daftar Produk', 'ppob_produk')],
        [Markup.button.callback('🔙 Kembali', 'menu_main')],
      ]),
    }
  ).catch(() => {});
});

bot.action('ppob_deposit', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  sessions.set(ctx.chat.id, { step: 'deposit_nominal' });
  await ctx.reply('💰 Kirim <b>nominal deposit</b> (min Rp10.000):', { parse_mode: 'HTML' });
});

bot.action('ppob_beli', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  sessions.set(ctx.chat.id, { step: 'ppob_kode', data: {} });
  await ctx.reply('🛒 Kirim <b>kode produk</b> (lihat /produk):', { parse_mode: 'HTML' });
});

bot.action('ppob_produk', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  const r = await ppob.productList().catch((e) => ({ success: false, message: `❌ ${e.message}` }));
  await ctx.reply(r.message.slice(0, 4000), { parse_mode: 'HTML' });
});

bot.action('ppob_cekorder', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
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
  await ctx.answerCbQuery().catch(() => {});
  sessions.set(ctx.chat.id, { step: 'kuota_nomor' });
  await ctx.reply('📡 Kirim <b>nomor HP</b> (contoh: 083153170199):', { parse_mode: 'HTML' });
});

// ---------- Statistik (admin lihat global, user lihat ringkas) ----------
bot.action('menu_stat', async (ctx) => {
  await ctx.answerCbQuery().catch(() => {});
  if (admin.isAdmin(ctx)) {
    const s = await admin.statistik();
    return ctx.editMessageText(s, { parse_mode: 'HTML', ...backBtn() }).catch(() =>
      ctx.reply(s, { parse_mode: 'HTML', ...backBtn() }));
  }
  const rows = await vpn.myAccounts(ctx.from.id);
  await ctx.reply(`📊 Kamu punya <b>${rows.length}</b> akun VPN.`, { parse_mode: 'HTML', ...backBtn() });
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
  console.log('✅ Database siap');
  await bot.launch();
  console.log('🤖 Bot Wendi berjalan (@IdWendi_bot)');
})();

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));
