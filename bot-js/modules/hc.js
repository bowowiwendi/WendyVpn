// ============================================================
// Modul HC — Generate file .hc (HTTP Custom) via ePro API
// Preset: 'default' | 'xl_edukasi'
// ============================================================
const axios = require('axios');
const crypto = require('crypto');
const config = require('../src/config');

const EPRO_API = 'https://api.eprodev.org/v1/configs/hc';

// Path WebSocket per service (sesuai vpnstore)
const HC_PATHS = {
  vmess: '/vmess',
  vless: '/vless',
  trojan: '/trojan-ws',
};

// Preset payload SSH (disalin dari /opt/vpnstore/app.py DEFAULT_HC_PRESETS)
const HC_PRESETS = {
  default: {
    label: 'Default',
    payload: 'GET / HTTP/1.1[crlf]Host: edu.ruangguru.com[crlf][crlf]' +
      'PATCH / HTTP/1.1[crlf]Host: [host][crlf]Upgrade: websocket[crlf][crlf]',
    remote_proxy: '',
    methods: ['payload', 'tls'],
    sni: 'edu.ruangguru.com',
    ssh_port: 443,
  },
  xl_edukasi: {
    label: 'XL EDUKASI',
    payload: 'GET / HTTP/1.1[crlf]Host: bimbel.ruangguru.com[crlf][crlf]' +
      'PATCH / HTTP/1.1[crlf]Host: [host][crlf]Upgrade: websocket[crlf][crlf]' +
      '[split]HTTP/ 69[crlf][crlf]',
    remote_proxy: '104.17.3.81:80',
    methods: ['payload'],
    sni: '',
    ssh_port: 443,
  },
};

function hcEnabled() {
  return !!(config.hcApiKey);
}

function presetList() {
  return Object.keys(HC_PRESETS).map((id) => ({ id, label: HC_PRESETS[id].label }));
}

async function generateHC(opts) {
  const service = opts.service;
  const username = opts.username;
  const uuid = opts.uuid;
  const password = opts.password;
  const domain = opts.domain;
  const presetId = HC_PRESETS[opts.preset] ? opts.preset : 'default';
  const preset = HC_PRESETS[presetId];

  const apiKey = config.hcApiKey;
  if (!apiKey) return { success: false, message: 'HC API belum dikonfigurasi.' };
  if (['vmess', 'vless', 'trojan', 'ssh'].indexOf(service) === -1) {
    return { success: false, message: 'Service tidak didukung untuk .hc.' };
  }

  const fileBase = ('wendyvpn-' + presetId + '-' + username).toLowerCase().replace(/[^a-z0-9_-]/g, '');
  let mainConnections = {};
  let profiles = [];

  if (service === 'ssh') {
    if (!password) return { success: false, message: 'Password SSH dibutuhkan.' };
    const payloadObj = {
      enabled_methods: preset.methods,
      custom_payload: preset.payload,
    };
    if (preset.remote_proxy) payloadObj.remote_proxy = preset.remote_proxy;
    if (payloadObj.enabled_methods.indexOf('tls') !== -1 && preset.sni) {
      payloadObj.tls = { sni: preset.sni, version: 'tls_1_3' };
    }
    mainConnections = {
      ssh: {
        payload: payloadObj,
        account: {
          server_host: domain,
          server_port: preset.ssh_port,
          username: username,
          password: password,
        },
      },
    };
  } else {
    const cred = uuid || password;
    if (!cred) return { success: false, message: 'UUID/password tidak ditemukan.' };
    const manual = {
      server_type: service,
      server_host: domain,
      server_port: 443,
      transport: 'websocket',
      transport_path: HC_PATHS[service] || '/',
      transport_host: domain,
      tls_mode: 'tls',
      sni: domain,
      allow_insecure: false,
    };
    if (service === 'vmess' || service === 'vless') {
      manual.uuid = cred;
    } else {
      manual.password = cred;
    }
    profiles = [{
      profile_name: 'WENDYVPN ' + service.toUpperCase() + ' ' + username,
      manual: manual,
    }];
  }

  const reqBody = {
    file_name: fileBase,
    powered_by: 'WENDYVPN',
    main_connections: mainConnections,
    profiles: profiles,
    protection: { content_access: 'lock_all' },
    password: '',
  };

  try {
    const resp = await axios.post(EPRO_API, reqBody, {
      headers: {
        'Authorization': 'Bearer ' + apiKey,
        'Content-Type': 'application/json',
        'Idempotency-Key': 'wendyvpn-tg-' + presetId + '-' + username + '-' + Date.now(),
      },
      timeout: 60000,
    });
    const data = resp.data;
    if (resp.status !== 201 || !data || !data.content_base64) {
      return { success: false, message: 'Gagal generate .hc dari API.' };
    }
    const buf = Buffer.from(data.content_base64, 'base64');
    const hash = crypto.createHash('sha256').update(buf).digest('hex');
    if (data.sha256 && hash !== data.sha256) {
      return { success: false, message: 'Checksum .hc tidak cocok.' };
    }
    return { success: true, buffer: buf, filename: fileBase + '.hc', preset: presetId };
  } catch (e) {
    return { success: false, message: 'Error API HC: ' + e.message };
  }
}

module.exports = { hcEnabled, generateHC, presetList, HC_PRESETS };
