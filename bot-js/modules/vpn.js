// ============================================================
// Modul VPN — SSH / VMess / VLess / Trojan (+ mode CloudFront)
// Membuat akun via API server VPN, format output siap copy.
// ============================================================
const axios = require('axios');
const config = require('../src/config');
const { run, get, all } = require('../src/db');
const { esc } = require('../src/format');

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

// ---------- Format tampilan kotak (fancy) hasil pembuatan akun ----------
// Port yang ditampilkan hanya yang terverifikasi sebagai layanan VPN:
// TLS 443, HTTP 80, OpenSSH 22, Dropbear 109/143. Port contoh lain
// (8443, 8080, 2086, 8880, UDPSSH 1-65535, DNS 53, BadVPN 7300) sengaja
// TIDAK ditampilkan: 8443 tidak mendengarkan di Aji02, 53/7300 hanya
// localhost, dan servis 8080/2086/8880 tidak terverifikasi sebagai
// layanan VPN. Save-account TIDAK ditampilkan: API bot tidak menulis
// file /var/www/html/*.txt (file itu hanya ditulis menu server), jadi
// link :81 akan mati (404) untuk akun buatan bot.
const FANCY_TOP = '╭━━━━━━━━━━━━━━━━━━━━━━╮';
const FANCY_BOT = '╰━━━━━━━━━━━━━━━━━━━━━━╯';
const FANCY_SEP = '━━━━━━━━━━━━━━━━━━━━━━';
const FANCY_TITLES = {
  ssh: '🚀 ꜱꜱʜ ᴀᴄᴄᴏᴜɴᴛ',
  vmess: '🚀 ᴠᴍᴇꜱꜱ ᴀᴄᴄᴏᴜɴᴛ',
  vless: '🚀 ᴠʟᴇꜱꜱ ᴀᴄᴄᴏᴜɴᴛ',
  trojan: '🚀 ᴛʀᴏᴊᴀɴ ᴀᴄᴄᴏᴜɴᴛ',
};

