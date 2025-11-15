#!/bin/bash

# === Konfigurasi ===
DROPBEAR_VERSION="2019.76"
DROPBEAR_DEB_URL="http://archive.ubuntu.com/ubuntu/pool/universe/d/dropbear/dropbear-bin_2019.76-2build1_amd64.deb"
DROPBEAR_CONFIG_URL="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/cfg_conf_js/dropbear.conf"

# === Fungsi Bantu ===
log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

# === Eksekusi Utama ===
log_info "Memulai instalasi Dropbear versi ${DROPBEAR_VERSION} (tahun 2019)..."

# 1. Backup konfigurasi dan kunci host
log_info "Backup konfigurasi dan kunci host Dropbear..."
sudo cp /etc/default/dropbear /etc/default/dropbear.bak 2>/dev/null || true
sudo cp /etc/dropbear/dropbear_rsa_host_key /etc/dropbear/dropbear_rsa_host_key.bak 2>/dev/null || true
sudo cp /etc/dropbear/dropbear_dss_host_key /etc/dropbear/dropbear_dss_host_key.bak 2>/dev/null || true
sudo cp /etc/dropbear/dropbear_ecdsa_host_key /etc/dropbear/dropbear_ecdsa_host_key.bak 2>/dev/null || true

# 2. Hapus versi dropbear saat ini
log_info "Menghapus Dropbear versi saat ini..."
sudo apt remove -y dropbear 2>/dev/null || true
sudo apt autoremove -y

# 3. Unduh paket Dropbear 2019.76
log_info "Mengunduh Dropbear ${DROPBEAR_VERSION} dari: ${DROPBEAR_DEB_URL}..."
wget -q -O "dropbear_${DROPBEAR_VERSION}_amd64.deb" "${DROPBEAR_DEB_URL}"

# 4. Instal paket dropbear
log_info "Menginstal Dropbear ${DROPBEAR_VERSION}..."
sudo dpkg -i "dropbear_${DROPBEAR_VERSION}_amd64.deb"

# 5. Perbaiki dependensi jika ada
log_info "Memperbaiki dependensi (jika ada)..."
sudo apt --fix-broken install -y

# 6. Unduh konfigurasi (opsional, jika ingin mengganti konfigurasi default)
log_info "Mengunduh file konfigurasi dari: ${DROPBEAR_CONFIG_URL}..."
sudo wget -q -O /etc/default/dropbear "${DROPBEAR_CONFIG_URL}"

# 7. Setel izin file konfigurasi
log_info "Mengatur izin file konfigurasi..."
sudo chmod 644 /etc/default/dropbear

# 8. Restart layanan Dropbear
log_info "Me-restart layanan Dropbear..."
sudo systemctl enable dropbear
sudo systemctl restart dropbear

# 9. Cek status layanan
log_info "Memeriksa status layanan Dropbear..."
sudo systemctl status dropbear --no-pager

# 10. Tahan paket agar tidak diperbarui otomatis
log_info "Menahan paket dropbear agar tidak diperbarui otomatis..."
sudo apt-mark hold dropbear

log_info "Instalasi Dropbear versi ${DROPBEAR_VERSION} (tahun 2019) selesai!"
log_info "Konfigurasi telah diterapkan dan upgrade otomatis dinonaktifkan."