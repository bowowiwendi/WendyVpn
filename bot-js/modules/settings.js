// ============================================================
// Modul Settings — key-value pengaturan bot (diatur via panel admin)
// ============================================================
const { run, get, all } = require('../src/db');

async function getSetting(key, def = '') {
  const row = await get('SELECT value FROM bot_settings WHERE key = ?', [key]).catch(() => null);
  return row ? row.value : def;
}

async function setSetting(key, value) {
  await run(
    `INSERT INTO bot_settings (key, value) VALUES (?, ?)
     ON CONFLICT(key) DO UPDATE SET value = ?`,
    [key, String(value), String(value)]
  ).catch(async () => {
    const row = await get('SELECT value FROM bot_settings WHERE key = ?', [key]).catch(() => null);
    if (row) await run('UPDATE bot_settings SET value = ? WHERE key = ?', [String(value), key]);
    else await run('INSERT INTO bot_settings (key, value) VALUES (?, ?)', [key, String(value)]);
  });
  return String(value);
}

// ---------- Force Join ----------
async function getForceJoin() {
  return {
    enabled: (await getSetting('force_join_enabled', '0')) === '1',
    channelId: await getSetting('force_join_channel_id', ''),
    channelUrl: await getSetting('force_join_channel_url', ''),
    groupId: await getSetting('force_join_group_id', ''),
    groupUrl: await getSetting('force_join_group_url', ''),
  };
}

// ---------- Grup notifikasi transaksi ----------
async function getNotifGroup() {
  return getSetting('notif_group_id', '');
}

// ---------- Minimal topup agar otomatis jadi reseller ----------
async function getResellerMinTopup() {
  return Number(await getSetting('reseller_min_topup', '0')) || 0;
}

// ---------- Badge role ----------
const ROLE_BADGE = { admin: '👑', reseller: '🏪', member: '👤' };
const ROLE_LABEL = { admin: 'ADMIN', reseller: 'RESELLER', member: 'MEMBER' };
function roleBadge(role) {
  const r = String(role || 'member').toLowerCase();
  return `${ROLE_BADGE[r] || '👤'} ${ROLE_LABEL[r] || 'MEMBER'}`;
}

// ---------- Broadcast groups ----------
async function listBroadcastGroups() {
  return all('SELECT * FROM broadcast_groups ORDER BY id').catch(() => []);
}

async function addBroadcastGroup(chatId, title = '') {
  await run('INSERT OR IGNORE INTO broadcast_groups (chat_id, title) VALUES (?, ?)',
    [String(chatId), String(title || '')]);
}

async function delBroadcastGroup(id) {
  const r = await run('DELETE FROM broadcast_groups WHERE id = ?', [id]);
  return r.changes > 0;
}

module.exports = {
  getSetting, setSetting,
  getForceJoin, getNotifGroup, getResellerMinTopup,
  ROLE_BADGE, ROLE_LABEL, roleBadge,
  listBroadcastGroups, addBroadcastGroup, delBroadcastGroup,
};