function fancyBox(d) {
  const lines = [];
  lines.push(FANCY_TOP);
  lines.push((FANCY_TITLES[d.proto] || '🚀 ᴀᴄᴄᴏᴜɴᴛ') + (d.viaCF ? ' ☁️' : ''));
  lines.push(FANCY_BOT);
  lines.push('');
  const info = [
    '┌〔 📄 ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ 〕',
    `├ 👤 Username : <code>${esc(d.username)}</code>`,
    `├ ${d.secretIcon} ${d.secretLabel} : <code>${esc(d.secret)}</code>`,
    `├ 📅 Expired : <code>${esc(d.exp)}</code>`,
  ];
  if (d.proto === 'ssh') info.push(`├ 🌐 IP Limit : ${d.ipLimit} IP`);
  info.push('└ 🟢 Status : ACTIVE');
  lines.push(info.join('\n'));
  lines.push('');
  lines.push(FANCY_SEP);
  lines.push('');
  const srv = [
    '┌〔 🌍 ꜱᴇʀᴠᴇʀ 〕',
    `├ 🌐 Domain : <code>${esc(d.origin)}</code>`,
  ];
  if (d.cfDomain) srv.push(`└ ☁️ CloudFront : <code>${esc(d.cfDomain)}</code>`);
  else srv[srv.length - 1] = srv[srv.length - 1].replace('├', '└');
  lines.push(srv.join('\n'));
  lines.push('');
  lines.push(FANCY_SEP);
  lines.push('');
  if (d.proto === 'ssh') {
    const ports = d.viaCF
      ? ['┌〔 🔌 ᴘᴏʀᴛ 〕', '└ 🔐 TLS : 443']
      : ['┌〔 🔌 ᴘᴏʀᴛ 〕', '├ 🔐 TLS : 443', '├ 🌐 HTTP : 80', '├ ⚡ OpenSSH : 22', '└ 📡 Dropbear : 109, 143'];
    lines.push(ports.join('\n'));
    lines.push('');
    lines.push(FANCY_SEP);
    lines.push('');
    lines.push('📡 ʜᴛᴛᴘ ᴄᴜꜱᴛᴏᴍ');
    lines.push('');
    for (const hc of d.httpCustom) lines.push(`<code>${esc(hc.host)}:${hc.port}@${esc(hc.user)}:${esc(hc.pass)}</code>\n`);
    lines.push(FANCY_SEP);
    lines.push('');
    lines.push('📄 ᴘᴀʏʟᴏᴀᴅ');
    lines.push('');
    lines.push(`<code>${d.payload}</code>`);
  } else {
    lines.push('┌〔 🔌 ᴘᴏʀᴛ 〕');
    lines.push('└ 🔐 TLS : 443');
    lines.push('');
    lines.push(FANCY_SEP);
    lines.push('');
    lines.push('🔗 ʟɪɴᴋ');
    lines.push('');
    lines.push(`<code>${d.link}</code>`);
    lines.push('');
    lines.push(FANCY_SEP);
    lines.push('');
    lines.push('┌〔 🌐 ᴡꜱ ᴅᴇᴛᴀɪʟ 〕');
    lines.push(`├ 🌐 Host : <code>${esc(d.host)}</code>`);
    lines.push('├ 🔐 Port TLS : 443');
    lines.push(`├ 🛣️ Path : <code>${esc(d.wsPath)}</code>`);
    lines.push(`└ 🔑 SNI : <code>${esc(d.host)}</code>`);
  }
  lines.push('');
  lines.push(FANCY_SEP);
  lines.push('');
  lines.push('🎉 ᴀᴋᴜɴ ʙᴇʀʜᴀꜱɪʟ ᴅɪʙᴜᴀᴛ');
  lines.push('');
  lines.push('🤝 ᴛᴇʀɪᴍᴀ ᴋᴀꜱɪʜ');
  lines.push('ꜱᴇʟᴀᴍᴀᴛ ᴍᴇɴɢɢᴜɴᴀᴋᴀɴ');
  lines.push('ʟᴀʏᴀɴᴀɴ ᴋᴀᴍɪ. ❤️');
  return lines.join('\n');
}


// ---------- SSH ----------
async function createSSH(username, password, days, ipLimit = 1) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const { data } = await api.get('/createshh', {
    params: apiParams({ user: username, password, exp: days, iplimit: ipLimit }),
  });
  if (data?.status !== 'success') return { success: false, message: `❌ Gagal: ${esc(data?.message || 'API error')}` };
  const exp = expiryDate(days);
  return {
    success: true,
    message: fancyBox({ proto: 'ssh', viaCF: false, username, secretIcon: '🔑', secretLabel: 'Password', secret: password, exp, ipLimit, origin: domain, host: domain, cfDomain: cf.domain || '', httpCustom: [{ host: domain, port: 80, user: username, pass: password }, { host: domain, port: 443, user: username, pass: password }], payload: `GET wss://[host]/ HTTP/1.1[crlf]Host: ${domain}[crlf]Upgrade: websocket[crlf][crlf]` }),
    expiry: exp,
    password,
  };
}

