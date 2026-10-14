// ============================================================
// Digiflazz API — cek harga & transaksi PPOB
// Signature: md5(username + apiKey + refId)
// ============================================================
const axios = require('axios');
const crypto = require('crypto');
const config = require('./config');

const BASE_URL = 'https://api.digiflazz.com/v1';
const { username: USERNAME, apiKey: API_KEY, margin: MARGIN } = config.digiflazz;

const enabled = () => Boolean(USERNAME && API_KEY);

const sign = (value) =>
  crypto.createHash('md5').update(`${USERNAME}${API_KEY}${value}`).digest('hex');

async function post(endpoint, body) {
  const { data } = await axios.post(`${BASE_URL}${endpoint}`, body, { timeout: 20000 });
  return data;
}

// Daftar harga produk (filter opsional: category / brand / type)
async function priceList(cmd, { category, brand, type } = {}) {
  const refId = `pricelist-${Date.now()}`;
  const body = {
    cmd,
    username: USERNAME,
    sign: sign(refId),
  };
  if (category) body.category = category;
  if (brand) body.brand = brand;
  if (type) body.type = type;
  const res = await post('', body);
  // Tambah margin ke harga jual
  if (Array.isArray(res?.data)) {
    for (const p of res.data) {
      p.price_sell = (p.price || 0) + MARGIN;
    }
  }
  return res;
}

// Buat transaksi
async function transaction(buyerSkuCode, customerNo, refId) {
  return post('', {
    username: USERNAME,
    buyer_sku_code: buyerSkuCode,
    customer_no: customerNo,
    ref_id: refId,
    sign: sign(refId),
  });
}

// Cek status transaksi by ref_id (untuk polling status pending)
async function checkTransaction(refId) {
  return post('', {
    username: USERNAME,
    ref_id: refId,
    sign: sign(refId),
  });
}

const rp = (n) => 'Rp' + Number(n || 0).toLocaleString('id-ID');

module.exports = { enabled, priceList, transaction, checkTransaction, rp };
