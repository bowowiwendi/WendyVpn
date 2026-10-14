// ============================================================
// Modul Admin — broadcast, tambah saldo, statistik
// ============================================================
const config = require('../src/config');
const digi = require('../src/digiflazz');
const { run, get, all } = require('../src/db');

const isAdmin = (ctx) => ctx.from?.id === config.adminId;

async function statistik() {
  const users = await get('SELECT COUNT(*) c FROM users');
  const acc = await all('SELECT proto, COUNT(*) c, SUM(is_trial) t FROM vpn_accounts GROUP BY proto');
  const expired = await get("SELECT COUNT(*) c FROM vpn_accounts WHERE date(expiry) < date('now')");
  const trx = await get("SELECT COUNT(*) c, COALESCE(SUM(amount),0) s FROM transactions WHERE status = 'success'");
  const lines = acc.map((a) => `• ${a.proto}: ${a.c} (trial: ${a.t || 0})`);
  return (
    `📊 <b>Statistik Bot</b>\n\n` +
    `👥 User Telegram: <b>${users.c}</b>\n` +
    `🔑 Akun VPN:\n${lines.join('\n') || '—'}\n` +
    `⏰ Kadaluarsa: <b>${expired.c}</b>\n` +
    `💰 Transaksi sukses: <b>${trx.c}</b> (${digi.rp(trx.s)})`
  );
}

async function broadcastList() {
  const rows = await all('SELECT telegram_id FROM users');
  return rows.map((r) => r.telegram_id);
}

const TEMPLATES = {
  info: (t) => `📢 <b>INFORMASI</b>\n\n${t}`,
  promo: (t) => `🎉 <b>PROMO</b>\n\n${t}`,
  maint: (t) => `🔧 <b>MAINTENANCE</b>\n\n${t}`,
};

module.exports = { isAdmin, statistik, broadcastList, TEMPLATES };
