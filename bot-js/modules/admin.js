// ============================================================
// Modul Admin — broadcast, tambah saldo, statistik
// ============================================================
const config = require('../src/config');
const digi = require('../src/digiflazz');
const { run, get, all } = require('../src/db');
const { esc } = require('../src/format');

// ============================================================
// ROLE:
//  - admin/owner : hanya config.adminId (Wendi). Semua command sensitif
//    (broadcast, tambah saldo, sewa list, statistik, dsb) wajib lewat
//    isAdmin() / isOwner().
//  - user        : semua pengguna Telegram lainnya. Hanya bisa pakai
//    fitur publik (buat akun trial, beli, cek saldo, dsb).
// Tidak ada tabel role terpisah; pembeda satu-satunya adalah adminId.
// ============================================================
const isAdmin = (ctx) => ctx.from?.id === config.adminId;

// Alias untuk kejelasan di command yang butuh "pemilik" mutlak.
const isOwner = (ctx) => ctx.from?.id === config.adminId;

// Cek akses admin berbasis role: owner (config.adminId) ATAU user dengan
// role 'admin' di tabel users. Versi async — pakai ini untuk gate menu admin.
async function hasAdminAccess(ctx) {
  if (!ctx?.from?.id) return false;
  if (isAdmin(ctx)) return true;
  try {
    const row = await get('SELECT role FROM users WHERE telegram_id = ?', [ctx.from.id]);
    return row?.role === 'admin';
  } catch {
    return false;
  }
}

async function listUsersByRole(role, limit = 50) {
  return all(
    'SELECT telegram_id, username, role, saldo FROM users WHERE role = ? ORDER BY telegram_id LIMIT ?',
    [role, limit]
  );
}

async function countUsersByRole() {
  return all('SELECT role, COUNT(*) c FROM users GROUP BY role');
}

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
  info: (t) => `📢 <b>INFORMASI</b>\n\n${esc(t)}`,
  promo: (t) => `🎉 <b>PROMO</b>\n\n${esc(t)}`,
  maint: (t) => `🔧 <b>MAINTENANCE</b>\n\n${esc(t)}`,
};

module.exports = { isAdmin, isOwner, hasAdminAccess, listUsersByRole, countUsersByRole, statistik, broadcastList, TEMPLATES };
