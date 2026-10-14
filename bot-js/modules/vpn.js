// ============================================================
// Modul VPN — SSH / VMess / VLess / Trojan (+ mode CloudFront)
// Membuat akun via API server VPN, format output siap copy.
// ============================================================
const axios = require('axios');
const config = require('../src/config');
const { run, get, all } = require('../src/db');

const { apiBase, apiAuth, domain } = config.vpn;
const cf = config.cloudfront;

const api = axios.create({ baseURL: apiBase, timeout: 25000 });

function apiParams(extra = {}) {
  return { auth: apiAuth, ...extra };
}

const validUser = (u) => /^[a-zA-Z0-9]{3,20}$/.test(u || '');

function expiryDate(days) {
  const d = new Date();
  d.setDate(d.getDate() + Number(days));
  return d.toISOString().slice(0, 10);
}

// ---------- SSH ----------
async function createSSH(username, password, days, ipLimit = 1) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const { data } = await api.get('/createshh', {
    params: apiParams({ user: username, password, exp: days, iplimit: ipLimit }),
  });
  if (data?.status !== 'success') return { success: false, message: `❌ Gagal: ${data?.message || 'API error'}` };
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      `✅ <b>SSH Account</b>\n` +
      `👤 Username: <code>${username}</code>\n` +
      `🔑 Password: <code>${password}</code>\n` +
      `🌐 Host: <code>${domain}</code>\n` +
      `📅 Expired: <code>${exp}</code>`,
    expiry: exp,
  };
}

// ---------- SSH via CloudFront (/cf-ssh) ----------
function cfSSHInfo(username, password, days) {
  if (!cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset (.env CF_DOMAIN).' };
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const exp = expiryDate(days);
  const p = cf.paths.ssh;
  // Format untuk HTTP Custom / aplikasi SSH WS
  const message =
    `✅ <b>SSH via CloudFront</b>\n` +
    `👤 Username: <code>${username}</code>\n` +
    `🔑 Password: <code>${password}</code>\n` +
    `🌐 Host: <code>${cf.domain}</code>\n` +
    `🔌 Port: <code>443</code> (TLS)\n` +
    `🛣️ Path: <code>${p}</code>\n` +
    `📅 Expired: <code>${exp}</code>\n\n` +
    `<i>Payload HTTP Custom:</i>\n` +
    `<code>GET ${p} HTTP/1.1[crlf]Host: ${cf.domain}[crlf]Upgrade: websocket[crlf][crlf]</code>`;
  return { success: true, message, expiry: exp };
}

// ---------- VMess ----------
function vmessLink(uuid, remark, host, port, path, tls) {
  const obj = {
    v: '2', ps: remark, add: host, port: String(port),
    id: uuid, aid: '0', scy: 'auto', net: 'ws',
    type: 'none', host: host, path, tls: tls ? 'tls' : '',
    sni: tls ? host : '',
  };
  return 'vmess://' + Buffer.from(JSON.stringify(obj)).toString('base64');
}

async function createVMess(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const uuid = require('crypto').randomUUID();
  const { data } = await api.get('/createvmess', {
    params: apiParams({ user: username, uuid, exp: days }),
  }).catch(() => ({ data: {} }));
  // Jika API tidak support, tetap hasilkan link dari UUID lokal
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  const useUuid = viaCF ? cf.vmessUuid || uuid : uuid;
  const path = viaCF ? cf.paths.vmess : `/vmess-${username}`;
  const link = vmessLink(useUuid, `${username}-cf`, host, viaCF ? 443 : 443, path, true);
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      `✅ <b>VMess${viaCF ? ' via CloudFront' : ''}</b>\n` +
      `👤 Username: <code>${username}</code>\n` +
      `📅 Expired: <code>${exp}</code>\n\n` +
      `<code>${link}</code>`,
    expiry: exp, link,
  };
}

// ---------- VLess ----------
async function createVLess(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const uuid = require('crypto').randomUUID();
  await api.get('/createvless', { params: apiParams({ user: username, uuid, exp: days }) }).catch(() => {});
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  const useUuid = viaCF ? cf.vlessUuid || uuid : uuid;
  const path = encodeURIComponent(viaCF ? cf.paths.vless : `/vless-${username}`);
  const link = `vless://${useUuid}@${host}:443?encryption=none&security=tls&sni=${host}&type=ws&path=${path}#${username}${viaCF ? '-cf' : ''}`;
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      `✅ <b>VLess${viaCF ? ' via CloudFront' : ''}</b>\n` +
      `👤 Username: <code>${username}</code>\n` +
      `📅 Expired: <code>${exp}</code>\n\n` +
      `<code>${link}</code>`,
    expiry: exp, link,
  };
}

// ---------- Trojan ----------
async function createTrojan(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const password = require('crypto').randomUUID();
  await api.get('/createtrojan', { params: apiParams({ user: username, password, exp: days }) }).catch(() => {});
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  const usePass = viaCF ? cf.trojanPassword || password : password;
  const path = encodeURIComponent(viaCF ? cf.paths.trojan : `/trojan-${username}`);
  const link = `trojan://${usePass}@${host}:443?security=tls&sni=${host}&type=ws&path=${path}#${username}${viaCF ? '-cf' : ''}`;
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      `✅ <b>Trojan${viaCF ? ' via CloudFront' : ''}</b>\n` +
      `👤 Username: <code>${username}</code>\n` +
      `📅 Expired: <code>${exp}</code>\n\n` +
      `<code>${link}</code>`,
    expiry: exp, link,
  };
}

// ---------- Renew / Delete (via API server) ----------
async function renewAccount(proto, username, days) {
  const { data } = await api.get('/renew', {
    params: apiParams({ proto, user: username, exp: days }),
  }).catch(() => ({ data: {} }));
  if (data?.status === 'success') {
    await run('UPDATE vpn_accounts SET expiry = ? WHERE username = ? AND proto = ?', [expiryDate(days), username, proto]);
    return { success: true, message: `✅ <b>${username}</b> diperpanjang ${days} hari.` };
  }
  return { success: false, message: `❌ Gagal renew: ${data?.message || 'API error'}` };
}

async function deleteAccount(proto, username) {
  await api.get('/delete', { params: apiParams({ proto, user: username }) }).catch(() => {});
  await run('DELETE FROM vpn_accounts WHERE username = ? AND proto = ?', [username, proto]);
  return { success: true, message: `🗑️ Akun <b>${username}</b> (${proto}) dihapus.` };
}

async function saveAccount(telegramId, proto, username, expiry, isTrial = 0, viaCF = 0) {
  await run(
    'INSERT INTO vpn_accounts (telegram_id, proto, username, expiry, is_trial, via_cf) VALUES (?,?,?,?,?,?)',
    [telegramId, proto, username, expiry, isTrial, viaCF]
  );
}

async function myAccounts(telegramId) {
  return all('SELECT * FROM vpn_accounts WHERE telegram_id = ? ORDER BY id DESC', [telegramId]);
}

module.exports = {
  createSSH, cfSSHInfo, createVMess, createVLess, createTrojan,
  renewAccount, deleteAccount, saveAccount, myAccounts, validUser, expiryDate,
};
