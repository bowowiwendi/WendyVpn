const axios = require('axios');
const crypto = require('crypto');

const config = require('./config');
const db = require('./db');

const BASE_URL = 'https://api.digiflazz.com/v1';

// ============================================================
// CONFIG DIGIFLAZZ
// Dibaca dari:
// .vars.json
//   ├── DIGIFLAZZ_USERNAME
//   └── DIGIFLAZZ_API_KEY
// ============================================================

const digiflazz = config.digiflazz || {};

const USERNAME = String(digiflazz.username || '').trim();
const API_KEY = String(digiflazz.apiKey || '').trim();


// ============================================================
// STATUS CONFIG
// ============================================================

function enabled() {
  return Boolean(USERNAME && API_KEY);
}


// ============================================================
// SIGNATURE
// MD5(username + apiKey + value)
// ============================================================

function sign(value) {
  return crypto
    .createHash('md5')
    .update(`${USERNAME}${API_KEY}${value}`)
    .digest('hex');
}


// ============================================================
// REQUEST DIGIFLAZZ
// ============================================================

async function post(endpoint, body) {
  try {
    const response = await axios.post(
      `${BASE_URL}${endpoint}`,
      body,
      {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );

    return response.data;

  } catch (error) {
    const apiError = error.response?.data;

    console.error(
      '❌ Digiflazz API Error:',
      apiError || error.message
    );

    throw new Error(
      apiError?.data?.message ||
      apiError?.message ||
      error.message ||
      'Request ke Digiflazz gagal'
    );
  }
}


// ============================================================
// PRICE LIST
// ============================================================

async function priceList(cmd) {
  if (!enabled()) {
    throw new Error(
      'DIGIFLAZZ_USERNAME / DIGIFLAZZ_API_KEY belum diisi di .vars.json'
    );
  }

  const result = await post(
    '/price-list',
    {
      cmd,
      username: USERNAME,
      sign: sign('pricelist')
    }
  );

  if (Array.isArray(result?.data)) {
    return result.data;
  }

  throw new Error(
    result?.data?.message ||
    result?.message ||
    `Pricelist ${cmd} gagal`
  );
}


// ============================================================
// SYNC PRODUK
// ============================================================

async function sync() {
  const old = db.products();

  const output = {
    ...old,
    lastSync: Date.now()
  };

  const [prepaid, pasca] = await Promise.allSettled([
    priceList('prepaid'),
    priceList('pasca')
  ]);

  const errors = [];

  // PREPAID
  if (prepaid.status === 'fulfilled') {
    output.list_prepaid = prepaid.value;
  } else {
    errors.push(
      `Prabayar: ${prepaid.reason?.message || 'Gagal sync'}`
    );
  }

  // PASCA
  if (pasca.status === 'fulfilled') {
    output.list_pasca = pasca.value;
  } else {
    errors.push(
      `Pascabayar: ${pasca.reason?.message || 'Gagal sync'}`
    );
  }

  db.saveProducts(output);

  if (
    prepaid.status === 'rejected' &&
    pasca.status === 'rejected'
  ) {
    throw new Error(errors.join('\n'));
  }

  return output;
}


// ============================================================
// CEK SALDO SUPPLIER
// ============================================================

async function balance() {
  if (!enabled()) {
    throw new Error(
      'DIGIFLAZZ_USERNAME / DIGIFLAZZ_API_KEY belum diisi di .vars.json'
    );
  }

  const result = await post(
    '/cek-saldo',
    {
      cmd: 'deposit',
      username: USERNAME,
      sign: sign('depo')
    }
  );

  if (result?.data) {
    return result.data;
  }

  throw new Error(
    result?.message ||
    'Gagal mengambil saldo supplier Digiflazz'
  );
}

async function balance() {
  if (!enabled()) {
    throw new Error(
      'DIGIFLAZZ_USERNAME / DIGIFLAZZ_API_KEY belum diisi di .vars.json'
    );
  }

  const signature = sign('depo');

  console.log('🔐 DIGIFLAZZ CEK SALDO');
  console.log('Username:', USERNAME);
  console.log('API Key length:', API_KEY.length);
  console.log('Signature:', signature);

  const result = await post('/cek-saldo', {
    cmd: 'deposit',
    username: USERNAME,
    sign: signature
  });

  if (result?.data) {
    return result.data;
  }

  throw new Error(
    result?.message ||
    'Gagal mengambil saldo supplier Digiflazz'
  );
}
// ============================================================
// TRANSAKSI
// ============================================================

async function transaction({
  sku,
  customerNo,
  refId,
  type = 'prepaid'
}) {
  if (!enabled()) {
    throw new Error(
      'DIGIFLAZZ_USERNAME / DIGIFLAZZ_API_KEY belum diisi di .vars.json'
    );
  }

  if (!sku) {
    throw new Error('SKU Digiflazz tidak boleh kosong');
  }

  if (!customerNo) {
    throw new Error('Nomor tujuan tidak boleh kosong');
  }

  if (!refId) {
    throw new Error('Ref ID transaksi tidak boleh kosong');
  }

  const result = await post(
    '/transaction',
    {
      username: USERNAME,
      buyer_sku_code: sku,
      customer_no: customerNo,
      ref_id: refId,
      sign: sign(refId)
    }
  );

  return result?.data;
}


// ============================================================
// CARI PRODUK
// ============================================================

function find(sku, type) {
  const products = db.products();

  const pools =
    type === 'prepaid'
      ? [products.list_prepaid]
      : type === 'pasca'
        ? [products.list_pasca]
        : [
            products.list_prepaid,
            products.list_pasca
          ];

  return pools
    .flat()
    .find(
      product =>
        String(product?.buyer_sku_code || '')
          .toLowerCase() ===
        String(sku || '').toLowerCase()
    ) || null;
}


// ============================================================
// HARGA DASAR
// ============================================================

function basePrice(product, type) {
  if (type === 'pasca') {
    return (
      Number(product?.price ?? product?.admin ?? 0) +
      Number(product?.commission ?? 0)
    );
  }

  return Number(product?.price || 0);
}


// ============================================================
// HARGA JUAL
// ============================================================

function sellPrice(product, role, type = 'prepaid') {
  const margin = Number(
    config.roles?.margin?.[role] ??
    config.roles?.margin?.bronze ??
    0
  );

  return Math.ceil(
    basePrice(product, type) *
    (1 + margin / 100)
  );
}


// ============================================================
// STATUS PRODUK
// ============================================================

function active(product) {
  return Boolean(
    product &&
    product.buyer_product_status === true
  );
}


// ============================================================
// KATEGORI
// ============================================================

function cats(type) {
  const products =
    type === 'prepaid'
      ? db.products().list_prepaid
      : db.products().list_pasca;

  const map = new Map();

  for (const product of products) {
    if (!active(product)) continue;

    const category = String(
      product.category || 'LAINNYA'
    );

    map.set(
      category,
      (map.get(category) || 0) + 1
    );
  }

  return [...map.entries()]
    .sort((a, b) =>
      a[0].localeCompare(b[0])
    );
}


// ============================================================
// BRAND
// ============================================================

function brands(type, category) {
  const products =
    type === 'prepaid'
      ? db.products().list_prepaid
      : db.products().list_pasca;

  const map = new Map();

  for (const product of products) {
    if (!active(product)) continue;

    if (
      String(product.category || '').toLowerCase() !==
      String(category || '').toLowerCase()
    ) {
      continue;
    }

    const brand = String(
      product.brand || 'LAINNYA'
    );

    map.set(
      brand,
      (map.get(brand) || 0) + 1
    );
  }

  return [...map.entries()]
    .sort((a, b) =>
      a[0].localeCompare(b[0])
    );
}


// ============================================================
// LIST PRODUK
// ============================================================

function list(type, category, brand) {
  const products =
    type === 'prepaid'
      ? db.products().list_prepaid
      : db.products().list_pasca;

  return products
    .filter(product => {
      if (!active(product)) {
        return false;
      }

      if (
        String(product.category || '').toLowerCase() !==
        String(category || '').toLowerCase()
      ) {
        return false;
      }

      if (
        brand &&
        String(product.brand || '').toLowerCase() !==
        String(brand || '').toLowerCase()
      ) {
        return false;
      }

      return true;
    })
    .sort(
      (a, b) =>
        basePrice(a, type) -
        basePrice(b, type)
    );
}


// ============================================================
// FORMAT INPUT TUJUAN
// ============================================================

function destinationSpec(category, brand) {
  const c = String(
    category || ''
  ).toLowerCase();

  const b = String(
    brand || ''
  ).toUpperCase();

  // GAME
  if (c === 'games') {
    if (/MOBILE\s*LEGEND/.test(b)) {
      return {
        tokens: 2,
        placeholder: 'ID ZoneID',
        label: 'ID + ZoneID'
      };
    }

    return {
      tokens: 1,
      placeholder: 'ID Game',
      label: 'ID Game'
    };
  }

  // PLN
  if (c === 'pln') {
    return {
      tokens: 1,
      placeholder: 'No Meter / ID Pelanggan',
      label: 'No Meter / ID Pelanggan'
    };
  }

  // TV / GAS
  if (
    ['tv', 'gas'].includes(c)
  ) {
    return {
      tokens: 1,
      placeholder: 'ID Pelanggan',
      label: 'ID Pelanggan'
    };
  }

  // NOMOR HP
  if (
    [
      'pulsa',
      'data',
      'masa aktif',
      'paket sms & telpon',
      'aktivasi perdana',
      'aktivasi voucher',
      'e-money',
      'voucher'
    ].includes(c)
  ) {
    return {
      tokens: 1,
      placeholder: '08xxxxxxxxxx',
      label: 'Nomor HP'
    };
  }

  // DEFAULT
  return {
    tokens: 1,
    placeholder: 'Nomor / ID Tujuan',
    label: 'Nomor / ID Tujuan'
  };
}


// ============================================================
// EXPORT
// ============================================================

const rp = n => "Rp" + Number(n||0).toLocaleString("id-ID");
module.exports = {
  enabled,
  sign,
  priceList,
  sync,
  balance,
  transaction,
  find,
  basePrice,
  sellPrice,
  cats,
  brands,
  list,
  destinationSpec,
  active,
  rp
};
