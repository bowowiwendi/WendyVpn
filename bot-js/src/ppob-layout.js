// ============================================================
// PPOB — LAYOUT MENU KATEGORI + LABEL MAPPING
// ============================================================
// Telegram tidak menyediakan ukuran button dalam pixel.
// Jumlah kolom mengatur ukuran visual button.
// 2 = dua button kecil/sedang per baris.
// ============================================================
module.exports = {
  CATEGORY_COLUMNS: 2,

  // Nama kategori dari Digiflazz → label tombol yang rapi.
  // Jumlah produk sengaja tidak ditampilkan di tombol.
  LABELS: {
    // Data / Kuota
    Data: 'Kuota',
    DATA: 'Kuota',
    data: 'Kuota',
    'Paket Data': 'Kuota',
    'paket data': 'Kuota',
    Internet: 'Kuota',
    // Game
    Games: 'Game',
    Game: 'Game',
    games: 'Game',
    game: 'Game',
    'Voucher Game': 'Game',
    // Perdana
    'Aktivasi Perdana': 'Perdana',
    Perdana: 'Perdana',
    perdana: 'Perdana',
    // Voucher
    'Aktivasi Voucher': 'Voucher',
    Voucher: 'Voucher',
    voucher: 'Voucher',
    // SMS & Telp
    'Paket SMS & Telpon': 'SMS & Telp',
    'Paket SMS & Telepon': 'SMS & Telp',
    SMS: 'SMS & Telp',
    // Masa Aktif
    'Masa Aktif': 'Masa Aktif',
    'MasaAktif': 'Masa Aktif',
    // E-Money
    'E-Money': 'E-Money',
    'E-money': 'E-Money',
    'e-money': 'E-Money',
    Emoney: 'E-Money',
    // PLN
    PLN: 'PLN',
    Pln: 'PLN',
    pln: 'PLN',
    // Pulsa
    Pulsa: 'Pulsa',
    pulsa: 'Pulsa',
    PULSA: 'Pulsa',
    // TV
    TV: 'TV',
    Tv: 'TV',
    tv: 'TV',
    // Gas
    Gas: 'Gas',
    gas: 'Gas',
    GAS: 'Gas',
  },

  // Label tombol kategori di menu utama PPOB (urutan tampil).
  // Key = group id untuk productList(), value = label tombol.
  CATEGORY_BUTTONS: [
    ['perdana', '📱 Perdana'], ['voucher', '🎫 Voucher'],
    ['kuota', '📶 Kuota'], ['e-money', '💳 E-Money'],
    ['game', '🎮 Game'], ['gas', '🔥 Gas'],
    ['masa-aktif', '⏰ Masa Aktif'], ['sms-telp', '💬 SMS & Telp'],
    ['pln', '💡 PLN'], ['pulsa', '📞 Pulsa'],
    ['tv', '📺 TV'],
  ],

  // ------------------------------------------------------------
  // PREMIUM EMOJI (custom emoji Telegram Premium)
  // ------------------------------------------------------------
  // Telegram TIDAK mendukung custom emoji di teks tombol inline
  // keyboard — hanya di teks pesan (message entities).
  // Cara pakai: isi custom_emoji_id dari pack favorit (didapat via
  // @Stickers bot / pack premium), lalu kirim judul menu dengan
  // entities: [{ type: 'custom_emoji', offset, length, custom_emoji_id }].
  // Kosongkan ('') bila belum ada — judul tampil tanpa emoji premium.
  // JANGAN isi ID acak: ID salah membuat pesan gagal terkirim.
  // ------------------------------------------------------------
  PREMIUM_EMOJI: {
    title_ppob: '',    // emoji untuk judul "PPOB RIPZZSTORE"
    perdana: '',
    voucher: '',
    kuota: '',
    'e-money': '',
    game: '',
    gas: '',
    'masa-aktif': '',
    'sms-telp': '',
    pln: '',
    pulsa: '',
    tv: '',
    cari: '',
    populer: '',
  },
};
