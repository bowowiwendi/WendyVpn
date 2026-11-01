#!/bin/bash
# install_dropbear2019.sh — Instal Dropbear 2019.78 LANGSUNG dari source.
# Dipanggil otomatis oleh setup-main.sh (ins_dropbear) di setiap setup baru.
#
# Alasan: versi distro (mis. 2022+ di Ubuntu 24.04) berbeda dari versi yang
# dipakai stack ini. Seluruh layanan (Aji02 + VPS Singapura) tervalidasi di
# Dropbear 2019.78 stock, jadi setup tidak lagi memakai versi distro apa pun
# — selalu build 2019.78 dari source, lalu apt-mark hold agar apt tidak
# menimpanya. Algoritma lawas (CBC, 3DES, hmac-sha1-96, dh-group1) diaktifkan
# seperti fix_dropbear.sh, agar client SSH tunnel lawas tetap bisa konek.
#
# Pola sama seperti fix_dropbear.sh (paket apt tetap terinstal untuk unit
# systemd-nya; yang diganti hanya binary di /usr/sbin).

set -e

VERSION="2019.78"
URL="https://github.com/mkj/dropbear/archive/refs/tags/DROPBEAR_${VERSION}.tar.gz"

echo "[install_dropbear2019] Instalasi dependensi build..."
apt-get update -y || true
apt-get install -y build-essential zlib1g-dev libtomcrypt-dev libtommath-dev wget
apt-get install -y libcrypt-dev 2>/dev/null || apt-get install -y libxcrypt-dev 2>/dev/null || true

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
cd "$TMPDIR"

echo "[install_dropbear2019] Download source Dropbear ${VERSION}..."
wget --timeout=30 --tries=2 -q "$URL" -O dropbear.tar.gz
tar xzf dropbear.tar.gz
cd "dropbear-DROPBEAR_${VERSION}"

echo "[install_dropbear2019] Aktifkan algoritma lama di default_options.h..."
sed -i 's/^#define DROPBEAR_ENABLE_CBC_MODE 0/#define DROPBEAR_ENABLE_CBC_MODE 1/' default_options.h
sed -i 's/^#define DROPBEAR_3DES 0/#define DROPBEAR_3DES 1/' default_options.h
sed -i 's/^#define DROPBEAR_SHA1_96_HMAC 0/#define DROPBEAR_SHA1_96_HMAC 1/' default_options.h
sed -i 's/^#define DROPBEAR_DH_GROUP1_CLIENTONLY 1/#define DROPBEAR_DH_GROUP1_CLIENTONLY 0/' default_options.h
sed -i 's/^#define DROPBEAR_DSS 1/#define DROPBEAR_DSS 0/' default_options.h

echo "[install_dropbear2019] Build (2-5 menit)..."
if ! ./configure --prefix=/usr --sysconfdir=/etc --disable-pam >/dev/null 2>&1 \
    || ! make -j"$(nproc)" PROGRAMS="dropbear dropbearkey dropbearconvert" >/dev/null 2>&1; then
    echo "[install_dropbear2019] Build dengan lib sistem gagal, coba bundled libtom..."
    make distclean >/dev/null 2>&1 || true
    ./configure --prefix=/usr --sysconfdir=/etc --disable-pam --enable-bundled-libtom >/dev/null
    make -j"$(nproc)" PROGRAMS="dropbear dropbearkey dropbearconvert"
fi

echo "[install_dropbear2019] Install binary..."
install -m 755 dropbear /usr/sbin/dropbear
install -m 755 dropbearkey /usr/sbin/dropbearkey
install -m 755 dropbearconvert /usr/sbin/dropbearconvert

echo "[install_dropbear2019] Mencegah apt menimpa build khusus..."
apt-mark hold dropbear dropbear-bin >/dev/null 2>&1 || true

echo "[install_dropbear2019] Restart layanan..."
pkill -x dropbear 2>/dev/null || true
sleep 1
systemctl restart dropbear

echo "[install_dropbear2019] Verifikasi versi dari banner..."
BANNER=$(timeout 5 bash -c 'exec 3<>/dev/tcp/127.0.0.1/143; head -1 <&3' 2>/dev/null || true)
echo "[install_dropbear2019] Banner: $BANNER"
case "$BANNER" in
    *dropbear_2019.78*) echo "[install_dropbear2019] OK: Dropbear 2019.78 aktif." ;;
    *) echo "[install_dropbear2019] PERINGATAN: banner bukan 2019.78, periksa layanan!"; exit 1 ;;
esac

echo "[install_dropbear2019] Verifikasi handshake dengan cipher lama..."
if ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o PreferredAuthentications=none -c aes128-cbc,3des-cbc -m hmac-sha1-96 -p 143 root@127.0.0.1 true 2>&1 | grep -qE "no matching cipher|refused|failed"; then
    echo "[install_dropbear2019] PERINGATAN: cipher lama masih tidak tersedia!"
else
    echo "[install_dropbear2019] OK: handshake cipher lama diterima."
fi

echo "[install_dropbear2019] Status layanan:"
systemctl status dropbear --no-pager | head -8
echo "[install_dropbear2019] Selesai."
