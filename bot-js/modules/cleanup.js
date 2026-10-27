// ============================================================
// Auto-cleanup — hapus akun trial menumpuk, akun kadaluarsa,
// dan akun tidak terpakai. Notif expire dikirim MAKSIMAL 1x
// per akun (anti-spam).
// ============================================================
const { run, get, all } = require('../src/db');
const vpn = require('./vpn');

const today = () => new Date().toISOString().slice(0, 10);

async function alreadyNotified(accountId) {
  const row = await get('SELECT 1 FROM notified_expired WHERE account_id = ?', [accountId]);
  return !!row;
}

async function markNotified(accountId) {
  await run('INSERT OR IGNORE INTO notified_expired (account_id) VALUES (?)', [accountId]);
}

// Hapus akun kadaluarsa; kirim notif 1x bila belum pernah
async function cleanupExpired(notifyFn) {
  const rows = await all("SELECT * FROM vpn_accounts WHERE date(expiry) < date('now')");
  let deleted = 0, notified = 0;
  for (const acc of rows) {
    let res = null;
    try { res = await vpn.deleteAccount(acc.proto, acc.username); } catch { res = null; }
    if (!res || !res.success) continue; // gagal hapus di server: baris dipertahankan
    await run('DELETE FROM vpn_accounts WHERE id = ?', [acc.id]);
    deleted++;
    // Trial yang dihapus: tanpa notif. Reguler: notif 1x, ditandai hanya
    // bila benar terkirim (gagal kirim = coba lagi siklus berikut).
    if (!acc.is_trial && !(await alreadyNotified(acc.id))) {
      let sent = true;
      if (notifyFn) {
        try { await notifyFn(acc); } catch { sent = false; }
      }
      if (sent) {
        await markNotified(acc.id);
        notified++;
      }
    }
  }
  return { deleted, notified };
}

// Hapus trial yang menumpuk (lebih dari maxAge hari sejak dibuat)
async function cleanupOldTrials(maxAgeDays = 3) {
  const rows = await all(
    "SELECT * FROM vpn_accounts WHERE is_trial = 1 AND date(created_at, '+' || ? || ' days') < date('now')",
    [maxAgeDays]
  );
  for (const acc of rows) {
    let res = null;
    try { res = await vpn.deleteAccount(acc.proto, acc.username); } catch { res = null; }
    if (!res || !res.success) continue; // gagal hapus di server: baris dipertahankan
    await run('DELETE FROM vpn_accounts WHERE id = ?', [acc.id]);
  }
  return { deleted: rows.length };
}

// Dry-run: tampilkan yang akan dihapus tanpa eksekusi
async function dryRun() {
  const expired = await all("SELECT proto, username, expiry, is_trial FROM vpn_accounts WHERE date(expiry) < date('now')");
  const oldTrials = await all(
    "SELECT proto, username, created_at FROM vpn_accounts WHERE is_trial = 1 AND date(created_at, '+3 days') < date('now')"
  );
  return { expired, oldTrials };
}

module.exports = { cleanupExpired, cleanupOldTrials, dryRun };
