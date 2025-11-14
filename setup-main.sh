#!/bin/bash
# --- Inisialisasi Logging ---
LOG_FILE="/var/log/wendy_vpn_setup.log"
exec > >(tee -a "$LOG_FILE") 2>&1 # Redirect semua output stdout dan stderr ke log dan terminal
# Fungsi untuk mencatat log dengan timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}
log "========== MULAI SETUP WENDY VPN =========="
log "Skrip dimulai oleh pengguna: $(whoami)"
# --- Bagian Setup Awal (tetap sama, hanya ditambah logging) ---
clear
log "Memperbarui daftar paket..."
apt update -y >> "$LOG_FILE" 2>&1
log "Memutakhirkan paket..."
apt upgrade -y >> "$LOG_FILE" 2>&1
log "Menginstal curl..."
apt install curl -y >> "$LOG_FILE" 2>&1
log "Menginstal socat..."
apt install socat -y >> "$LOG_FILE" 2>&1

# Coba instal wondershaper dari repo, jika gagal, instal dari GitHub
log "Menginstal wondershaper..."
if ! apt install wondershaper -y >> "$LOG_FILE" 2>&1; then
    log "wondershaper tidak tersedia di repo, menginstal dari GitHub..."
    apt install -y git make >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal dependensi build untuk wondershaper."
    cd /tmp || exit 1
    if git clone https://github.com/magnific0/wondershaper.git >> "$LOG_FILE" 2>&1; then
        cd wondershaper || exit 1
        if sudo make install >> "$LOG_FILE" 2>&1; then
            log "wondershaper berhasil dikompilasi dan diinstal."
        else
            log "ERROR: Gagal mengkompilasi/menginstal wondershaper."
        fi
        cd / || exit 1
        rm -rf /tmp/wondershaper
    else
        log "ERROR: Gagal mengkloning repositori wondershaper."
    fi
    cd / || exit 1
fi

# Definisi warna (tidak perlu di-log)
Green="\e[92;1m"
RED="\033[1;31m"
YELLOW="\033[33m"
BLUE="\033[36m"
FONT="\033[0m"
GREENBG="\033[42;37m"
REDBG="\033[41;37m"
OK="${Green}--->${FONT}"
EROR="${RED}[EROR]${FONT}"
GRAY="\e[1;30m"
NC='\e[0m'
red='\e[1;31m'
green='\e[0;32m'
TIME=$(date '+%d %b %Y')
log "Mendapatkan IP publik..."
ipsaya=$(wget -qO- ipinfo.io/ip)
TIMES="10"
CHATID="5162695441"
KEY="7117869623:AAHBmgzOUsmHBjcm5TFir9JmaZ_X7ynMoF4"
URL="https://api.telegram.org/bot$KEY/sendMessage"
clear
export IP=$( curl -sS icanhazip.com )
clear
clear && clear && clear
clear;clear;clear
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo -e "\033[96;1m                  WENDY VPN TUNNELING\033[0m"
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo ""
# --- Bagian Password (ditambah logging) ---
while true; do
    echo "Select an option/Pilih opsi:"
    echo "1. Ubah Password/Change Password"
    echo "2. or Enter, Lewati/Skip"
    read -p "Masukkan pilihan/Input option(1/2): " pilihan
    if [[ "$pilihan" == "1" ]]; then
        while true; do
            read -s -p "Password : " passwd
            echo
            read -s -p "Konfirmasi Password : " passwd_confirm
            echo
            if [[ -n "$passwd" && "$passwd" == "$passwd_confirm" ]]; then
                echo "$passwd" > /etc/.password.txt
                log "Password root berhasil diubah."
                break
            else
                echo "Password harus diisi dan harus sama. Silakan coba lagi."
                log "Gagal mengubah password: Password tidak cocok atau kosong."
            fi
        done
        echo root:$passwd | sudo chpasswd root > /dev/null 2>&1
        # Perbaikan restart ssh/sshd
        sudo systemctl restart ssh > /dev/null 2>&1 || sudo systemctl restart sshd > /dev/null 2>&1
        log "Layanan SSH/SSHD telah direstart."
        break
    elif [[ "$pilihan" == "2" || -z "$pilihan" ]]; then
        echo "Proses pengubahan password dilewati."
        log "Proses pengubahan password dilewati oleh pengguna."
        break
    else
        echo "Pilihan tidak valid. Silakan coba lagi."
    fi
done
# --- Deteksi Arsitektur dan OS (ditambah logging) ---
if [[ $( uname -m | awk '{print $1}' ) == "x86_64" ]]; then
    echo -e "${OK} Your Architecture Is Supported ( ${green}$( uname -m )${NC} )"
    log "Arsitektur $(uname -m) didukung."
else
    echo -e "${EROR} Your Architecture Is Not Supported ( ${YELLOW}$( uname -m )${NC} )"
    log "ERROR: Arsitektur $(uname -m) tidak didukung. Keluar."
    exit 1
fi
OS_ID=$(grep -w ID /etc/os-release | cut -d'=' -f2 | tr -d '"')
OS_NAME=$(grep -w PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '"')
if [[ "$OS_ID" == "ubuntu" ]] || [[ "$OS_ID" == "debian" ]]; then
    echo -e "${OK} Your OS Is Supported ( ${green}$OS_NAME${NC} )"
    log "OS $OS_NAME didukung."
else
    echo -e "${EROR} Your OS Is Not Supported ( ${YELLOW}$OS_NAME${NC} )"
    log "ERROR: OS $OS_NAME tidak didukung. Keluar."
    exit 1
fi
# --- Deteksi IP (ditambah logging) ---
if [[ -z "$ipsaya" ]]; then
    echo -e "${EROR} IP Address ( ${RED}Not Detected${NC} )"
    log "ERROR: IP publik tidak terdeteksi."
else
    echo -e "${OK} IP Address ( ${green}$ipsaya${NC} )"
    log "IP publik terdeteksi: $ipsaya"
fi
echo ""
read -p "$( echo -e "Press ${GRAY}[ ${NC}${green}Enter${NC} ${GRAY}]${NC} For Starting Installation") "
echo ""
clear
# --- Cek Root dan Virtualisasi (ditambah logging) ---
if [ "${EUID}" -ne 0 ]; then
    echo "You need to run this script as root"
    log "ERROR: Skrip tidak dijalankan sebagai root. Keluar."
    exit 1
fi
if [ "$(systemd-detect-virt)" == "openvz" ]; then
    echo "OpenVZ is not supported"
    log "ERROR: Lingkungan OpenVZ tidak didukung. Keluar."
    exit 1
fi
red='\e[1;31m'
green='\e[0;32m'
NC='\e[0m'
MYIP=$(curl -sS ipv4.icanhazip.com)
log "IP publik (alternatif): $MYIP"
echo -e "\e[32mloading...\e[0m"
clear
# --- Pengambilan Data Pengguna (ditambah logging) ---
rm -f /usr/bin/user
log "Mengambil data pengguna dari repositori..."
username=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $2}')
if [ -z "$username" ]; then
    log "WARNING: Username tidak ditemukan untuk IP $MYIP."
