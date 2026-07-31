#!/bin/bash
# fix_dropbear.sh — Rebuild Dropbear >= 2020.79 dengan dukungan algoritma lama
# (CBC, 3DES, hmac-sha1-96, dh-group1) agar client SSH tunnel lawas tetap bisa konek.
# Dipanggil otomatis oleh setup-main.sh (ins_dropbear) atau manual di VPS.

set -e

VERSION="2020.81"
URL="https://github.com/mkj/dropbear/archive/refs/tags/DROPBEAR_${VERSION}.tar.gz"

echo "[fix_dropbear] Instalasi dependensi build..."
apt-get update -y || true
apt-get install -y build-essential zlib1g-dev libtomcrypt-dev libtommath-dev wget
apt-get install -y libcrypt-dev 2>/dev/null || apt-get install -y libxcrypt-dev 2>/dev/null || true

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
cd "$TMPDIR"

echo "[fix_dropbear] Download source Dropbear ${VERSION}..."
wget -q "$URL" -O dropbear.tar.gz
tar xzf dropbear.tar.gz
cd "dropbear-DROPBEAR_${VERSION}"

echo "[fix_dropbear] Aktifkan algoritma lama di default_options.h..."
sed -i 's/^#define DROPBEAR_ENABLE_CBC_MODE 0/#define DROPBEAR_ENABLE_CBC_MODE 1/' default_options.h
sed -i 's/^#define DROPBEAR_3DES 0/#define DROPBEAR_3DES 1/' default_options.h
sed -i 's/^#define DROPBEAR_SHA1_96_HMAC 0/#define DROPBEAR_SHA1_96_HMAC 1/' default_options.h
sed -i 's/^#define DROPBEAR_DH_GROUP1_CLIENTONLY 1/#define DROPBEAR_DH_GROUP1_CLIENTONLY 0/' default_options.h
sed -i 's/^#define DROPBEAR_DSS 1/#define DROPBEAR_DSS 0/' default_options.h

echo "[fix_dropbear] Build (2-5 menit)..."
./configure --prefix=/usr --sysconfdir=/etc --disable-pam >/dev/null
make -j"$(nproc)" PROGRAMS="dropbear dropbearkey dropbearconvert"

echo "[fix_dropbear] Install binary..."
install -m 755 dropbear /usr/sbin/dropbear
install -m 755 dropbearkey /usr/sbin/dropbearkey
install -m 755 dropbearconvert /usr/sbin/dropbearconvert

echo "[fix_dropbear] Mencegah apt menimpa build khusus..."
apt-mark hold dropbear dropbear-bin >/dev/null 2>&1 || true

echo "[fix_dropbear] Restart layanan..."
pkill -x dropbear 2>/dev/null || true
sleep 1
systemctl restart dropbear

echo "[fix_dropbear] Verifikasi handshake dengan cipher lama..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PreferredAuthentications=none -c aes128-cbc,3des-cbc -m hmac-sha1-96 -p 143 root@127.0.0.1 true 2>&1 | grep -qE "no matching cipher|refused|failed"; then
    echo "[fix_dropbear] PERINGATAN: cipher lama masih tidak tersedia!"
else
    echo "[fix_dropbear] OK: handshake cipher lama diterima."
fi

echo "[fix_dropbear] Status layanan:"
systemctl status dropbear --no-pager | head -8
echo "[fix_dropbear] Selesai."