// ---------- SSH via CloudFront (/cf-ssh) ----------
function cfSSHInfo(username, password, days) {
  if (!cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset (.env CF_DOMAIN).' };
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const exp = expiryDate(days);
  const p = cf.paths.ssh;
  // Format untuk HTTP Custom / aplikasi SSH WS
  const message = fancyBox({ proto: 'ssh', viaCF: true, username, secretIcon: '🔑', secretLabel: 'Password', secret: password, exp, ipLimit: 1, origin: domain, host: cf.domain, cfDomain: cf.domain || '', httpCustom: [{ host: cf.domain, port: 443, user: username, pass: password }], payload: `GET ${p} HTTP/1.1[crlf]Host: ${cf.domain}[crlf]Upgrade: websocket[crlf][crlf]` });
  return { success: true, message, expiry: exp, password };
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
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  // Mode CF memakai UUID CF yang sudah terdaftar — aman lanjut walau API gagal.
  // Mode biasa: akun harus terdaftar di server; gagal API = gagal jujur (jangan kasih link mati).
  if (!viaCF && data?.status !== 'success')
    return { success: false, message: `❌ Gagal membuat akun: ${esc(data?.message || 'API error')}` };
  const useUuid = viaCF ? cf.vmessUuid || uuid : uuid;
  const path = viaCF ? cf.paths.vmess : `/vmess-${username}`;
  const link = vmessLink(useUuid, `${username}-cf`, host, viaCF ? 443 : 443, path, true);
  const exp = expiryDate(days);
  return {
    success: true,
    message: fancyBox({ proto: 'vmess', viaCF, username, secretIcon: '🆔', secretLabel: 'UUID', secret: useUuid, exp, origin: domain, host, cfDomain: cf.domain || '', link, wsPath: path }),
    expiry: exp, link, uuid: useUuid,
  };
}

// ---------- VLess ----------
async function createVLess(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const uuid = require('crypto').randomUUID();
  const { data: dataVL } = await api.get('/createvless', { params: apiParams({ user: username, uuid, exp: days }) }).catch(() => ({ data: {} }));
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  if (!viaCF && dataVL?.status !== 'success')
    return { success: false, message: `❌ Gagal membuat akun: ${esc(dataVL?.message || 'API error')}` };
  const useUuid = viaCF ? cf.vlessUuid || uuid : uuid;
  const path = encodeURIComponent(viaCF ? cf.paths.vless : `/vless-${username}`);
  const link = `vless://${useUuid}@${host}:443?encryption=none&security=tls&sni=${host}&type=ws&path=${path}#${username}${viaCF ? '-cf' : ''}`;
  const exp = expiryDate(days);
  return {
    success: true,
    message: fancyBox({ proto: 'vless', viaCF, username, secretIcon: '🆔', secretLabel: 'UUID', secret: useUuid, exp, origin: domain, host, cfDomain: cf.domain || '', link, wsPath: viaCF ? cf.paths.vless : `/vless-${username}` }),
    expiry: exp, link, uuid: useUuid,
  };
}

// ---------- Trojan ----------
async function createTrojan(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '❌ Username 3-20 karakter, huruf/angka saja.' };
  const password = require('crypto').randomUUID();
  const { data: dataTR } = await api.get('/createtrojan', { params: apiParams({ user: username, password, exp: days }) }).catch(() => ({ data: {} }));
  const host = viaCF ? cf.domain : domain;
  if (viaCF && !cf.domain) return { success: false, message: '❌ Domain CloudFront belum diset.' };
  if (!viaCF && dataTR?.status !== 'success')
    return { success: false, message: `❌ Gagal membuat akun: ${esc(dataTR?.message || 'API error')}` };
  const usePass = viaCF ? cf.trojanPassword || password : password;
  const path = encodeURIComponent(viaCF ? cf.paths.trojan : `/trojan-${username}`);
  const link = `trojan://${usePass}@${host}:443?security=tls&sni=${host}&type=ws&path=${path}#${username}${viaCF ? '-cf' : ''}`;
  const exp = expiryDate(days);
  return {
    success: true,
    message: fancyBox({ proto: 'trojan', viaCF, username, secretIcon: '🔑', secretLabel: 'Password', secret: usePass, exp, origin: domain, host, cfDomain: cf.domain || '', link, wsPath: viaCF ? cf.paths.trojan : `/trojan-${username}` }),
    expiry: exp, link, password: usePass,
  };
}

