// ============================================================
// Helper format pesan Telegram (HTML parse_mode)
// esc(): amankan teks dinamis agar tidak error "can't parse entities"
// ============================================================
function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

module.exports = { esc };
