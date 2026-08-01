#!/bin/bash
# fix_all.sh — Perbaikan otomatis menyeluruh yang dipanggil setiap update:
#   1. Dropbear >= 2020.79  -> rebuild dengan algoritma lama (CBC/3DES/hmac-sha1-96) bila belum
#   2. Wendy API             -> install/update API saja (tanpa web dashboard), token dibuat otomatis
#   3. /etc/default/dropbear -> diperbarui (hapus flag -b duplikat)
#   4. Restart dropbear + wendy-api + verifikasi

set -e

REPO="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/"

echo "[fix_all] Pasang haveged (cegah timeout karena kekurangan entropy)..."
apt-get install -y haveged >/dev/null 2>&1 || true
systemctl enable --now haveged >/dev/null 2>&1 || true

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FIX ALL - PERBAIKAN OTOMATIS SETELAH UPDATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Dropbear: pastikan algoritma lama aktif (CBC/3DES/hmac-sha1-96) ──
echo "[1/4] Cek algoritma lama pada dropbear..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PreferredAuthentications=none \
    -c aes128-cbc,3des-cbc -m hmac-sha1-96 -p 143 root@127.0.0.1 true 2>&1 \
    | grep -qE "no matching cipher|refused|failed"; then
    echo "[1/4] Algoritma lama belum aktif. Membangun ulang dropbear (2-5 menit)..."
    wget -qO /usr/bin/fix_dropbear.sh "${REPO}files/fix_dropbear.sh"
    chmod +x /usr/bin/fix_dropbear.sh
    /usr/bin/fix_dropbear.sh
else
    echo "[1/4] Dropbear: algoritma lama sudah aktif. Skip rebuild."
fi

# ── 2. Wendy API: install/update (API only, tanpa dashboard) ──
echo "[2/4] Install/update Wendy API (tanpa web dashboard)..."
mkdir -p /etc/wendy-api
if [ ! -f /etc/wendy-api/token ]; then
    openssl rand -hex 24 >/etc/wendy-api/token
fi
chmod 600 /etc/wendy-api/token
wget -qO /usr/local/bin/wendy-api.py "${REPO}files/wendy-api.py"
wget -qO /etc/systemd/system/wendy-api.service "${REPO}files/wendy-api.service"
chmod +x /usr/local/bin/wendy-api.py
chmod 644 /etc/systemd/system/wendy-api.service
systemctl daemon-reload 2>/dev/null || true
systemctl enable --now wendy-api >/dev/null 2>&1 || systemctl restart wendy-api >/dev/null 2>&1 || true

# ── 3. Config dropbear ──
echo "[3/4] Perbarui /etc/default/dropbear + banner..."
wget -qO /etc/default/dropbear "${REPO}cfg_conf_js/dropbear.conf"
chmod 644 /etc/default/dropbear
wget -qO /etc/banner.txt "${REPO}banner/issue.net"
pkill -x dropbear 2>/dev/null || true
sleep 1
systemctl restart dropbear 2>/dev/null || /etc/init.d/dropbear restart >/dev/null 2>&1

# ── 4. Verifikasi ──
echo "[4/4] Verifikasi..."
if systemctl is-active wendy-api >/dev/null 2>&1; then
    echo "  ✓ wendy-api aktif (port 9000)"
else
    echo "  ✗ wendy-api GAGAL aktif"
fi
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PreferredAuthentications=none \
    -c aes128-cbc,3des-cbc -m hmac-sha1-96 -p 143 root@127.0.0.1 true 2>&1 \
    | grep -qE "no matching cipher|refused|failed"; then
    echo "  ✗ dropbear: algoritma lama GAGAL"
else
    echo "  ✓ dropbear: algoritma lama OK"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FIX ALL SELESAI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
