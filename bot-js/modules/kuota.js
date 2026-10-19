// ============================================================
// Modul Cek Kuota — via Sidompul API (format Aji/BotVPN2)
// ============================================================
const axios = require('axios');
const config = require('../src/config');
const { esc } = require('../src/format');

const SIDOMPUL_URL = 'https://apigw.kmsp-store.com/sidompul/v4/cek_kuota';

function stripHtml(html) {
  if (!html) return '';
  return String(html)
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]*>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .trim();
}

async function cekKuota(msisdn) {
  const apiKey = config.sidompul.apiKey;
  if (!apiKey) {
    return { success: false, message: '❌ <b>Cek Kuota</b>\nAPI belum dikonfigurasi.' };
  }
  const nomor = String(msisdn || '').replace(/\D/g, '');
  const bersih = nomor.startsWith('62') ? '0' + nomor.slice(2) : nomor;
  if (!/^08\d{8,13}$/.test(bersih)) {
    return { success: false, message: '❌ Format nomor salah.\nContoh: <code>083153170199</code>' };
  }
  try {
    const headers = {
      'Authorization': 'Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw',
      'X-API-Key': apiKey,
      'X-App-Version': '4.0.0',
    };
    const res = await axios.get(SIDOMPUL_URL, {
      params: { msisdn: bersih },
      headers: headers,
      timeout: 25000,
    });
    const data = res.data;
    const result = data && data.data ? data.data : data;
    let hasil = '';
    if (result && typeof result === 'object' && result.hasil) {
      hasil = stripHtml(result.hasil);
    } else if (typeof result === 'object') {
      const lines = [];
      for (const entry of Object.entries(result)) {
        const k = entry[0], v = entry[1];
        if (typeof v === 'string' || typeof v === 'number') {
          lines.push('- ' + k + ': ' + stripHtml(String(v)));
        }
      }
      hasil = lines.join('\n') || stripHtml(JSON.stringify(result)).slice(0, 1500);
    } else {
      hasil = stripHtml(String(result)).slice(0, 1500);
    }
    hasil = esc(hasil);
    return {
      success: true,
      message:
        `📡 <b>CEK KUOTA</b>\n` +
        `━━━━━━━━━━━━━━━━━━\n` +
        `📱 Nomor: <code>${bersih}</code>\n\n` +
        `<blockquote>${hasil}</blockquote>`,
    };
  } catch (e) {
    return { success: false, message: `❌ <b>Error:</b> ${esc(e.message)}` };
  }
}

module.exports = { cekKuota };