// ---------- Shadowsocks ----------
function ssLink(method, password, host, port, remark) {
  const userinfo = Buffer.from(`${method}:${password}`).toString('base64');
  return `ss://${userinfo}@${host}:${port}#${encodeURIComponent(remark)}`;
}

async function createShadowsocks(username, days, viaCF = false) {
  if (!validUser(username)) return { success: false, message: '\u274c Username 3-20 karakter, huruf/angka saja.' };
  const password = require('crypto').randomUUID();
  const method = 'aes-256-gcm';
  const { data: dataSS } = await api.get('/createss', { params: apiParams({ user: username, password, exp: days }) }).catch(() => ({ data: {} }));
  const host = viaCF ? cf.domain : domain;
  if (!viaCF && dataSS?.status !== 'success')
    return { success: false, message: `❌ Gagal membuat akun: ${esc(dataSS?.message || 'API error')}` };
  if (viaCF && !cf.domain) return { success: false, message: '\u274c Domain CloudFront belum diset.' };
  const port = 443;
  const link = ssLink(method, password, host, port, `${username}${viaCF ? '-cf' : ''}`);
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      `\u2705 <b>Shadowsocks${viaCF ? ' via CloudFront' : ''}</b>\n<blockquote>` +
      `👤 Username: <code>${username}</code>\n` +
      `🔑 Password: <code>${password}</code>\n` +
      `🔐 Method: <code>${method}</code>\n` +
      `🌍 Host: <code>${host}</code>\n` +
      `🔌 Port: <code>${port}</code>\n` +
      `📅 Expired: <code>${exp}</code></blockquote>\n\n` +
      `<code>${link}</code>`,
    expiry: exp, link, password,
  };
}

