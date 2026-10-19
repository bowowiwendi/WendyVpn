const axios = require('axios');
const crypto = require('crypto');

const config = require('./config');


// =========================================================
// AUTHENTICATION
// =========================================================

function authHeaders(
  method,
  path,
  body = ''
) {

  const headers = {
    'X-API-Key': config.austin.apiKey
  };

  if (body) {
    headers['Content-Type'] =
      'application/json';
  }

  if (config.austin.apiSecret) {

    const timestamp =
      Date.now().toString();

    const signature =
      crypto
        .createHmac(
          'sha256',
          config.austin.apiSecret
        )
        .update(
          `${method}\n${path}\n${body}\n${timestamp}`
        )
        .digest('hex');

    headers['X-Timestamp'] =
      timestamp;

    headers['X-Signature'] =
      signature;
  }

  return headers;
}


// =========================================================
// CREATE DEPOSIT / QRIS
// =========================================================

async function create(amount) {

  if (!config.austin.apiKey) {
    throw new Error(
      'AUSTIN_API_KEY belum diisi'
    );
  }

  const path =
    '/api/deposit/create';

  const body = JSON.stringify({
    amount: Number(amount)
  });

  const response =
    await axios.post(
      `${config.austin.baseUrl}${path}`,
      body,
      {
        headers: {
          ...authHeaders(
            'POST',
            path,
            body
          ),

          'Content-Type':
            'application/json'
        },

        timeout: 30000
      }
    );

  if (
    !response.data?.success ||
    !response.data?.deposit
  ) {
    throw new Error(
      response.data?.message ||
      'Gagal membuat QRIS AustinPay'
    );
  }

  const deposit =
    response.data.deposit;

  return {
    depositId:
      deposit.transaction_id ||
      deposit.id,

    id:
      deposit.transaction_id ||
      deposit.id,

    amount:
      deposit.amount,

    totalAmount:
      deposit.amount,

    uniqueCode:
      deposit.unique_code || 0,

    qrImage:
      deposit.qr_image || null,

    expiredAt:
      deposit.expired_at || null,

    status:
      deposit.status
  };
}


// =========================================================
// CHECK DEPOSIT STATUS
// =========================================================

async function status(id) {

  if (!config.austin.apiKey) {
    throw new Error(
      'AUSTIN_API_KEY belum diisi'
    );
  }

  const path =
    `/api/deposit/check/${encodeURIComponent(id)}`;

  const response =
    await axios.get(
      `${config.austin.baseUrl}${path}`,
      {
        headers:
          authHeaders(
            'GET',
            path,
            ''
          ),

        timeout: 30000
      }
    );

  return response.data;
}


// =========================================================
// CHECK PAYMENT STATUS
// =========================================================

function paid(data) {

  const layers = [
    data,
    data?.data,
    data?.transaction,
    data?.payment,
    data?.result
  ];

  const successStatuses = [
    'success',
    'paid',
    'settlement',
    'settled',
    'completed',
    'complete',
    'done',
    'sukses',
    'berhasil',
    'lunas',
    'capture',
    'accepted',
    'confirmed',
    'terbayar',
    '1',
    'true'
  ];

  for (const layer of layers) {

    if (
      !layer ||
      typeof layer !== 'object'
    ) {
      continue;
    }

    // Boolean / numeric payment flags
    if (
      layer.paid === true ||
      layer.isPaid === true ||
      layer.is_paid === true ||
      layer.paid === 1 ||
      layer.paid === '1'
    ) {
      return true;
    }

    // Status fields
    const statusFields = [
      'status',
      'paymentStatus',
      'payment_status',
      'transactionStatus',
      'transaction_status',
      'settlementStatus',
      'settlement_status',
      'statusCode',
      'status_code'
    ];

    for (const key of statusFields) {

      const value = String(
        layer[key] ?? ''
      )
        .toLowerCase()
        .trim();

      if (
        successStatuses.includes(value)
      ) {
        return true;
      }
    }
  }

  return false;
}


// =========================================================
// EXPORTS
// =========================================================

module.exports = {
  create,
  status,
  paid
};