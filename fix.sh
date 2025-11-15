#!/bin/bash

# --- Konfigurasi ---
# Ganti dengan versi Dropbear 2019 yang sesuai untuk sistem Anda
# Temukan versi yang tersedia dengan: apt-cache policy dropbear
DROPBEAR_VERSION="2019.78-1" 
URL_CONFIG="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/cfg_conf_js/dropbear.conf"

# --- Eksekusi ---
# Keluar dari script jika ada perintah yang gagal
set -e

echo "Memulai proses instalasi Dropbear versi ${DROPBEAR_VERSION}..."

# 1. Update daftar paket
echo "Mengupdate daftar paket..."
apt-get update

# 2. Instal Dropbear dengan versi spesifik
echo "Menginstal dropbear versi ${DROPBEAR_VERSION}..."
apt-get install dropbear=${DROPBEAR_VERSION} -y

# 3. Unduh file konfigurasi
echo "Mengunduh file konfigurasi..."
wget -q -O /etc/default/dropbear "${URL_CONFIG}"

# 4. Setel izin file konfigurasi yang benar (bukan eksekusi)
echo "Mengatur izin file konfigurasi..."
chmod 644 /etc/default/dropbear

# 5. Restart layanan Dropbear untuk menerapkan konfigurasi
echo "Me-restart layanan Dropbear..."
systemctl restart dropbear

# 6. Cek status layanan
echo "Menampilkan status layanan Dropbear..."
systemctl status dropbear --no-pager

# 7. "Hold" paket untuk mencegah upgrade otomatis
echo "Menahan paket dropbear agar tidak diperbarui otomatis..."
apt-mark hold dropbear

echo "Instalasi dan konfigurasi Dropbear versi ${DROPBEAR_VERSION} selesai!"
echo "Catatan: Script ini mempertahankan dropbear versi 2019 sesuai keinginan."