// ---------- Renew / Delete (via API server) ----------
async function renewAccount(proto, username, days) {
  const { data } = await api.get('/renew', {
    params: apiParams({ proto, user: username, exp: days }),
  }).catch(() => ({ data: {} }));
  if (data?.status === 'success') {
    // Perpanjang dari expiry saat ini (bila masih aktif), bukan dari hari ini —
    // user tidak kehilangan sisa masa aktif yang sudah dibayar.
    const today = new Date().toISOString().slice(0, 10);
    const row = await get('SELECT expiry FROM vpn_accounts WHERE username = ? AND proto = ?', [username, proto]).catch(() => null);
    const base = (row?.expiry && row.expiry > today) ? row.expiry : today;
    const d = new Date(base + 'T00:00:00');
    d.setDate(d.getDate() + Number(days));
    const newExp = d.toISOString().slice(0, 10);
    await run('UPDATE vpn_accounts SET expiry = ? WHERE username = ? AND proto = ?', [newExp, username, proto]);
    return { success: true, message: `✅ <b>${username}</b> diperpanjang ${days} hari (s/d <code>${newExp}</code>).` };
  }
  return { success: false, message: `❌ Gagal renew: ${esc(data?.message || 'API error')}` };
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


async function createZivpn(username, password, days) {
  if (!validUser(username)) return { success: false, message: 'Username 3-20 karakter, huruf/angka saja.' };
  try {
    await api.get('/createzivpn', { params: apiParams({ user: username, password, exp: days }) });
  } catch(e) {}
  const host = domain;
  const port = 5667;
  const exp = expiryDate(days);
  return {
    success: true,
    message:
      'Zivpn UDP<br><blockquote>' +
      'Username: <code>' + username + '</code><br>' +
      'Password: <code>' + password + '</code><br>' +
      'Host: <code>' + host + '</code><br>' +
      'Port UDP: <code>' + port + '</code><br>' +
      'Expired: <code>' + exp + '</code></blockquote>',
    expiry: exp,
  };
}

// ---------- Harga VPN per role (diatur admin, Rp/hari) ----------
// product_key = jenis akun VPN. Harga disimpan di tabel vpn_prices
// (kolom: product_key, role, price). Role 'admin' selalu harga 0 (modal).
const VPN_PRODUCTS = [
  { key: 'ssh', label: 'SSH' },
  { key: 'vmess', label: 'VMess' },
  { key: 'vless', label: 'VLess' },
  { key: 'trojan', label: 'Trojan' },
  { key: 'shadowsocks', label: 'Shadowsocks' },
  { key: 'zivpn', label: 'Zivpn UDP' },
];
// Default awal (meniru perilaku lama: Rp500/hari, reseller diskon 10%)
const DEFAULT_VPN_PRICE = { member: 500, reseller: 450 };

async function seedVpnPrices() {
  // Migrasi harga CF: kolom cf_price (NULL = fallback ke harga biasa).
  await run('ALTER TABLE vpn_prices ADD COLUMN cf_price INTEGER').catch(() => {});
  for (const p of VPN_PRODUCTS) {
    for (const role of ['member', 'reseller']) {
      await run(
        'INSERT OR IGNORE INTO vpn_prices (product_key, role, price) VALUES (?,?,?)',
        [p.key, role, DEFAULT_VPN_PRICE[role]]
      ).catch(() => {});
    }
  }
}

async function getVpnPrice(productKey, role, viaCF = false) {
  if (role === 'admin') return 0; // harga modal untuk admin
  const row = await get(
    'SELECT price, cf_price FROM vpn_prices WHERE product_key = ? AND role = ?',
    [productKey, role]
  ).catch(() => null);
  const isNum = (v) => v !== null && v !== undefined && v !== '' && Number.isFinite(Number(v));
  const biasa = (row && isNum(row.price))
    ? Number(row.price) : (DEFAULT_VPN_PRICE[role] ?? DEFAULT_VPN_PRICE.member);
  // Harga CF: pakai cf_price bila terisi; bila NULL/belum diset, fallback ke harga biasa.
  // (Number(null) = 0, jadi NULL harus dicek eksplisit, bukan via Number.isFinite saja.)
  if (viaCF && row && isNum(row.cf_price)) return Number(row.cf_price);
  return biasa;
}

async function setVpnPrice(productKey, role, price, viaCF = false) {
  if (!VPN_PRODUCTS.some((p) => p.key === productKey)) {
    throw new Error('Produk tidak dikenal: ' + productKey);
  }
  if (!['member', 'reseller'].includes(role)) {
    throw new Error('Harga hanya bisa diatur untuk role member/reseller (admin = 0)');
  }
  price = Math.round(Number(price));
  if (!Number.isFinite(price) || price < 0) throw new Error('Harga tidak valid (angka ≥ 0)');
  // Pastikan baris ada (harga biasa = default bila baru), lalu ubah HANYA kolom yang dipilih,
  // supaya harga Biasa dan CF tidak saling menimpa.
  await run(
    'INSERT OR IGNORE INTO vpn_prices (product_key, role, price) VALUES (?,?,?)',
    [productKey, role, DEFAULT_VPN_PRICE[role] ?? DEFAULT_VPN_PRICE.member]
  ).catch(() => {});
  const col = viaCF ? 'cf_price' : 'price';
  await run(
    `UPDATE vpn_prices SET ${col} = ? WHERE product_key = ? AND role = ?`,
    [price, productKey, role]
  );
  return price;
}

async function listVpnPrices() {
  return all('SELECT product_key, role, price, cf_price FROM vpn_prices ORDER BY product_key, role')
    .catch(() => all('SELECT product_key, role, price FROM vpn_prices ORDER BY product_key, role'));
}

module.exports = {
  createSSH, cfSSHInfo, createVMess, createVLess, createTrojan, createShadowsocks, createZivpn, fancyBox,
  renewAccount, deleteAccount, saveAccount, myAccounts, validUser, expiryDate,
  VPN_PRODUCTS, DEFAULT_VPN_PRICE, seedVpnPrices, getVpnPrice, setVpnPrice, listVpnPrices,
};
