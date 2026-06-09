#!/bin/bash

restore_backup() {
    local API_URL="https://script.google.com/macros/s/AKfycbxntHxLWt0Bxgg4HnbCDuaBZev3aBIIcZOD-0jkxuu33m8mt5FqibJmm1YfCVgGRnnqdA/exec"
    local DEBUG=false

    local RED='\033[0;31m'
    local GREEN='\033[0;32m'
    local YELLOW='\033[0;33m'
    local BLUE='\033[0;34m'
    local CYAN='\033[0;36m'
    local NC='\033[0m'

    error_exit() {
        echo -e "\e[31mError: $1\e[0m" >&2
        return 1
    }

    debug() {
        if [ "$DEBUG" = "true" ]; then
            echo -e "\e[33mDEBUG: $1\e[0m" >&2
        fi
    }

    print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
    print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
    print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

    if ! command -v curl &>/dev/null; then
        error_exit "curl tidak terinstall."
        return 1
    fi
    if ! command -v jq &>/dev/null; then
        error_exit "jq tidak terinstall."
        return 1
    fi
    if ! command -v wget &>/dev/null; then
        error_exit "wget tidak terinstall."
        return 1
    fi
    if ! command -v unzip &>/dev/null; then
        error_exit "unzip tidak terinstall."
        return 1
    fi

    local DOMAIN=$(cat /etc/xray/domain 2>/dev/null)
    local API_KEY="ArjunaKencanaWungu"
    local DATE="${1:-$(date +%Y-%m-%d)}"

    if [[ ! $DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        error_exit "Format tanggal tidak valid. Gunakan YYYY-MM-DD."
        return 1
    fi

    perform_restore() {
        local url_to_restore="$1"
        print_info "Link ditemukan. Memulai restore dari:"
        echo -e "${CYAN}${url_to_restore}${NC}"
        echo ""

        cd /root || { print_error "Gagal ke /root"; return 1; }
        rm -rf /root/backup

        print_info "Mendownload file backup..."
        if echo "$url_to_restore" | grep -q "drive.google.com"; then
            local FILE_ID
            FILE_ID=$(echo "$url_to_restore" | grep -oP '(?<=/d/)[^/]+|(?<=id=)[^&]+')
            if [[ -n "$FILE_ID" ]]; then
                wget -q --show-progress --timeout=30 \
                    "https://docs.google.com/uc?export=download&confirm=t&id=$FILE_ID" -O backup.zip 2>/dev/null || \
                wget -q --show-progress --timeout=30 \
                    "https://docs.google.com/uc?export=download&id=$FILE_ID" -O backup.zip || {
                    print_error "Gagal download dari Google Drive"
                    return 1
                }
            else
                wget -q --show-progress --timeout=30 -O backup.zip "$url_to_restore" || {
                    print_error "Gagal download backup"
                    return 1
                }
            fi
        else
            wget -q --show-progress --timeout=30 -O backup.zip "$url_to_restore" || {
                print_error "Gagal download backup"
                return 1
            }
        fi

        if ! unzip -t backup.zip &>/dev/null; then
            print_error "File backup.zip rusak atau tidak valid!"
            rm -f backup.zip
            return 1
        fi

        print_info "Mengekstrak file backup..."
        unzip -o backup.zip
        rm -f backup.zip

        if [[ ! -d /root/backup ]]; then
            print_error "Direktori backup tidak ditemukan setelah ekstrak!"
            return 1
        fi

        print_info "Menyalin file konfigurasi..."
        cd /root/backup

        [[ -f passwd ]] && cp passwd /etc/ || print_error "Gagal passwd"
        [[ -f group ]] && cp group /etc/ || print_error "Gagal group"
        [[ -f shadow ]] && cp shadow /etc/ || print_error "Gagal shadow"
        [[ -f gshadow ]] && cp gshadow /etc/ || print_error "Gagal gshadow"
        [[ -f crontab ]] && cp crontab /etc/ || print_error "Gagal crontab"

        # File database (.db adalah file, bukan direktori)
        [[ -f .ssh.db ]] && cp .ssh.db /etc/ssh/ || print_error "Gagal .ssh.db"
        [[ -f .vmess.db ]] && cp .vmess.db /etc/vmess/ || print_error "Gagal .vmess.db"
        [[ -f .vless.db ]] && cp .vless.db /etc/vless/ || print_error "Gagal .vless.db"
        [[ -f .trojan.db ]] && cp .trojan.db /etc/trojan/ || print_error "Gagal .trojan.db"
        [[ -f .shadowsocks.db ]] && cp .shadowsocks.db /etc/shadowsocks/ || print_error "Gagal .shadowsocks.db"

        # Direktori konfigurasi
        [[ -d xray ]] && cp -r xray /etc/ && print_info "✓ xray"
        [[ -d bot ]] && cp -r bot /etc/ && print_info "✓ bot"
        [[ -d html ]] && cp -r html /var/www/ && print_info "✓ html"
        [[ -d kyt ]] && cp -r kyt /var/lib/ && print_info "✓ kyt"
        [[ -d limit ]] && cp -r limit /etc/kyt/ && print_info "✓ limit"
        [[ -d vmess ]] && cp -r vmess /etc/ && print_info "✓ vmess"
        [[ -d vless ]] && cp -r vless /etc/ && print_info "✓ vless"
        [[ -d trojan ]] && cp -r trojan /etc/ && print_info "✓ trojan"
        [[ -d shadowsocks ]] && cp -r shadowsocks /etc/ && print_info "✓ shadowsocks"

        # Bot panel
        if [[ -f var.txt ]]; then
            print_info "File var.txt ditemukan."
            local RESPONSE
            while true; do
                echo -n "Install bot panel? (y/n): "
                read -r RESPONSE
                case "$RESPONSE" in
                    [Yy])
                        print_info "Menginstall bot panel..."
                        mkdir -p /usr/bin/kyt
                        cp var.txt /usr/bin/kyt/
                        cd /root
                        rm -rf /root/backup
                        apt update -y >/dev/null 2>&1
                        apt install -y python3 python3-pip git >/dev/null 2>&1
                        cd /usr/bin
                        wget -q "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/bot.zip" -O bot.zip && \
                            unzip -o bot.zip >/dev/null 2>&1 && mv bot/* . 2>/dev/null && chmod +x * && rm -rf bot bot.zip
                        wget -q "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/kyt.zip" -O kyt.zip && \
                            unzip -o kyt.zip >/dev/null 2>&1 && pip3 install -r kyt/requirements.txt >/dev/null 2>&1
                        apt install -y python3-telethon >/dev/null 2>&1
                        rm -rf kyt.zip
                        cat > /etc/systemd/system/kyt.service << END
[Unit]
Description=Bot Panel - @kyt
After=network.target

[Service]
WorkingDirectory=/usr/bin
ExecStart=/usr/bin/python3 -m kyt
Restart=always

[Install]
WantedBy=multi-user.target
END
                        systemctl daemon-reload >/dev/null 2>&1
                        systemctl enable kyt >/dev/null 2>&1
                        systemctl restart kyt >/dev/null 2>&1
                        print_success "Bot panel terinstall."
                        break
                        ;;
                    [Nn])
                        print_info "Melewati instalasi bot panel."
                        break
                        ;;
                    *)
                        print_error "Input y/n."
                        ;;
                esac
            done
        fi

        # Fix permission dan restart services
        chmod 600 /etc/shadow /etc/gshadow 2>/dev/null
        print_info "Merestart layanan..."
        for svc in xray ws nginx haproxy ssh dropbear cron; do
            systemctl restart "$svc" 2>/dev/null && print_info "  ✓ $svc"
        done

        cd /root
        rm -rf /root/backup
        print_success "Proses restore selesai!"
        return 0
    }

    echo "Mencari backup untuk domain: $DOMAIN"
    echo "Tanggal: $DATE"
    echo "----------------------------------------"

    local FULL_URL="${API_URL}?path=findBackup&domain=${DOMAIN}&date=${DATE}&key=${API_KEY}"
    debug "URL: $FULL_URL"

    local RESPONSE=$(curl -s -L --connect-timeout 15 --max-time 30 "${FULL_URL}")
    if [ $? -ne 0 ]; then
        error_exit "Gagal menghubungi server API."
        return 1
    fi

    debug "Response: $RESPONSE"

    if [ -z "$RESPONSE" ]; then
        error_exit "Response dari server kosong."
        return 1
    fi

    if ! echo "$RESPONSE" | jq . >/dev/null 2>&1; then
        error_exit "Response bukan JSON valid. Response: $RESPONSE"
        return 1
    fi

    local HTTP_STATUS=$(echo "${RESPONSE}" | jq -r '.status')
    local SUCCESS=$(echo "${RESPONSE}" | jq -r '.data.success // false')
    local MESSAGE=$(echo "${RESPONSE}" | jq -r '.data.message // empty')
    local ERROR_MSG=$(echo "${RESPONSE}" | jq -r '.data.error // empty')
    local FILE_NAME=$(echo "${RESPONSE}" | jq -r '.data.fileName // empty')
    local DOWNLOAD_URL=$(echo "${RESPONSE}" | jq -r '.data.url // empty')

    if [ "${HTTP_STATUS}" -eq 200 ] && [ "${SUCCESS}" = "true" ]; then
        echo -e "\e[32m${MESSAGE}\e[0m"
        echo "Nama File    : ${FILE_NAME}"
        echo "URL Download : ${DOWNLOAD_URL}"
        echo ""
        local RESPONSE
        while true; do
            echo -n "Lanjutkan restore? (y/n): "
            read -r RESPONSE
            case "$RESPONSE" in
                [Yy])
                    perform_restore "$DOWNLOAD_URL"
                    return $?
                    ;;
                [Nn])
                    print_info "Restore dibatalkan."
                    return 0
                    ;;
                *)
                    print_error "Input y/n."
                    ;;
            esac
        done
    else
        local FINAL_ERROR="${ERROR_MSG}"
        if [ -z "${FINAL_ERROR}" ]; then
            FINAL_ERROR="API mengembalikan status ${HTTP_STATUS}"
        fi
        error_exit "${FINAL_ERROR}"
        return 1
    fi
}

restore_backup "$@"