else
    echo "$username" >/usr/bin/user
    log "Username ditemukan: $username"
fi
valid=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $3}')
echo "$valid" >/usr/bin/e
# username=$(cat /usr/bin/user) # Tidak perlu, sudah didefinisikan di atas
# oid=$(cat /usr/bin/ver) # Tidak ada definisi untuk /usr/bin/ver, dilewati
exp=$(cat /usr/bin/e)
clear
# --- Perhitungan Tanggal (tidak perlu di-log detail) ---
DATE=$(date +'%Y-%m-%d')
d1=$(date -d "$valid" +%s)
d2=$(date -d "$DATE" +%s)
certifacate=$(((d1 - d2) / 86400))
datediff() {
d1=$(date -d "$1" +%s)
d2=$(date -d "$2" +%s)
echo -e "$COLOR1 $NC Expiry In   : $(( (d1 - d2) / 86400 )) Days"
}
mai="datediff "$Exp" "$DATE""
Info="(${green}Active${NC})"
Error="(${RED}ExpiRED${NC})"
today=`date -d "0 days" +"%Y-%m-%d"`
Exp1=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $4}')
if [[ $today < $Exp1 ]]; then
sts="${Info}"
else
sts="${Error}"
fi
echo -e "\e[32mloading...\e[0m"
clear
# --- Definisi Variabel (tidak perlu di-log detail) ---
REPO="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/"
start=$(date +%s)
secs_to_human() {
echo "Installation time : $((${1} / 3600)) hours $(((${1} / 60) % 60)) minute's $((${1} % 60)) seconds"
}
# --- Fungsi Helper (ditambah logging) ---
function print_ok() {
    echo -e "${OK} ${BLUE} $1 ${FONT}"
    log "OK: $1"
}
function print_install() {
    echo -e "${green} =============================== ${FONT}"
    echo -e "${YELLOW} # $1 ${FONT}"
    echo -e "${green} =============================== ${FONT}"
    log "INSTALL: $1"
    sleep 1
}
function print_error() {
    echo -e "${EROR} ${REDBG} $1 ${FONT}"
    log "ERROR: $1"
}
function print_success() {
    if [[ 0 -eq $? ]]; then
        echo -e "${green} =============================== ${FONT}"
        echo -e "${Green} # $1 berhasil dipasang${FONT}"
        echo -e "${green} =============================== ${FONT}"
        log "SUCCESS: $1 berhasil dipasang"
        sleep 2
    fi
}
function is_root() {
    if [[ 0 == "$UID" ]]; then
        print_ok "Root user Start installation process"
    else
        print_error "The current user is not the root user, please switch to the root user and run the script again"
    fi
}
# --- Fungsi Instalasi Utama (ditambah logging di dalamnya) ---
function first_setup() {
    log "========== MENJALANKAN first_setup =========="
    timedatectl set-timezone Asia/Jakarta >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal mengatur timezone."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections >> "$LOG_FILE" 2>&1
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections >> "$LOG_FILE" 2>&1
    print_success "Directory Xray"
    # Mendeteksi OS (sudah dilakukan sebelumnya)
    if [[ "$OS_ID" == "ubuntu" ]]; then
        log "Setup Dependencies $OS_NAME"
        sudo apt update -y >> "$LOG_FILE" 2>&1
        log "Installing haproxy from default repo for Ubuntu"
        apt-get install -y haproxy >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal haproxy."
    elif [[ "$OS_ID" == "debian" ]]; then
        log "Setup Dependencies For OS Is $OS_NAME"
        log "Installing haproxy from default repo for Debian"
        apt-get install -y haproxy >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal haproxy."
    else
        echo -e "Your OS Is Not Supported ($OS_NAME)"
        log "ERROR: OS tidak didukung dalam first_setup. Ini seharusnya tidak terjadi."
        exit 1
    fi
    print_success "HAProxy Installation"
    log "========== first_setup SELESAI =========="
}
function nginx_install() {
    log "========== MENJALANKAN nginx_install =========="
    if [[ "$OS_ID" == "ubuntu" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        sudo apt-get install nginx -y >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal nginx (Ubuntu)."
    elif [[ "$OS_ID" == "debian" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        apt -y install nginx >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal nginx (Debian)."
    else
        echo -e " Your OS Is Not Supported ( ${YELLOW}$OS_NAME${FONT} )"
        log "ERROR: OS tidak didukung dalam nginx_install. Ini seharusnya tidak terjadi."
    fi
    print_success "Nginx Installation"
    log "========== nginx_install SELESAI =========="
}
function base_package() {
    log "========== MENJALANKAN base_package =========="
    clear
    print_install "Menginstall Packet Yang Dibutuhkan"
    # Instalasi paket (dikelompokkan untuk logging yang lebih baik)
    log "Menginstal paket dasar..."
    # Ganti python dengan python3
    apt install zip pwgen openssl netcat socat cron bash-completion figlet python3 -y >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal paket dasar 1."
    log "Memperbarui dan memutakhirkan sistem..."
    apt update -y >> "$LOG_FILE" 2>&1
    apt upgrade -y >> "$LOG_FILE" 2>&1
    apt dist-upgrade -y >> "$LOG_FILE" 2>&1
    log "Menginstal dan mengkonfigurasi chrony..."
    systemctl enable chronyd >> "$LOG_FILE" 2>&1
    systemctl restart chronyd >> "$LOG_FILE" 2>&1
    systemctl enable chrony >> "$LOG_FILE" 2>&1
    systemctl restart chrony >> "$LOG_FILE" 2>&1
    chronyc sourcestats -v >> "$LOG_FILE" 2>&1
    chronyc tracking -v >> "$LOG_FILE" 2>&1
    apt install ntpdate -y >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal ntpdate."
    ntpdate pool.ntp.org >> "$LOG_FILE" 2>&1
    log "Menginstal utilitas sistem..."
    apt install sudo -y >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal sudo."
    sudo apt-get clean all >> "$LOG_FILE" 2>&1
    sudo apt-get autoremove -y >> "$LOG_FILE" 2>&1
    sudo apt-get install -y debconf-utils >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal debconf-utils."
    log "Menghapus paket yang tidak diinginkan..."
    sudo apt-get remove --purge exim4 -y >> "$LOG_FILE" 2>&1
    sudo apt-get remove --purge ufw firewalld -y >> "$LOG_FILE" 2>&1
    log "Menginstal software-properties-common..."
    sudo apt-get install -y --no-install-recommends software-properties-common >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal software-properties-common."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections >> "$LOG_FILE" 2>&1
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections >> "$LOG_FILE" 2>&1
    log "Menginstal paket utama..."
    # Ganti python dengan python3
    sudo apt-get install -y speedtest-cli vnstat libnss3-dev libnspr4-dev pkg-config libpam0g-dev libcap-ng-dev libcap-ng-utils libselinux1-dev libcurl4-nss-dev flex bison make libnss3-tools libevent-dev bc rsyslog dos2unix zlib1g-dev libssl-dev libsqlite3-dev sed dirmngr libxml-parser-perl build-essential gcc g++ python3 htop lsof tar wget curl ruby zip unzip p7zip-full python3-pip libc6 util-linux build-essential msmtp-mta ca-certificates bsd-mailx iptables iptables-persistent netfilter-persistent net-tools openssl ca-certificates gnupg gnupg2 ca-certificates lsb-release gcc shc make cmake git screen socat xz-utils apt-transport-https gnupg1 dnsutils cron bash-completion ntpdate chrony jq openvpn easy-rsa >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal paket utama."
    print_success "Packet Yang Dibutuhkan"
    log "========== base_package SELESAI =========="
}
function pasang_domain() {
    log "========== MENJALANKAN pasang_domain =========="
    clear
    echo -e "==============================="
    echo -e "   |\e[1;32mPlease Select a Domain Type Below \e[0m|"
    echo -e "==============================="
    echo -e "     \e[1;32m1)\e[0m Your Domain"
    echo -e "     \e[1;32m2)\e[0m Random Domain "
    echo -e "==============================="
    read -p "   Please select numbers 1-2 or Any Button(Random) : " host
    echo ""
    if [[ $host == "1" ]]; then
        clear
        echo -e "\e[1;32m===============================$NC"
        echo -e "\e[1;36m     INPUT SUBDOMAIN $NC"
        echo -e "\e[1;32m===============================$NC"
        echo -e "\033[91;1m contoh subdomain :\033[0m \033[93 wendi.ssh.cloud\033[0m"
        read -p "SUBDOMAIN :  " host1
        echo "IP=" >> /var/lib/kyt/ipvps.conf
        echo $host1 > /etc/xray/domain
        echo $host1 > /etc/xray/scdomain
        echo $host1 > /etc/v2ray/domain
        echo $host1 > /root/domain
        echo $host1 > /root/scdomain
        echo ""
        print_install "Subdomain/Domain is Used"
        log "Domain kustom digunakan: $host1"
        clear
    elif [[ $host == "2" ]]; then
        log "Mengunduh dan menjalankan random.sh..."
        wget ${REPO}files/random.sh && chmod +x random.sh && ./random.sh >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menjalankan random.sh."
        rm -f /root/random.sh
        clear
        print_install "Random Subdomain/Domain is Used"
        log "Domain acak digunakan."
    else
        host="2"
        print_install "Random Subdomain/Domain is Used"
        log "Domain acak digunakan (default)."
        clear
    fi
    log "========== pasang_domain SELESAI =========="
}
function pasang_ssl() {
    log "========== MENJALANKAN pasang_ssl =========="
    clear
    print_install "Memasang SSL Pada Domain"
    rm -rf /etc/xray/xray.key
    rm -rf /etc/xray/xray.crt
    domain=$(cat /root/domain)
    log "Domain untuk SSL: $domain"
    STOPWEBSERVER=$(lsof -i:80 | cut -d' ' -f1 | awk 'NR==2 {print $1}')
    rm -rf /root/.acme.sh
    mkdir /root/.acme.sh
    log "Menghentikan layanan web sementara..."
    systemctl stop $STOPWEBSERVER >> "$LOG_FILE" 2>&1 || log "INFO: Gagal menghentikan $STOPWEBSERVER (mungkin tidak berjalan)."
    systemctl stop nginx >> "$LOG_FILE" 2>&1 || log "INFO: Gagal menghentikan nginx (mungkin tidak berjalan)."
    log "Mengunduh dan menjalankan acme.sh..."
    # Ganti URL acme.sh ke yang resmi
    curl https://raw.githubusercontent.com/acmesh-official/acme.sh/master/acme.sh -o /root/.acme.sh/acme.sh >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh acme.sh."
    chmod +x /root/.acme.sh/acme.sh
    /root/.acme.sh/acme.sh --upgrade --auto-upgrade >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal memutakhirkan acme.sh."
    /root/.acme.sh/acme.sh --set-default-ca --server letsencrypt >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengatur CA default untuk acme.sh."
    log "Menerbitkan sertifikat SSL..."
    /root/.acme.sh/acme.sh --issue -d $domain --standalone -k ec-256 >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menerbitkan sertifikat SSL untuk $domain."
    ~/.acme.sh/acme.sh --installcert -d $domain --fullchainpath /etc/xray/xray.crt --keypath /etc/xray/xray.key --ecc >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal sertifikat SSL untuk $domain."
    chmod 777 /etc/xray/xray.key # Peringatan: Permission ini berisiko tinggi
    log "Permission key diatur ke 777 (PERINGATAN: BERISIKO TINGGI!)."
    print_success "SSL Certificate"
    log "========== pasang_ssl SELESAI =========="
}
function make_folder_xray() {
    log "========== MENJALANKAN make_folder_xray =========="
    rm -rf /etc/vmess/.vmess.db
    rm -rf /etc/vless/.vless.db
    rm -rf /etc/trojan/.trojan.db
    rm -rf /etc/shadowsocks/.shadowsocks.db
    rm -rf /etc/ssh/.ssh.db
    rm -rf /etc/bot/.bot.db
    mkdir -p /etc/bot
    mkdir -p /etc/xray
    mkdir -p /etc/vmess
    mkdir -p /etc/vless
    mkdir -p /etc/trojan
    mkdir -p /etc/shadowsocks
    mkdir -p /etc/ssh
    mkdir -p /usr/bin/xray/
    mkdir -p /var/log/xray/
    mkdir -p /var/www/html
    mkdir -p /etc/kyt/files/vmess/ip
    mkdir -p /etc/kyt/files/vless/ip
    mkdir -p /etc/kyt/files/trojan/ip
    mkdir -p /etc/kyt/files/ssh/ip
    mkdir -p /etc/files/vmess
    mkdir -p /etc/files/vless
    mkdir -p /etc/files/trojan
    mkdir -p /etc/files/ssh
    chmod +x /var/log/xray
    touch /etc/xray/domain
    touch /var/log/xray/access.log
    touch /var/log/xray/error.log
    touch /etc/vmess/.vmess.db
    touch /etc/vless/.vless.db
    touch /etc/trojan/.trojan.db
    touch /etc/shadowsocks/.shadowsocks.db
    touch /etc/ssh/.ssh.db
    touch /etc/bot/.bot.db
    touch /etc/xray/.lock.db
    echo "& plughin Account" >>/etc/vmess/.vmess.db
    echo "& plughin Account" >>/etc/vless/.vless.db
    echo "& plughin Account" >>/etc/trojan/.trojan.db
    echo "& plughin Account" >>/etc/shadowsocks/.shadowsocks.db
    echo "& plughin Account" >>/etc/ssh/.ssh.db
    cat >/etc/xray/.lock.db <<EOF
#vmess
#vless
#trojan
#ss
EOF
    log "Folder dan file Xray berhasil dibuat."
    log "========== make_folder_xray SELESAI =========="
}
function install_xray() {
    log "========== MENJALANKAN install_xray =========="
    clear
    print_install "Core Xray 1.8.1 Latest Version"
    domainSock_dir="/run/xray";! [ -d $domainSock_dir ] && mkdir  $domainSock_dir
    chown www-data.www-data $domainSock_dir
    # Gunakan python3 untuk mendapatkan versi
    latest_version="$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases | grep tag_name | sed -E 's/.*"v(.*)".*/\1/' | head -n 1)"
    log "Versi Xray terbaru yang ditemukan: $latest_version"
    log "Mengunduh dan menjalankan skrip instalasi Xray resmi..."
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" @ install -u www-data --version $latest_version >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal Xray."
    log "Mengunduh konfigurasi Xray..."
    wget -O /etc/xray/config.json "${REPO}cfg_conf_js/config.json" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh config.json Xray."
    wget -O /etc/systemd/system/runn.service "${REPO}files/runn.service" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh runn.service."
    domain=$(cat /etc/xray/domain)
    IPVS=$(cat /etc/xray/ipvps)
    print_success "Core Xray 1.8.1 Latest Version"
    clear
    curl -s ipinfo.io/city >>/etc/xray/city
    curl -s ipinfo.io/org | cut -d " " -f 2-10 >>/etc/xray/isp
    print_install "Memasang Konfigurasi Packet"
    log "Mengunduh konfigurasi HAProxy dan Nginx..."
    wget -O /etc/haproxy/haproxy.cfg "${REPO}cfg_conf_js/haproxy.cfg" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh haproxy.cfg."
    wget -O /etc/nginx/conf.d/xray.conf "${REPO}cfg_conf_js/xray.conf" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh xray.conf Nginx."
    sed -i "s/xxx/${domain}/g" /etc/haproxy/haproxy.cfg
    sed -i "s/xxx/${domain}/g" /etc/nginx/conf.d/xray.conf
    curl ${REPO}cfg_conf_js/nginx.conf > /etc/nginx/nginx.conf >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh nginx.conf utama."
    cat /etc/xray/xray.crt /etc/xray/xray.key | tee /etc/haproxy/hap.pem >> "$LOG_FILE" 2>&1
    chmod +x /etc/systemd/system/runn.service
    rm -rf /etc/systemd/system/xray.service.d
    # Perbaiki konfigurasi systemd service
    cat >/etc/systemd/system/xray.service <<EOF
[Unit]
Description=Xray Service
Documentation=https://github.com
After=network.target nss-lookup.target
[Service]
User=www-data
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
NoNewPrivileges=true
ExecStart=/usr/local/bin/xray run -config /etc/xray/config.json
Restart=on-failure
RestartPreventExitStatus=23
LimitNPROC=10000
LimitNOFILE=1000000
[Install]
WantedBy=multi-user.target
EOF
    print_success "Konfigurasi Packet"
    log "========== install_xray SELESAI =========="
}
function ssh(){
    log "========== MENJALANKAN ssh =========="
    clear
    print_install "Memasang Password SSH"
    log "Mengunduh konfigurasi common-password..."
    wget -O /etc/pam.d/common-password "${REPO}files/password" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh common-password."
    chmod 644 /etc/pam.d/common-password # Perbaiki permission
    log "Permission common-password diatur ke 644."
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure keyboard-configuration >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal mengkonfigurasi keyboard secara non-interaktif."
    # Konfigurasi keyboard (dibiarkan seperti asli karena kompleks)
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/altgr select The default for the keyboard layout" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/compose select No compose key" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/ctrl_alt_bksp boolean false" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/layoutcode string de" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/layout select English" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/modelcode string pc105" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/model select Generic 105-key (Intl) PC" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/optionscode string " >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/store_defaults_in_debconf_db boolean true" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/switch select No temporary switch" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/toggle select No toggling" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_config_layout boolean true" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_config_options boolean true" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_layout boolean true" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_options boolean true" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variantcode string " >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variant select English" >> "$LOG_FILE" 2>&1
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/xkb-keymap select " >> "$LOG_FILE" 2>&1
    cd
    # Perbaiki konfigurasi rc-local service
    cat > /etc/systemd/system/rc-local.service <<-END
[Unit]
Description=/etc/rc.local Compatibility
ConditionPathExists=/etc/rc.local
[Service]
Type=forking
ExecStart=/etc/rc.local start
TimeoutSec=0
StandardOutput=tty
RemainAfterExit=yes
SysVStartPriority=99
[Install]
WantedBy=multi-user.target
END
    # Perbaiki isi /etc/rc.local
    cat > /etc/rc.local <<-END
#!/bin/sh -e
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.
exit 0
END
    chmod +x /etc/rc.local
    systemctl enable rc-local >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan rc-local service."
    systemctl start rc-local.service >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memulai rc-local service."
    echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6
    sed -i '$ i\echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' /etc/rc.local
    ln -fs /usr/share/zoneinfo/Asia/Jakarta /etc/localtime
    sed -i 's/AcceptEnv/#AcceptEnv/g' /etc/ssh/sshd_config # Komentar baris AcceptEnv
    log "Konfigurasi SSH dasar selesai."
    print_success "Password SSH"
    log "========== ssh SELESAI =========="
}
function udp_mini(){
    log "========== MENJALANKAN udp_mini =========="
    clear
    print_install "Memasang Service limit Quota"
    log "Mengunduh dan menjalankan limit.sh..."
    # Perbaiki URL wget
    if wget -O /root/limit.sh "${REPO}files/limit.sh" && chmod +x /root/limit.sh && /root/limit.sh >> "$LOG_FILE" 2>&1; then
        log "limit.sh berhasil dijalankan."
    else
        log "WARNING: limit.sh gagal atau menyebabkan masalah."
    fi
    cd
    log "Mengunduh limit-ip..."
    wget -q -O /usr/bin/limit-ip "${REPO}files/limit-ip" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh limit-ip."
    # Perbaiki chmod agar tidak memberi execute pada semua file di /usr/bin
    chmod +x /usr/bin/limit-ip
    # chmod +x /usr/bin/* # Baris ini berpotensi bahaya dan dihapus
    cd /usr/bin
    sed -i 's/\r//' limit-ip # Hapus karakter carriage return jika ada
    cd
    clear
    # Perbaiki service unit systemd (ganti ProjectAfter menjadi After, tambah Type)
    cat >/etc/systemd/system/vmip.service << EOF
[Unit]
Description=My VMIP Service
After=network.target
[Service]
Type=simple
WorkingDirectory=/root
ExecStart=/usr/bin/files-ip vmip
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload >> "$LOG_FILE" 2>&1
    systemctl restart vmip >> "$LOG_FILE" 2>&1 || log "INFO: Gagal merestart vmip (mungkin baru dibuat)."
    systemctl enable vmip >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan vmip service."
    cat >/etc/systemd/system/vlip.service << EOF
[Unit]
Description=My VLIP Service
After=network.target
[Service]
Type=simple
WorkingDirectory=/root
ExecStart=/usr/bin/files-ip vlip
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload >> "$LOG_FILE" 2>&1
    systemctl restart vlip >> "$LOG_FILE" 2>&1 || log "INFO: Gagal merestart vlip (mungkin baru dibuat)."
    systemctl enable vlip >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan vlip service."
    cat >/etc/systemd/system/trip.service << EOF
[Unit]
Description=My TRIP Service
After=network.target
[Service]
Type=simple
WorkingDirectory=/root
ExecStart=/usr/bin/files-ip trip
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload >> "$LOG_FILE" 2>&1
    systemctl restart trip >> "$LOG_FILE" 2>&1 || log "INFO: Gagal merestart trip (mungkin baru dibuat)."
    systemctl enable trip >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan trip service."
    mkdir -p /usr/local/kyt/
    log "Mengunduh udp-mini binary..."
    wget -q -O /usr/local/kyt/udp-mini "${REPO}files/udp-mini" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh udp-mini binary."
    chmod +x /usr/local/kyt/udp-mini
    # Perbaiki service unit untuk udp-mini (ganti ProjectAfter menjadi After)
    for i in 1 2 3; do
        log "Mengunduh dan mengkonfigurasi udp-mini-${i}.service..."
        wget -q -O /etc/systemd/system/udp-mini-${i}.service "${REPO}files/udp-mini-${i}.service" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh udp-mini-${i}.service."
        # Opsional: Periksa dan perbaiki isi file service jika perlu
        # sed -i 's/ProjectAfter/After/g' /etc/systemd/system/udp-mini-${i}.service
        systemctl disable "udp-mini-${i}" >> "$LOG_FILE" 2>&1 || log "INFO: Gagal mendisable udp-mini-${i} (mungkin belum aktif)."
        systemctl stop "udp-mini-${i}" >> "$LOG_FILE" 2>&1 || log "INFO: Gagal menghentikan udp-mini-${i} (mungkin belum berjalan)."
        systemctl enable "udp-mini-${i}" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan udp-mini-${i} service."
        systemctl start "udp-mini-${i}" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memulai udp-mini-${i} service."
    done
    print_success "files Quota Service"
    log "========== udp_mini SELESAI =========="
}
function ssh_slow(){
    log "========== MENJALANKAN ssh_slow =========="
    clear
    print_install "Memasang modul SlowDNS Server"
    print_success "SlowDNS"
    log "Modul SlowDNS (placeholder) selesai."
    log "========== ssh_slow SELESAI =========="
}
function ins_SSHD(){
    log "========== MENJALANKAN ins_SSHD =========="
    clear
    print_install "Memasang SSHD"
    log "Mengunduh konfigurasi sshd_config..."
    wget -q -O /etc/ssh/sshd_config "${REPO}files/sshd" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh sshd_config."
    # chmod 700 /etc/ssh/sshd_config # Perbaiki permission yang salah
    chmod 644 /etc/ssh/sshd_config # Gunakan permission yang benar
    log "Permission sshd_config diatur ke 644."
    log "Merestart layanan SSH..."
    # Perbaikan restart ssh/sshd
    systemctl restart ssh >> "$LOG_FILE" 2>&1 || systemctl restart sshd >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan SSH/SSHD."
    # /etc/init.d/ssh status # Tidak perlu, systemctl restart sudah cukup
    print_success "SSHD"
    log "========== ins_SSHD SELESAI =========="
}
function ins_dropbear(){
    log "========== MENJALANKAN ins_dropbear =========="
    clear
    print_install "Menginstall Dropbear"
    log "Memperbarui daftar paket dan menginstal Dropbear..."
    apt-get update -y >> "$LOG_FILE" 2>&1
    apt-get install dropbear -y >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal Dropbear."
    log "Mengunduh konfigurasi Dropbear..."
    wget -q -O /etc/default/dropbear "${REPO}cfg_conf_js/dropbear.conf" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh konfigurasi Dropbear."
    chmod 644 /etc/default/dropbear # Gunakan permission yang benar
    log "Permission konfigurasi Dropbear diatur ke 644."
    log "Merestart layanan Dropbear..."
    systemctl restart dropbear >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan Dropbear."
    # /etc/init.d/dropbear status # Tidak perlu
    print_success "Dropbear"
    log "========== ins_dropbear SELESAI =========="
}
function ins_vnstat(){
    log "========== MENJALANKAN ins_vnstat =========="
    clear
    print_install "Menginstall Vnstat"
    log "Menginstal vnstat dari repositori..."
    apt -y install vnstat >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal vnstat dari repositori."
    # /etc/init.d/vnstat restart # Gunakan systemctl
    log "Memeriksa versi vnstat..."
    VNSTAT_VERSION=$(vnstat --version 2>/dev/null | head -n1 | awk '{print $2}' | cut -d'.' -f1-2)
    REQUIRED_VERSION="2.6"
    VERSION_OK=$(awk -v ver="$VNSTAT_VERSION" -v req="$REQUIRED_VERSION" 'BEGIN { print (ver >= req) }')
    if [[ $VERSION_OK -eq 1 ]]; then
        log "Vnstat versi $VNSTAT_VERSION sudah cukup."
    else
        log "Vnstat versi $VNSTAT_VERSION lebih lama dari $REQUIRED_VERSION. Mengkompilasi dari sumber..."
        apt install -y libsqlite3-dev build-essential >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal dependensi build untuk vnstat."
        cd /tmp || exit 1
        wget -O vnstat-2.6.tar.gz https://humdi.net/vnstat/vnstat-2.6.tar.gz >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh sumber vnstat."
        tar zxvf vnstat-2.6.tar.gz >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengekstrak sumber vnstat."
        cd vnstat-2.6 || exit 1
        ./configure --prefix=/usr --sysconfdir=/etc && make && make install >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengkompilasi atau menginstal vnstat."
        cd / || exit 1
        rm -rf /tmp/vnstat-2.6*
    fi
    # Tentukan interface jaringan
    NET=$(ip -4 route show default | awk '{print $5}' | head -n1)
    if [[ -z "$NET" ]]; then
       NET="eth0" # Fallback
       log "WARNING: Interface jaringan tidak terdeteksi, menggunakan fallback: $NET"
    fi
    log "Interface jaringan yang digunakan: $NET"
    # Inisialisasi database
    vnstat -u -i "$NET" >> "$LOG_FILE" 2>&1 || log "INFO: Gagal menginisialisasi database vnstat untuk $NET (mungkin sudah ada)."
    # Update konfigurasi
    sed -i "s/Interface \"eth0\"/Interface \"$NET\"/g" /etc/vnstat.conf
    # Set ownership
    chown vnstat:vnstat /var/lib/vnstat -R >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal mengatur ownership untuk /var/lib/vnstat."
    # Enable dan restart service
    systemctl enable vnstat >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan layanan vnstat."
    systemctl restart vnstat >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan vnstat."
    # /etc/init.d/vnstat status # Tidak perlu
    # rm -f /root/vnstat-2.6.tar.gz # Sudah ditangani di blok kompilasi
    # rm -rf /root/vnstat-2.6 # Sudah ditangani di blok kompilasi
    print_success "Vnstat"
    log "========== ins_vnstat SELESAI =========="
}
function ins_openvpn(){
    log "========== MENJALANKAN ins_openvpn =========="
    clear
    print_install "Menginstall OpenVPN"
    log "Mengunduh dan menjalankan skrip instalasi OpenVPN..."
    # Perbaiki URL wget
    wget -O /root/openvpn_setup.sh "${REPO}files/openvpn" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh skrip instalasi OpenVPN."
    chmod +x /root/openvpn_setup.sh
    /root/openvpn_setup.sh >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menjalankan skrip instalasi OpenVPN."
    log "Merestart layanan OpenVPN..."
    systemctl restart openvpn >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan OpenVPN."
    # /etc/init.d/openvpn restart # Gunakan systemctl
    print_success "OpenVPN"
    log "========== ins_openvpn SELESAI =========="
}
function ins_swab(){
    log "========== MENJALANKAN ins_swab =========="
    clear
    print_install "Memasang Swap 1 G"
    gotop_latest="$(curl -s https://api.github.com/repos/xxxserxxx/gotop/releases | grep tag_name | sed -E 's/.*"v(.*)".*/\1/' | head -n 1)"
    gotop_link="https://github.com/xxxserxxx/gotop/releases/download/v$gotop_latest/gotop_v"$gotop_latest"_linux_amd64.deb"
    log "Mengunduh gotop versi $gotop_latest..."
    curl -sL "$gotop_link" -o /tmp/gotop.deb >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh gotop."
    dpkg -i /tmp/gotop.deb >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal gotop."
    log "Membuat file swap..."
    # Gunakan fallocate jika dd gagal
    if ! dd if=/dev/zero of=/swapfile bs=1024 count=1048576 >> "$LOG_FILE" 2>&1; then
        log "dd gagal, mencoba fallocate..."
        if ! fallocate -l 1G /swapfile >> "$LOG_FILE" 2>&1; then
            log "ERROR: Gagal membuat file swap dengan dd dan fallocate."
        else
            log "fallocate berhasil."
        fi
    fi
    mkswap /swapfile >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal membuat swap space."
    chown root:root /swapfile >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal mengatur ownership file swap."
    chmod 0600 /swapfile >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal mengatur permission file swap."
    swapon /swapfile >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan swap."
    # Tambahkan ke fstab dengan pengecekan duplikat
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab || log "ERROR: Gagal menambahkan swap ke /etc/fstab."
    log "Menyinkronkan waktu dengan chrony..."
    chronyd -q 'server 0.id.pool.ntp.org iburst' >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menyinkronkan waktu dengan chrony."
    chronyc sourcestats -v >> "$LOG_FILE" 2>&1
    chronyc tracking -v >> "$LOG_FILE" 2>&1
    log "Mengunduh dan menjalankan bbr.sh..."
    # Perbaiki URL wget
    wget -O /root/bbr.sh "${REPO}files/bbr.sh" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh bbr.sh."
    chmod +x /root/bbr.sh
    /root/bbr.sh >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menjalankan bbr.sh."
    print_success "Swap 1 G"
    log "========== ins_swab SELESAI =========="
}
function ins_Fail2ban(){
    log "========== MENJALANKAN ins_Fail2ban =========="
    clear
    print_install "Menginstall Fail2ban"
    # Periksa dan hapus direktori konflik
    if [ -d '/usr/local/ddos' ]; then
        echo; echo; echo "Please un-install the previous DDOS version first"
        log "ERROR: Direktori /usr/local/ddos ditemukan. Instalasi dibatalkan."
        exit 1 # Keluar dengan error code jika ada konflik
    else
        mkdir -p /usr/local/ddos # Buat direktori jika tidak ada
        log "Direktori /usr/local/ddos dibuat."
    fi
    # Instal fail2ban dari repo
    log "Menginstal Fail2ban..."
    apt install -y fail2ban >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal Fail2ban."
    # Setup banner
    echo "Banner /etc/banner.txt" >>/etc/ssh/sshd_config
    sed -i 's@^DROPBEAR_BANNER=.*@DROPBEAR_BANNER="/etc/banner.txt"@g' /etc/default/dropbear # Perbaiki regex
    log "Mengunduh banner..."
    wget -O /etc/banner.txt "${REPO}banner/issue.net" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh banner."
    print_success "Fail2ban"
    log "========== ins_Fail2ban SELESAI =========="
}
function ins_epro(){
    log "========== MENJALANKAN ins_epro =========="
    clear
    print_install "Menginstall ePro WebSocket Proxy"
    log "Mengunduh komponen ePro WebSocket Proxy..."
    wget -O /usr/bin/ws "${REPO}files/ws" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh ws binary."
    wget -O /usr/bin/tun.conf "${REPO}cfg_conf_js/tun.conf" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh tun.conf."
    wget -O /etc/systemd/system/ws.service "${REPO}files/ws.service" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh ws.service."
    chmod +x /etc/systemd/system/ws.service
    chmod +x /usr/bin/ws
    chmod 644 /usr/bin/tun.conf # Permission untuk file konfigurasi
    log "Mengelola layanan ws..."
    systemctl disable ws >> "$LOG_FILE" 2>&1 || log "INFO: Gagal mendisable layanan ws (mungkin belum aktif)."
    systemctl stop ws >> "$LOG_FILE" 2>&1 || log "INFO: Gagal menghentikan layanan ws (mungkin belum berjalan)."
    systemctl enable ws >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan layanan ws."
    systemctl start ws >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memulai layanan ws."
    # systemctl restart ws # Tidak perlu restart jika sudah start
    # Unduh GeoIP/GeoSite data
    log "Mengunduh data GeoIP dan GeoSite..."
    wget -q -O /usr/local/share/xray/geosite.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh geosite.dat."
    wget -q -O /usr/local/share/xray/geoip.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh geoip.dat."
    log "Mengunduh ftvpn binary..."
    wget -O /usr/sbin/ftvpn "${REPO}files/ftvpn" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh ftvpn binary."
    chmod +x /usr/sbin/ftvpn
    # Aturan iptables untuk BitTorrent (dibiarkan seperti asli)
    log "Menerapkan aturan iptables untuk memblokir BitTorrent..."
    iptables -A FORWARD -m string --string "get_peers" --algo bm -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 1."
    iptables -A FORWARD -m string --string "announce_peer" --algo bm -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 2."
    iptables -A FORWARD -m string --string "find_node" --algo bm -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 3."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 4."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent protocol" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 5."
    iptables -A FORWARD -m string --algo bm --string "peer_id=" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 6."
    iptables -A FORWARD -m string --algo bm --string ".torrent" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 7."
    iptables -A FORWARD -m string --algo bm --string "announce.php?passkey=" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 8."
    iptables -A FORWARD -m string --algo bm --string "torrent" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 9."
    iptables -A FORWARD -m string --algo bm --string "announce" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 10."
    iptables -A FORWARD -m string --algo bm --string "info_hash" -j DROP >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan aturan iptables 11."
    # Simpan dan muat ulang aturan
    log "Menyimpan dan memuat ulang aturan iptables..."
    iptables-save > /etc/iptables.up.rules >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menyimpan aturan iptables."
    iptables-restore -t < /etc/iptables.up.rules >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memuat ulang aturan iptables."
    # Gunakan netfilter-persistent untuk Debian 12+
    if command -v netfilter-persistent &> /dev/null; then
        netfilter-persistent save >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menyimpan konfigurasi netfilter."
        netfilter-persistent reload >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memuat ulang konfigurasi netfilter."
    else
        # Fallback ke iptables-persistent jika netfilter-persistent tidak ada
        iptables-persistent save >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menyimpan konfigurasi iptables-persistent."
        iptables-persistent reload >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memuat ulang konfigurasi iptables-persistent."
    fi
    cd
    apt autoclean -y >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menjalankan autoclean."
    apt autoremove -y >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menjalankan autoremove."
    print_success "ePro WebSocket Proxy"
    log "========== ins_epro SELESAI =========="
}
function ins_restart(){
    log "========== MENJALANKAN ins_restart =========="
    clear
    print_install "Restarting All Services"
    # Restart services menggunakan systemctl
    log "Merestart layanan..."
    systemctl daemon-reload >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memuat ulang daemon systemd."
    for svc in nginx ssh sshd dropbear fail2ban vnstat haproxy cron netfilter-persistent ws xray; do
         log "Merestart layanan: $svc"
         systemctl restart "$svc" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan $svc."
    done
    # Enable services
    log "Mengaktifkan layanan..."
    for svc in nginx ssh sshd dropbear fail2ban vnstat cron haproxy netfilter-persistent ws xray rc-local; do
        log "Mengaktifkan layanan: $svc"
        systemctl enable "$svc" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan layanan $svc."
    done
    # Enable OpenVPN jika ada unit servicenya
    if systemctl list-unit-files | grep -q '^openvpn'; then
        log "Mengaktifkan layanan OpenVPN..."
        systemctl enable openvpn >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan layanan OpenVPN."
        systemctl restart openvpn >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart layanan OpenVPN."
    fi
    # Clear history
    history -c
    echo "unset HISTFILE" >> /etc/profile
    # Cleanup downloaded files
    cd
    rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh
    log "File sementara dihapus."
    print_success "All Services"
    log "========== ins_restart SELESAI =========="
}
function menu(){
    log "========== MENJALANKAN menu =========="
    clear
    print_install "Memasang Menu Packet"
    log "Mengunduh dan mengekstrak menu..."
    # Perbaiki URL wget
    wget -O /root/menu.zip "${REPO}Features/menu.zip" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh menu.zip."
    unzip menu.zip >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengekstrak menu.zip."
    chmod +x menu/*
    mv menu/* /usr/local/sbin/
    rm -rf menu /root/menu.zip
    log "Menu dipindahkan ke /usr/local/sbin."
    print_success "Menu Packet"
    log "========== menu SELESAI =========="
}
function profile(){
    log "========== MENJALANKAN profile =========="
    clear
    print_install "Setting up Profile and Cron Jobs"
    # Setup .profile
    cat >/root/.profile <<EOF
# ~/.profile: executed by Bourne-compatible login shells.
if [ "\$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi
mesg n || true
# Run menu on login
menu
EOF
    chmod 644 /root/.profile
    log ".profile root diperbarui."
    # Tambahkan cron jobs (menggunakan crontab alih-alih menulis langsung ke /etc/crontab)
    # Backup cron (asumsi bot-backup script ada)
    log "Menambahkan cron job untuk backup..."
    (crontab -l 2>/dev/null; echo "0 0 * * * root bot-backup") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job backup."
    # Expire check (asumsi xp script ada)
    log "Menambahkan cron job untuk pengecekan expire..."
    (crontab -l 2>/dev/null; echo "0 3 * * * root xp") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job expire."
    # Clean lock (asumsi clean_lock.sh script ada)
    log "Menambahkan cron job untuk pembersihan lock..."
    (crontab -l 2>/dev/null; echo "0 3 */3 * * root clean_lock.sh >> /var/log/reset_xray_lock.log 2>&1") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job clean lock."
    # Log cleaning
    log "Menambahkan cron job untuk pembersihan log..."
    (crontab -l 2>/dev/null; echo "*/10 * * * * root /usr/local/sbin/clearlog") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job clearlog."
    # Daily reboot (akan dihapus dan diganti dengan prompt)
    log "Menambahkan cron job untuk reboot harian..."
    (crontab -l 2>/dev/null; echo "9 3 * * * root /sbin/reboot") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job reboot."
    # Nginx log rotation
    log "Menambahkan cron job untuk rotasi log Nginx..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/nginx/access.log") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job rotasi log Nginx."
    # Xray log rotation
    log "Menambahkan cron job untuk rotasi log Xray..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/xray/access.log") | crontab - >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menambahkan cron job rotasi log Xray."
    # Add shells
    echo "/bin/false" >>/etc/shells
    echo "/usr/sbin/nologin" >>/etc/shells
    log "Shell /bin/false dan /usr/sbin/nologin ditambahkan ke /etc/shells."
    # Setup rc.local for iptables rules on boot
    cat >/etc/rc.local <<EOF
#!/bin/sh -e
# rc.local for additional boot-time commands
# Redirect DNS port 53 to 5300 for UDP Mini
iptables -I INPUT -p udp --dport 5300 -j ACCEPT
iptables -t nat -I PREROUTING -p udp --dport 53 -j REDIRECT --to-ports 5300
# Restart netfilter-persistent to apply rules if needed
systemctl restart netfilter-persistent 2>/dev/null
exit 0
EOF
    chmod +x /etc/rc.local
    log "/etc/rc.local diperbarui."
    # Determine reboot time format (logic kept as is)
    AUTOREB=$(cat /home/daily_reboot 2>/dev/null || echo "5") # Default to 5 if file not found
    SETT=11
    if [ "$AUTOREB" -gt "$SETT" ]; then
        TIME_DATE="PM"
    else
        TIME_DATE="AM"
    fi
    log "Waktu reboot harian: $AUTOREB (format: $TIME_DATE)"
    print_success "Profile and Cron Jobs"
    log "========== profile SELESAI =========="
}
function enable_services(){
    log "========== MENJALANKAN enable_services =========="
    clear
    print_install "Enable Core Services"
    log "Mengaktifkan layanan inti..."
    systemctl daemon-reload >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memuat ulang daemon systemd."
    systemctl start netfilter-persistent >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal memulai netfilter-persistent."
    systemctl enable --now rc-local >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan rc-local."
    systemctl enable --now cron >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan cron."
    systemctl enable --now netfilter-persistent >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengaktifkan netfilter-persistent."
    systemctl restart nginx >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart nginx."
    systemctl restart xray >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart xray."
    systemctl restart cron >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart cron."
    systemctl restart haproxy >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal merestart haproxy."
    print_success "Enable Core Services"
    clear
    log "========== enable_services SELESAI =========="
}
function ins_backup() {
    log "========== MENJALANKAN ins_backup =========="
    clear
    print_install "Memasang Backup Server"
    # Cek apakah wondershaper sudah terinstal via package manager
    # Sudah dilakukan di awal skrip
    # Instal rclone
    log "Menginstal rclone..."
    apt install -y rclone >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal rclone."
    # Konfigurasi rclone (non-interaktif, lalu timpa)
    log "Mengkonfigurasi rclone (non-interaktif)..."
    printf "q
" | rclone config >> "$LOG_FILE" 2>&1 # Ini hanya keluar dari config
    log "Mengunduh konfigurasi rclone..."
    wget -O /root/.config/rclone/rclone.conf "${REPO}cfg_conf_js/rclone.conf" >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal mengunduh konfigurasi rclone."
    # Buat placeholder file
    touch /home/files
    log "File placeholder /home/files dibuat."
    # Instal utilitas mail
    log "Menginstal utilitas mail..."
    apt install -y msmtp-mta ca-certificates bsd-mailx >> "$LOG_FILE" 2>&1 || log "ERROR: Gagal menginstal utilitas mail."
    # Konfigurasi msmtp (PERINGATAN: Kredensial ter-hardcode!)
    log "Mengkonfigurasi msmtp (PERINGATAN: Kredensial ter-hardcode!)..."
    cat >/etc/msmtprc << EOF
# --- PERINGATAN: Kredensial Gmail Ter-Hardcode ---
# --- Harap edit file ini dengan kredensial Anda sendiri ---
defaults
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
account default
host smtp.gmail.com
port 587
auth on
user oceantestdigital@gmail.com
from oceantestdigital@gmail.com
password jokerman77 # <-- RISIKO KEAMANAN: Password Ter-Hardcode
logfile ~/.msmtp.log
EOF
    chown root:root /etc/msmtprc
    chmod 600 /etc/msmtprc # Permission aman untuk file konfigurasi
    log "Konfigurasi msmtp diperbarui dan permission diatur ke 600."
    # Unduh dan jalankan ipserver script (asumsi diperlukan)
    log "Mengunduh dan menjalankan ipserver script..."
    wget -q -O /etc/ipserver "${REPO}files/ipserver" >> "$LOG_FILE" 2>&1 && bash /etc/ipserver >> "$LOG_FILE" 2>&1 || log "WARNING: Gagal menjalankan ipserver script."
    print_success "Backup Server"
    log "========== ins_backup SELESAI =========="
}
function password_default() {
    # Fungsi ini kosong dalam skrip asli, mungkin untuk keperluan tertentu nanti
    # Atau bisa diisi dengan konfigurasi password default jika diperlukan
    log "Fungsi password_default dipanggil (kosong)."
    :
}
function restart_system() {
    log "========== MENJALANKAN restart_system =========="
    # Pastikan variabel yang dibutuhkan telah didefinisikan sebelum fungsi ini dipanggil
    domain=$(cat /root/domain 2>/dev/null) # Tangkap error jika file tidak ada
    if [ -z "$domain" ]; then
        log "WARNING: Domain tidak ditemukan untuk notifikasi Telegram."
    fi
    USRSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $2}')
    EXPSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $3}')
    # Format tanggal dan waktu
    DATE_FORMAT=$(date '+%d-%m-%Y')
    TIME_FORMAT=$(date '+%H:%M:%S')
    # Membangun pesan teks
    TEXT="ð     <b>â  ¨ VPS SETUP COMPLETE â  ¨</b> ð     
<b>ð     INFORMATION DETAILS ð     </b>
ð   ¤ ID       : <code>$USRSC</code>
ð     Domain   : <code>$domain</code>
ð     Wildcard : <code>*.$domain</code>
ð     Date     : <code>$DATE_FORMAT</code>
â  ° Time     : <code>$TIME_FORMAT</code>
ð     IP VPS   : <code>$MYIP</code>
â  ³ Exp Sc   : <code>$EXPSC</code>
ð     User     : <code>root</code>
ð     Password : <code>$passwd</code>
ð    ð   ¢ð   ¡ð   §ð    ð    ð   § :
ð   ¬ð   §ð    ð    ð    ð    ð   ¥ð    ð    
â    @WendiVpn
ð   ¬ð   ªð    ð    ð   §ð   ¦ð    ð   £ð   £
â    +6283153170199
<i>Simpan Baik-baik informasi ini tidak akan di kirim Ulang </i>"
    # Membangun reply markup sebagai variabel terpisah untuk kejelasan
    REPLY_MARKUP='{"inline_keyboard":[[{"text":"á´  Ê  á´  á´  Ê  ","url":"https://t.me/wendivpn"},{"text":"Contack","url":"https://wa.me/6283153170199"}]]}'
    # Mengirim pesan melalui curl
    log "Mengirim notifikasi ke Telegram..."
    curl -s --max-time "$TIMES" \
         -d "chat_id=$CHATID" \
         -d "disable_web_page_preview=1" \
         -d "text=$TEXT" \
         -d "parse_mode=html" \
         -d "reply_markup=$REPLY_MARKUP" \
         "$URL" >> "$LOG_FILE" 2>&1
    # Periksa apakah curl berhasil
    if [ $? -ne 0 ]; then
        echo "Gagal mengirim notifikasi ke Telegram."
        log "ERROR: Gagal mengirim notifikasi ke Telegram."
    else
        log "Notifikasi Telegram berhasil dikirim."
    fi
    log "========== restart_system SELESAI =========="
}
# --- Fungsi Utama Install ---
function install(){
    log "========== MENJALANKAN FUNGSI INSTALL UTAMA =========="
    clear
    pasang_domain
    first_setup
    make_folder_xray
    nginx_install
    base_package
    password_default
    pasang_ssl
    install_xray
    ssh
    udp_mini
    ssh_slow
    ins_SSHD
    ins_dropbear
    ins_vnstat
    ins_openvpn
    ins_backup
    ins_swab
    ins_Fail2ban
    ins_epro
    ins_restart
    menu
    profile
    enable_services
    restart_system
    log "========== FUNGSI INSTALL UTAMA SELESAI =========="
}
# --- Bagian Akhir Skrip (ditambah logging) ---
log "========== MEMULAI PROSES INSTALASI =========="
install # Jalankan fungsi install utama
# --- Final Cleanup ---
log "========== MEMULAI FINAL CLEANUP =========="
echo ""
history -c
# Hapus file-file sementara yang spesifik
rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh /root/random.sh /root/menu.zip /root/domain
# Hapus direktori sementara jika ada
# rm -rf /root/menu # Sudah dipindah dan dihapus di fungsi menu
# rm -rf /root/vnstat-2.6* # Sudah ditangani di ins_vnstat
# --- Final Output dan Reboot Bersyarat ---
secs_to_human "$(($(date +%s) - ${start}))"
sudo hostnamectl set-hostname "$username" # Pastikan $username didefinisikan
log "Hostname diatur ke: $username"
# Tampilkan pesan sukses
clear
echo -e ""
echo -e "\033[96m===============================\033[0m"
echo -e "\033[92m        INSTALL SUCCESS\033[0m"
echo -e "\033[96m===============================\033[0m"
echo -e ""
log "========== SETUP SELESAI =========="
log "Sistem akan reboot sekarang."
echo -e "\033[93mSystem setup is complete.\033[0m"
echo -e "\033[93mThe system will NOT reboot automatically.\033[0m"
echo -e "\033[93mPress [Enter] to confirm and reboot the server...\033[0m"
echo -e "\033[93m(Tekan [Enter] untuk konfirmasi dan reboot server...)\033[0m"
# Tunggu input pengguna
read dummy
# Lakukan reboot setelah Enter ditekan
log "Reboot diminta oleh pengguna."
echo "Rebooting the server..."
reboot