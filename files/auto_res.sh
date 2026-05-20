#!/bin/bash

# --- FUNGSI RESTORE BACKUP ---
restore_backup() {
    # --- KONFIGURASI ---
    # Ganti dengan URL Web App Anda
    local API_URL="https://script.google.com/macros/s/AKfycbxntHxLWt0Bxgg4HnbCDuaBZev3aBIIcZOD-0jkxuu33m8mt5FqibJmm1YfCVgGRnnqdA/exec"

    # Mode debug (ubah ke "true" untuk melihat detail request dan response)
    local DEBUG=false

    # --- DEFINISI WARNA ---
    local RED='\033[0;31m'
    local GREEN='\033[0;32m'
    local YELLOW='\033[0;33m'
    local BLUE='\033[0;34m'
    local CYAN='\033[0;36m'
    local NC='\033[0m' # No Color

    # --- FUNGSI BANTUAN ---
    
    # Fungsi untuk menampilkan pesan error (warna merah)
    error_exit() {
        echo -e "\e[31mError: $1\e[0m" >&2
        return 1
    }

    # Fungsi debug
    debug() {
        if [ "$DEBUG" = "true" ]; then
            echo -e "\e[33mDEBUG: $1\e[0m" >&2
        fi
    }

    # Fungsi untuk menampilkan pesan info
    print_info() {
        echo -e "${BLUE}[INFO]${NC} $1"
    }

    # Fungsi untuk menampilkan pesan error
    print_error() {
        echo -e "${RED}[ERROR]${NC} $1"
    }

    # Fungsi untuk menampilkan pesan sukses
    print_success() {
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    }

    # --- CEK DEPENDENSI ---
    if ! command -v curl &> /dev/null; then
        error_exit "curl tidak terinstall. Silakan install curl terlebih dahulu."
        return 1
    fi

    if ! command -v jq &> /dev/null; then
        error_exit "jq tidak terinstall. Silakan install jq untuk parsing JSON ('sudo apt-get install jq' atau 'brew install jq')."
        return 1
    fi

    if ! command -v wget &> /dev/null; then
        error_exit "wget tidak terinstall. Silakan install wget terlebih dahulu."
        return 1
    fi

    if ! command -v unzip &> /dev/null; then
        error_exit "unzip tidak terinstall. Silakan install unzip terlebih dahulu."
        return 1
    fi

    # --- PARSING ARGUMEN ---
    local DOMAIN=$(cat /etc/xray/domain)
    local API_KEY="ArjunaKencanaWungu"
    local DATE="$3"

    # Jika tanggal diberikan, gunakan itu. Jika tidak, gunakan hari ini.
    if [ -z "$DATE" ]; then
        DATE=$(date +%Y-%m-%d)
    fi

    # Validasi format tanggal (YYYY-MM-DD)
    if [[ ! $DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        error_exit "Format tanggal tidak valid. Gunakan format YYYY-MM-DD."
        return 1
    fi

    # --- FUNGSI RESTORE ---
    perform_restore() {
        local url_to_restore="$1"
        print_info "Link ditemukan. Memulai proses restore dari:"
        echo -e "${CYAN}${url_to_restore}${NC}"
        echo ""
        
        # Download dan ekstrak backup
        print_info "Mendownload file backup..."
        wget -O backup.zip "$url_to_restore" --no-check-certificate

        print_info "Mengekstrak file backup..."
        unzip -o backup.zip
        rm -f backup.zip

        print_info "Menyalin file konfigurasi..."
        [ -f "/root/backup/passwd" ] && cp /root/backup/passwd /etc/ || { print_error "Gagal menyalin passwd"; return 1; }
        [ -f "/root/backup/group" ] && cp /root/backup/group /etc/ || { print_error "Gagal menyalin group"; return 1; }
        [ -f "/root/backup/shadow" ] && cp /root/backup/shadow /etc/ || { print_error "Gagal menyalin shadow"; return 1; }
        [ -f "/root/backup/gshadow" ] && cp /root/backup/gshadow /etc/ || { print_error "Gagal menyalin gshadow"; return 1; }
        [ -f "/root/backup/crontab" ] && cp /root/backup/crontab /etc/ || { print_error "Gagal menyalin crontab"; return 1; }
        
        # Salin folder konfigurasi
        [ -d "/root/backup/.ssh.db" ] && cp -r /root/backup/.ssh.db/* /etc/ssh/ || { print_error "Gagal menyalin konfigurasi SSH"; return 1; }
        [ -d "/root/backup/.vmess.db" ] && cp -r /root/backup/.vmess.db/* /etc/vmess/ || { print_error "Gagal menyalin konfigurasi Vmess"; return 1; }
        [ -d "/root/backup/.vless.db" ] && cp -r /root/backup/.vless.db/* /etc/vless/ || { print_error "Gagal menyalin konfigurasi Vless"; return 1; }
        [ -d "/root/backup/.trojan.db" ] && cp -r /root/backup/.trojan.db/* /etc/trojan/ || { print_error "Gagal menyalin konfigurasi Trojan"; return 1; }
        [ -d "/root/backup/.shadowsocks.db" ] && cp -r /root/backup/.shadowsocks.db/* /etc/shadowsocks/ || { print_error "Gagal menyalin konfigurasi Shadowsocks"; return 1; }
        [ -d "/root/backup/figlet_text" ] && cp -r /root/backup/figlet_text /usr/bin/ || { print_error "Gagal menyalin figlet_text"; return 1; }
        [ -d "/root/backup/bot" ] && cp -r /root/backup/bot /etc/ || { print_error "Gagal menyalin bot"; return 1; }
        [ -d "/root/backup/kyt" ] && cp -r /root/backup/kyt /var/lib/ || { print_error "Gagal menyalin kyt"; return 1; }
        [ -d "/root/backup/xray" ] && cp -r /root/backup/xray /etc/ || { print_error "Gagal menyalin xray"; return 1; }
        [ -d "/root/backup/html" ] && cp -r /root/backup/html /var/www/ || { print_error "Gagal menyalin html"; return 1; }
        [ -d "/root/backup/limit" ] && cp -r /root/backup/limit /etc/kyt/ || { print_error "Gagal menyalin limit"; return 1; }
        [ -d "/root/backup/vmess" ] && cp -r /root/backup/vmess /etc/ || { print_error "Gagal menyalin vmess"; return 1; }
        [ -d "/root/backup/trojan" ] && cp -r /root/backup/trojan /etc/ || { print_error "Gagal menyalin trojan"; return 1; }
        [ -d "/root/backup/vless" ] && cp -r /root/backup/vless /etc/ || { print_error "Gagal menyalin vless"; return 1; }
        [ -d "/root/backup/shadowsocks" ] && cp -r /root/backup/shadowsocks /etc/ || { print_error "Gagal menyalin shadowsocks"; return 1; }

        # Cek untuk instalasi bot panel
        if [ -f "/root/backup/var.txt" ]; then
            print_info "File var.txt ditemukan."
            local RESPONSE
            while true; do
                echo -n "Apakah Anda ingin install bot panel? (y/n): "
                read -r RESPONSE
                case "$RESPONSE" in
                    [Yy]) 
                        print_info "Menginstall bot panel..."
                        mkdir -p /usr/bin/kyt
                        cp /root/backup/var.txt /usr/bin/kyt
                        rm -rf /root/backup
                        
                        apt update && apt upgrade -y
                        apt install python3 python3-pip git -y
                        cd /usr/bin
                        wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/bot.zip -O bot.zip
                        unzip -o bot.zip
                        mv bot/* /usr/bin/
                        chmod +x /usr/bin/*
                        rm -rf bot.zip
                        
                        wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/kyt.zip -O kyt.zip
                        unzip -o kyt.zip
                        pip3 install -r kyt/requirements.txt
                        apt install python3-telethon -y
                        rm -rf kyt.zip
                        
                        # Buat service systemd untuk bot
                        cat > /etc/systemd/system/kyt.service << END
[Unit]
Description=Simple kyt - @kyt
After=network.target

[Service]
WorkingDirectory=/usr/bin
ExecStart=/usr/bin/python3 -m kyt
Restart=always

[Install]
WantedBy=multi-user.target
END
                        systemctl daemon-reload
                        systemctl start kyt
                        systemctl enable kyt
                        print_success "Instalasi bot panel selesai."
                        break
                        ;;
                    [Nn]) 
                        print_info "Melewati instalasi bot panel."
                        break
                        ;;
                    *) 
                        print_error "Input tidak valid. Silakan masukkan 'y' atau 'n'."
                        ;;
                esac
            done
        fi
        
        # Bersihkan folder sementara
        rm -rf /root/backup
        
        print_success "Proses restore selesai!"
        return 0
    }

    # --- EKSEKUSI UTAMA ---
    echo "Mencari backup untuk domain: $DOMAIN"
    echo "Tanggal: $DATE"
    echo "----------------------------------------"

    # Buat URL dengan parameter
    local FULL_URL="${API_URL}?path=findBackup&domain=${DOMAIN}&date=${DATE}&key=${API_KEY}"

    debug "URL request: $FULL_URL"

    # Lakukan request ke API dan simpan response
    local RESPONSE=$(curl -s -L "${FULL_URL}")

    # Periksa jika curl gagal (misalnya masalah jaringan)
    if [ $? -ne 0 ]; then
        error_exit "Gagal menghubungi server API. Periksa koneksi internet dan URL Anda."
        return 1
    fi

    debug "Response dari server: $RESPONSE"

    # Periksa jika response kosong
    if [ -z "$RESPONSE" ]; then
        error_exit "Response dari server kosong. Mungkin ada masalah dengan API atau jaringan."
        return 1
    fi

    # Periksa jika response adalah valid JSON
    if ! echo "$RESPONSE" | jq . >/dev/null 2>&1; then
        error_exit "Response dari server bukan format JSON yang valid. Response: $RESPONSE"
        return 1
    fi

    # Parsing JSON response dengan jq
    local HTTP_STATUS=$(echo "${RESPONSE}" | jq -r '.status')
    local SUCCESS=$(echo "${RESPONSE}" | jq -r '.data.success // false') # Gunakan 'false' sebagai default jika kunci tidak ada
    local MESSAGE=$(echo "${RESPONSE}" | jq -r '.data.message // empty')
    local ERROR_MSG=$(echo "${RESPONSE}" | jq -r '.data.error // empty')
    local FILE_NAME=$(echo "${RESPONSE}" | jq -r '.data.fileName // empty')
    local DOWNLOAD_URL=$(echo "${RESPONSE}" | jq -r '.data.url // empty')

    debug "HTTP Status: $HTTP_STATUS"
    debug "Success: $SUCCESS"
    debug "Message: $MESSAGE"
    debug "Error: $ERROR_MSG"

    # --- TAMPILKAN HASIL ---
    if [ "${HTTP_STATUS}" -eq 200 ] && [ "${SUCCESS}" = "true" ]; then
        # Jika sukses, tampilkan informasi file dalam warna hijau
        echo -e "\e[32m${MESSAGE}\e[0m"
        echo "Nama File    : ${FILE_NAME}"
        echo "URL Download : ${DOWNLOAD_URL}"
        echo ""
        
        # Tanyakan apakah ingin melanjutkan dengan restore
        local RESPONSE
        while true; do
            echo -n "Apakah Anda ingin melanjutkan dengan proses restore? (y/n): "
            read -r RESPONSE
            case "$RESPONSE" in
                [Yy]) 
                    perform_restore "$DOWNLOAD_URL"
                    return $?
                    ;;
                [Nn]) 
                    print_info "Proses restore dibatalkan."
                    return 0
                    ;;
                *) 
                    print_error "Input tidak valid. Silakan masukkan 'y' atau 'n'."
                    ;;
            esac
        done
    else
        # Jika error, tampilkan pesan error dari API dalam warna merah
        local FINAL_ERROR="${ERROR_MSG}"
        # Jika pesan error tidak ada di body, gunakan status HTTP
        if [ -z "${FINAL_ERROR}" ]; then
            FINAL_ERROR="API mengembalikan status ${HTTP_STATUS}"
        fi
        error_exit "${FINAL_ERROR}"
        return 1
    fi
}

# Contoh penggunaan fungsi:
# restore_backup "wendi1.shifastore.my.id" "ArjunaKencanaWungu" "2023-10-27"
restore_backup