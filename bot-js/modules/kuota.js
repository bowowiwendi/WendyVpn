// ============================================================
// Modul Cek Kuota — via Sidompul API
// ============================================================
const axios = require('axios');
const config = require('../src/config');

async function cekKuota(msisdn) {
  const apiKey = config.sidompul.apiKey;
  if (!apiKey) return { success: false, message: '❌ API cek kuota belum dikonfigurasi.' };
  const nomor = String(msisdn || '').replace(/\D/g, '');
  if (!/^08\d{8,13}$/.test(nomor)) {
    return { success: false, message: '❌ Format nomor salah. Contoh: 083153170199' };
  }
  try {
    const { data } = await axios.get('https://api.sidompul.com/cek-kuota', {
      params: { api_key: apiKey, msisdn: nomor },
      timeout: 25000,
    });
    if (!data?.success && !data?.data) {
      return { success: false, message: `❌ ${data?.message || 'Gagal cek kuota.'}` };
    }
    const hasil = data.data?.hasil || data.hasil || JSON.stringify(data.data).slice(0, 1500);
    return { success: true, message: `📡 <b>Cek Kuota ${nomor}</b>\n\n${hasil}` };
  } catch (e) {
    return { success: false, message: `❌ Error: ${e.message}` };
  }
}

module.exports = { cekKuota };
