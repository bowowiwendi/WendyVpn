#!/bin/bash                         
# Definisi warna
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

clear
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo -e "\033[96;1m                  WENDY VPN TUNNELING\033[0m"
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo ""

# # --- Bagian Password ---
# while true; do
#     echo "Select an option/Pilih opsi:"
#     echo "1. Ubah Password/Change Password"
#     echo "2. or Enter, Lewati/Skip"
#     read -p "Masukkan pilihan/Input option(1/2): " pilihan
#     if [[ "$pilihan" == "1" ]]; then
#         while true; do
#             read -s -p "Password : " passwd
#             echo
#             read -s -p "Konfirmasi Password : " passwd_confirm
#             echo
#             if [[ -n "$passwd" && "$passwd" == "$passwd_confirm" ]]; then
#                 echo "$passwd" > /etc/.password.txt
#                 echo "Password root berhasil diubah."
#                 break
#             else
#                 echo "Password harus diisi dan harus sama. Silakan coba lagi."
#             fi
#         done
#         echo root:$passwd | sudo chpasswd root > /dev/null 2>&1
#         sudo systemctl restart sshd > /dev/null 2>&1
#         break
#     elif [[ "$pilihan" == "2" || -z "$pilihan" ]]; then
#         echo "Proses pengubahan password dilewati."
#         break
#     else
#         echo "Pilihan tidak valid. Silakan coba lagi."
#     fi
# done

# --- Deteksi Arsitektur dan OS ---
if [[ $( uname -m | awk '{print $1}' ) == "x86_64" ]]; then
    echo -e "${OK} Your Architecture Is Supported ( ${green}$( uname -m )${NC} )"
else
    echo -e "${EROR} Your Architecture Is Not Supported ( ${YELLOW}$( uname -m )${NC} )"
    exit 1
fi

OS_ID=$(grep -w ID /etc/os-release | cut -d'=' -f2 | tr -d '"')
OS_NAME=$(grep -w PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '"')
if [[ "$OS_ID" == "ubuntu" ]] || [[ "$OS_ID" == "debian" ]]; then
    echo -e "${OK} Your OS Is Supported ( ${green}$OS_NAME${NC} )"
else
    echo -e "${EROR} Your OS Is Not Supported ( ${YELLOW}$OS_NAME${NC} )"
    exit 1
fi

# --- Deteksi IP ---
ipsaya=$(wget -qO- ipinfo.io/ip)
if [[ -z "$ipsaya" ]]; then
    echo -e "${EROR} IP Address ( ${RED}Not Detected${NC} )"
    exit 1  # <-- Tambahkan exit jika IP tidak terdeteksi
else
    echo -e "${OK} IP Address ( ${green}$ipsaya${NC} )"
fi

echo ""  # Baris kosong sebagai pemisah estetika

# --- Cek Root dan Virtualisasi ---
if [ "${EUID}" -ne 0 ]; then
    echo "You need to run this script as root"
    exit 1
fi
if [ "$(systemd-detect-virt)" == "openvz" ]; then
    echo "OpenVZ is not supported"
    exit 1
fi

# --- SEMUA PENGECEKAN SUDAH LULUS → LANJUTKAN INSTALASI SECARA OTOMATIS ---
echo -e "${GREENBG} ALL CHECKS PASSED. STARTING INSTALLATION... ${FONT}"
sleep 2  # Opsional: beri jeda 2 detik agar pengguna bisa membaca pesan sukses
clear

# --- Pengambilan Data Pengguna ---
rm -f /usr/bin/user
username=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $2}')
if [ -z "$username" ]; then
    echo "WARNING: Username tidak ditemukan untuk IP $MYIP."
else
    echo "$username" >/usr/bin/user
    echo "Username ditemukan: $username"
fi
valid=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $3}')
echo "$valid" >/usr/bin/e
username=$(cat /usr/bin/user)
oid=$(cat /usr/bin/ver)
exp=$(cat /usr/bin/e)
clear

# --- Perhitungan Tanggal ---
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

# --- Definisi Variabel ---
REPO="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/"
start=$(date +%s)
secs_to_human() {
echo "Installation time : $((${1} / 3600)) hours $(((${1} / 60) % 60)) minute's $((${1} % 60)) seconds"
}

# --- Fungsi Helper ---
function print_ok() {
    echo -e "${OK} ${BLUE} $1 ${FONT}"
}

function print_install() {
    echo -e "${green} =============================== ${FONT}"
    echo -e "${YELLOW} # $1 ${FONT}"
    echo -e "${green} =============================== ${FONT}"
    sleep 1
}

function print_error() {
    echo -e "${EROR} ${REDBG} $1 ${FONT}"
}

function print_success() {
    if [[ 0 -eq $? ]]; then
        echo -e "${green} =============================== ${FONT}"
        echo -e "${Green} # $1 berhasil dipasang${FONT}"
        echo -e "${green} =============================== ${FONT}"
        sleep 2
    fi
}

# --- DEFINISIKAN VARIABEL GLOBAL DOMAIN ---
DOMAIN=""

# --- FUNGSI pasang_domain DIMODIFIKASI ---
function pasang_domain() {
    echo "========== MENJALANKAN pasang_domain =========="
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
        read -p "SUBDOMAIN :  " DOMAIN
        DOMAIN="$DOMAIN"
        #echo "IP=" >> /var/lib/kyt/ipvps.conf
        mkdir -p /etc/xray
        echo "$DOMAIN" > /etc/xray/domain
        echo "$DOMAIN" > /root/domain
        echo "$DOMAIN" > /root/scdomain
        echo ""
        print_install "Subdomain/Domain is Used"
        echo "Domain kustom digunakan: $DOMAIN"
        clear
    elif [[ $host == "2" ]]; then
        echo "Mengunduh dan menjalankan random.sh..."
        wget ${REPO}files/random.sh && chmod +x random.sh && ./random.sh || echo "ERROR: Gagal menjalankan random.sh."
        rm -f /root/random.sh
        # Asumsi random.sh menulis domain ke /root/domain
        if [[ -f "/root/domain" ]]; then
            DOMAIN=$(cat /root/domain)
            echo "Domain acak digunakan: $DOMAIN"
        else
            echo "ERROR: random.sh gagal menghasilkan file /root/domain."
            exit 1
        fi
        clear
        print_install "Random Subdomain/Domain is Used"
    else
        host="2"
        print_install "Random Subdomain/Domain is Used"
        echo "Domain acak digunakan (default)."
        # Asumsi random.sh menulis domain ke /root/domain
        if [[ -f "/root/domain" ]]; then
            DOMAIN=$(cat /root/domain)
            echo "Domain acak digunakan: $DOMAIN"
        else
            echo "ERROR: random.sh gagal menghasilkan file /root/domain."
            exit 1
        fi
        clear
    fi
    
    # Pastikan DOMAIN tidak kosong
    if [[ -z "$DOMAIN" ]]; then
        echo "ERROR: Domain tidak bisa didefinisikan. Keluar dari skrip."
        exit 1
    fi
    
    echo "========== pasang_domain SELESAI =========="
}

# --- Fungsi Instalasi Utama ---
function first_setup() {
    echo "========== MENJALANKAN first_setup =========="
    timedatectl set-timezone Asia/Jakarta || echo "WARNING: Gagal mengatur timezone."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
    print_success "Directory Xray"
    # Mendeteksi OS (sudah dilakukan sebelumnya)
    if [[ "$OS_ID" == "ubuntu" ]]; then
        echo "Setup Dependencies $OS_NAME"
        sudo apt update -y
        echo "Installing haproxy from default repo for Ubuntu"
        apt install -y haproxy || echo "ERROR: Gagal menginstal haproxy."
    elif [[ "$OS_ID" == "debian" ]]; then
        echo "Setup Dependencies For OS Is $OS_NAME"
        echo "Installing haproxy from default repo for Debian"
        apt install -y haproxy || echo "ERROR: Gagal menginstal haproxy."
    else
        echo -e "Your OS Is Not Supported ($OS_NAME)"
        exit 1
    fi
    print_success "HAProxy Installation"
    echo "========== first_setup SELESAI =========="
}

function nginx_install() {
    echo "========== MENJALANKAN nginx_install =========="
    if [[ "$OS_ID" == "ubuntu" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        sudo apt install nginx -y || echo "ERROR: Gagal menginstal nginx (Ubuntu)."
    elif [[ "$OS_ID" == "debian" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        apt -y install nginx || echo "ERROR: Gagal menginstal nginx (Debian)."
    else
        echo -e " Your OS Is Not Supported ( ${YELLOW}$OS_NAME${FONT} )"
    fi
    print_success "Nginx Installation"
    echo "========== nginx_install SELESAI =========="
}

function base_package() {
    echo "========== MENJALANKAN base_package =========="
    clear
    print_install "Menginstall Packet Yang Dibutuhkan"
    # Instalasi paket (dikelompokkan untuk logging yang lebih baik)
    echo "Menginstal paket dasar..."
    apt install zip pwgen openssl netcat-openbsd socat cron bash-completion figlet -y || echo "ERROR: Gagal menginstal paket dasar 1."
    echo "Memperbarui dan memutakhirkan sistem..."
    apt update -y
    apt upgrade -y
    apt dist-upgrade -y
    echo "Menginstal dan mengkonfigurasi chrony..."
    sudo apt install -y chrony
    systemctl enable chronyd
    systemctl restart chronyd
    systemctl enable chrony
    systemctl restart chrony
    chronyc sourcestats -v
    chronyc tracking -v
    apt install ntpdate -y || echo "ERROR: Gagal menginstal ntpdate."
    ntpdate pool.ntp.org
    echo "Menginstal utilitas sistem..."
    apt install sudo -y || echo "ERROR: Gagal menginstal sudo."
    sudo apt clean all
    sudo apt autoremove -y
    sudo apt install -y debconf-utils || echo "ERROR: Gagal menginstal debconf-utils."
    echo "Menghapus paket yang tidak diinginkan..."
    sudo apt remove --purge exim4 -y
    sudo apt remove --purge ufw firewalld -y
    echo "Menginstal software-properties-common..."
    sudo apt install -y --no-install-recommends software-properties-common || echo "ERROR: Gagal menginstal software-properties-common."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
    echo "Menginstal paket utama..."
    sudo apt install -y speedtest-cli vnstat libnss3-dev libnspr4-dev pkg-config libpam0g-dev libcap-ng-dev libcap-ng-utils libselinux1-dev libcurl4-nss-dev flex bison make libnss3-tools libevent-dev bc rsyslog dos2unix zlib1g-dev libssl-dev libsqlite3-dev sed dirmngr libxml-parser-perl build-essential gcc g++ python3 htop lsof tar wget curl ruby zip unzip p7zip-full python3-pip libc6 util-linux build-essential msmtp-mta ca-certificates bsd-mailx iptables iptables-persistent net-tools openssl ca-certificates gnupg gnupg2 ca-certificates lsb-release gcc shc make cmake git screen socat xz-utils apt-transport-https dnsutils cron bash-completion ntpdate chrony jq easy-rsa || echo "ERROR: Gagal menginstal paket utama."
    sudo apt install -y netfilter-persistent
    print_success "Packet Yang Dibutuhkan"
    echo "========== base_package SELESAI =========="
}


function pasang_ssl() {
    echo "========== MENJALANKAN pasang_ssl =========="
    clear
    print_install "Memasang SSL Pada Domain"
    rm -rf /etc/xray/xray.key
    rm -rf /etc/xray/xray.crt
    domain="$DOMAIN"
    echo "Domain untuk SSL: $domain"
    STOPWEBSERVER=$(lsof -i:80 | cut -d' ' -f1 | awk 'NR==2 {print $1}')
    rm -rf /root/.acme.sh
    mkdir /root/.acme.sh
    echo "Menghentikan layanan web sementara..."
    systemctl stop $STOPWEBSERVER || echo "INFO: Gagal menghentikan $STOPWEBSERVER (mungkin tidak berjalan)."
    systemctl stop nginx || echo "INFO: Gagal menghentikan nginx (mungkin tidak berjalan)."
    echo "Mengunduh dan menjalankan acme.sh..."
    curl https://acme-install.netlify.app/acme.sh -o /root/.acme.sh/acme.sh || echo "ERROR: Gagal mengunduh acme.sh."
    chmod +x /root/.acme.sh/acme.sh
    /root/.acme.sh/acme.sh --upgrade --auto-upgrade || echo "WARNING: Gagal memutakhirkan acme.sh."
    /root/.acme.sh/acme.sh --set-default-ca --server letsencrypt || echo "ERROR: Gagal mengatur CA default untuk acme.sh."
    echo "Menerbitkan sertifikat SSL..."
    /root/.acme.sh/acme.sh --issue -d $domain --standalone -k ec-256 || echo "ERROR: Gagal menerbitkan sertifikat SSL untuk $domain."
    ~/.acme.sh/acme.sh --installcert -d $domain --fullchainpath /etc/xray/xray.crt --keypath /etc/xray/xray.key --ecc || echo "ERROR: Gagal menginstal sertifikat SSL untuk $domain."
    chmod 644 /etc/xray/xray.key # Perbaikan permission
    echo "Permission key diatur ke 644."
    print_success "SSL Certificate"
    echo "========== pasang_ssl SELESAI =========="
}

function make_folder_xray() {
    echo "========== MENJALANKAN make_folder_xray =========="
    rm -rf /etc/vmess/.vmess.db
    rm -rf /etc/vless/.vless.db
    rm -rf /etc/trojan/.trojan.db
    rm -rf /etc/shadowsocks/.shadowsocks.db
    rm -rf /etc/ssh/.ssh.db
    rm -rf /etc/bot/.bot.db
    mkdir -p /etc/bot
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
    echo "Folder dan file Xray berhasil dibuat."
    echo "========== make_folder_xray SELESAI =========="
}

function install_xray() {
    echo "========== MENJALANKAN install_xray =========="
    clear
    print_install "Core Xray 25.1.30"

    # --- Konfigurasi Versi Stabil ---
    XRAY_VERSION="v25.1.30"  # ← Ganti dengan versi stabil yang diuji

    domainSock_dir="/run/xray"
    ! [ -d "$domainSock_dir" ] && mkdir "$domainSock_dir"
    chown www-data.www-data "$domainSock_dir"

    echo "Memaksa menginstal Xray versi: $XRAY_VERSION"

    # Instalasi Xray dengan versi spesifik
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" \
        @ install -u www-data --version "$XRAY_VERSION" || {
            echo "❌ ERROR: Gagal menginstal Xray versi $XRAY_VERSION"
            exit 1
        }

    # Verifikasi instalasi
    echo "Memverifikasi versi Xray..."
    /usr/local/bin/xray version

    # Unduh konfigurasi
    wget -O /etc/xray/config.json "${REPO}cfg_conf_js/config.json" || echo "ERROR: Gagal mengunduh config.json"
    wget -O /etc/systemd/system/runn.service "${REPO}files/runn.service" || echo "ERROR: Gagal mengunduh runn.service"

    # Gunakan sumber kebenaran DOMAIN dan IPVS
    domain="$DOMAIN"
    IPVS="$ipsaya"

    print_success "Core Xray $XRAY_VERSION"
    clear

    curl -s ipinfo.io/city >>/etc/xray/city
    curl -s ipinfo.io/org | cut -d " " -f 2-10 >>/etc/xray/isp

    print_install "Memasang Konfigurasi Packet"

    # HAProxy & Nginx
    wget -O /etc/haproxy/haproxy.cfg "${REPO}cfg_conf_js/haproxy.cfg"
    wget -O /etc/nginx/conf.d/xray.conf "${REPO}cfg_conf_js/xray.conf"
    sed -i "s/xxx/${domain}/g" /etc/haproxy/haproxy.cfg
    sed -i "s/xxx/${domain}/g" /etc/nginx/conf.d/xray.conf
    curl "${REPO}cfg_conf_js/nginx.conf" > /etc/nginx/nginx.conf
    cat /etc/xray/xray.crt /etc/xray/xray.key | tee /etc/haproxy/hap.pem

    chmod +x /etc/systemd/system/runn.service
    rm -rf /etc/systemd/system/xray.service.d

    # Service systemd
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
    echo "========== install_xray SELESAI =========="
}

function ssh(){
    echo "========== MENJALANKAN ssh =========="
    clear
    print_install "Memasang Password SSH"
    echo "Mengunduh konfigurasi common-password..."
    wget -O /etc/pam.d/common-password "${REPO}files/password" || echo "ERROR: Gagal mengunduh common-password."
    chmod 644 /etc/pam.d/common-password # Perbaiki permission
    echo "Permission common-password diatur ke 644."
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure keyboard-configuration || echo "WARNING: Gagal mengkonfigurasi keyboard secara non-interaktif."
    # Konfigurasi keyboard (dibiarkan seperti asli karena kompleks)
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/altgr select The default for the keyboard layout"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/compose select No compose key"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/ctrl_alt_bksp boolean false"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/layoutcode string de"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/layout select English"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/modelcode string pc105"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/model select Generic 105-key (Intl) PC"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/optionscode string "
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/store_defaults_in_debconf_db boolean true"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/switch select No temporary switch"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/toggle select No toggling"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_config_layout boolean true"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_config_options boolean true"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_layout boolean true"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/unsupported_options boolean true"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variantcode string "
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variant select English"
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/xkb-keymap select "
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
    systemctl enable rc-local || echo "ERROR: Gagal mengaktifkan rc-local service."
    systemctl start rc-local.service || echo "ERROR: Gagal memulai rc-local service."
    echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6
    sed -i '$ i\echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' /etc/rc.local
    ln -fs /usr/share/zoneinfo/Asia/Jakarta /etc/localtime
    sed -i 's/AcceptEnv/#AcceptEnv/g' /etc/ssh/sshd_config # Komentar baris AcceptEnv
    echo "Konfigurasi SSH dasar selesai."
    print_success "Password SSH"
    echo "========== ssh SELESAI =========="
}

function ssh_slow(){
    echo "========== MENJALANKAN ssh_slow =========="
    clear
    print_install "Memasang modul SlowDNS Server"
    print_success "SlowDNS"
    echo "Modul SlowDNS (placeholder) selesai."
    echo "========== ssh_slow SELESAI =========="
}

function ins_SSHD(){
    echo "========== MENJALANKAN ins_SSHD =========="
    clear
    print_install "Memasang SSHD"
    echo "Mengunduh konfigurasi sshd_config..."
    wget -q -O /etc/ssh/sshd_config "${REPO}files/sshd" || echo "ERROR: Gagal mengunduh sshd_config."
    chmod 644 /etc/ssh/sshd_config # Gunakan permission yang benar
    echo "Permission sshd_config diatur ke 644."
    echo "Merestart layanan SSH..."
    systemctl restart ssh || echo "ERROR: Gagal merestart layanan SSH."
    print_success "SSHD"
    echo "========== ins_SSHD SELESAI =========="
}

function ins_dropbear(){
    echo "========== MENJALANKAN ins_dropbear =========="
    clear
    print_install "Menginstall Dropbear"
    echo "Memperbarui daftar paket dan menginstal Dropbear..."
    apt update -y
    apt install dropbear -y || echo "ERROR: Gagal menginstal Dropbear."
    echo "Mengunduh konfigurasi Dropbear..."
    wget -q -O /etc/default/dropbear "${REPO}cfg_conf_js/dropbear.conf" || echo "ERROR: Gagal mengunduh konfigurasi Dropbear."
    chmod 644 /etc/default/dropbear # Gunakan permission yang benar
    echo "Permission konfigurasi Dropbear diatur ke 644."
    echo "Merestart layanan Dropbear..."
    systemctl restart dropbear || echo "ERROR: Gagal merestart layanan Dropbear."
    print_success "Dropbear"
    echo "========== ins_dropbear SELESAI =========="
}

function ins_vnstat(){
    echo "========== MENJALANKAN ins_vnstat =========="
    clear
    print_install "Menginstall Vnstat"
    echo "Menginstal vnstat dari repositori..."
    apt -y install vnstat || echo "ERROR: Gagal menginstal vnstat dari repositori."
    echo "Memeriksa versi vnstat..."
    VNSTAT_VERSION=$(vnstat --version 2>/dev/null | head -n1 | awk '{print $2}' | cut -d'.' -f1-2)
    REQUIRED_VERSION="2.6"
    VERSION_OK=$(awk -v ver="$VNSTAT_VERSION" -v req="$REQUIRED_VERSION" 'BEGIN { print (ver >= req) }')
    if [[ $VERSION_OK -eq 1 ]]; then
        echo "Vnstat versi $VNSTAT_VERSION sudah cukup."
    else
        echo "Vnstat versi $VNSTAT_VERSION lebih lama dari $REQUIRED_VERSION. Mengkompilasi dari sumber..."
        apt install -y libsqlite3-dev build-essential || echo "ERROR: Gagal menginstal dependensi build untuk vnstat."
        cd /tmp || exit 1
        wget -O vnstat-2.6.tar.gz https://humdi.net/vnstat/vnstat-2.6.tar.gz || echo "ERROR: Gagal mengunduh sumber vnstat."
        tar zxvf vnstat-2.6.tar.gz || echo "ERROR: Gagal mengekstrak sumber vnstat."
        cd vnstat-2.6 || exit 1
        ./configure --prefix=/usr --sysconfdir=/etc && make && make install || echo "ERROR: Gagal mengkompilasi atau menginstal vnstat."
        cd / || exit 1
        rm -rf /tmp/vnstat-2.6*
    fi
    # Tentukan interface jaringan
    NET=$(ip -4 route show default | awk '{print $5}' | head -n1)
    if [[ -z "$NET" ]]; then
       NET="eth0" # Fallback
       echo "WARNING: Interface jaringan tidak terdeteksi, menggunakan fallback: $NET"
    fi
    echo "Interface jaringan yang digunakan: $NET"
    # Inisialisasi database
    vnstat -u -i "$NET" || echo "INFO: Gagal menginisialisasi database vnstat untuk $NET (mungkin sudah ada)."
    # Update konfigurasi
    sed -i "s/Interface \"eth0\"/Interface \"$NET\"/g" /etc/vnstat.conf
    # Set ownership
    chown vnstat:vnstat /var/lib/vnstat -R || echo "WARNING: Gagal mengatur ownership untuk /var/lib/vnstat."
    # Enable dan restart service
    systemctl enable vnstat || echo "ERROR: Gagal mengaktifkan layanan vnstat."
    systemctl restart vnstat || echo "ERROR: Gagal merestart layanan vnstat."
    print_success "Vnstat"
    echo "========== ins_vnstat SELESAI =========="
}

function ins_swab(){
    echo "========== MENJALANKAN ins_swab =========="
    clear
    print_install "Memasang Swap 1 G"
    gotop_latest="$(curl -s https://api.github.com/repos/xxxserxxx/gotop/releases | grep tag_name | sed -E 's/.*"v(.*)".*/\1/' | head -n 1)"
    gotop_link="https://github.com/xxxserxxx/gotop/releases/download/v$gotop_latest/gotop_v"$gotop_latest"_linux_amd64.deb"
    echo "Mengunduh gotop versi $gotop_latest..."
    curl -sL "$gotop_link" -o /tmp/gotop.deb || echo "ERROR: Gagal mengunduh gotop."
    dpkg -i /tmp/gotop.deb || echo "ERROR: Gagal menginstal gotop."
    echo "Membuat file swap..."
    dd if=/dev/zero of=/swapfile bs=1024 count=1048576 || echo "ERROR: Gagal membuat file swap."
    mkswap /swapfile || echo "ERROR: Gagal membuat swap space."
    chown root:root /swapfile || echo "WARNING: Gagal mengatur ownership file swap."
    chmod 0600 /swapfile || echo "WARNING: Gagal mengatur permission file swap."
    swapon /swapfile || echo "ERROR: Gagal mengaktifkan swap."
    # Tambahkan ke fstab dengan pengecekan duplikat
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab || echo "ERROR: Gagal menambahkan swap ke /etc/fstab."
    echo "Menyinkronkan waktu dengan chrony..."
    chronyd -q 'server 0.id.pool.ntp.org iburst' || echo "WARNING: Gagal menyinkronkan waktu dengan chrony."
    chronyc sourcestats -v
    chronyc tracking -v
    echo "Mengunduh dan menjalankan bbr.sh..."
    wget -O /root/bbr.sh "${REPO}files/bbr.sh" || echo "ERROR: Gagal mengunduh bbr.sh."
    chmod +x /root/bbr.sh
    /root/bbr.sh || echo "ERROR: Gagal menjalankan bbr.sh."
    print_success "Swap 1 G"
    echo "========== ins_swab SELESAI =========="
}

function ins_Fail2ban(){
    echo "========== MENJALANKAN ins_Fail2ban =========="
    clear
    print_install "Menginstall Fail2ban"
    # Periksa dan hapus direktori konflik
    if [ -d '/usr/local/ddos' ]; then
        echo; echo; echo "Please un-install the previous DDOS version first"
        exit 1 # Keluar dengan error code jika ada konflik
    else
        mkdir -p /usr/local/ddos # Buat direktori jika tidak ada
        echo "Direktori /usr/local/ddos dibuat."
    fi
    # Instal fail2ban dari repo
    echo "Menginstal Fail2ban..."
    apt install -y fail2ban || echo "ERROR: Gagal menginstal Fail2ban."
    # Setup banner
    echo "Banner /etc/banner.txt" >>/etc/ssh/sshd_config
    sed -i 's@^DROPBEAR_BANNER=.*@DROPBEAR_BANNER="/etc/banner.txt"@g' /etc/default/dropbear # Perbaiki regex
    echo "Mengunduh banner..."
    wget -O /etc/banner.txt "${REPO}banner/issue.net" || echo "ERROR: Gagal mengunduh banner."
    print_success "Fail2ban"
    echo "========== ins_Fail2ban SELESAI =========="
}

function ins_epro(){
    echo "========== MENJALANKAN ins_epro =========="
    clear
    print_install "Menginstall ePro WebSocket Proxy"
    echo "Mengunduh komponen ePro WebSocket Proxy..."
    wget -O /usr/bin/ws "${REPO}files/ws" || echo "ERROR: Gagal mengunduh ws binary."
    wget -O /usr/bin/tun.conf "${REPO}cfg_conf_js/tun.conf" || echo "ERROR: Gagal mengunduh tun.conf."
    wget -O /etc/systemd/system/ws.service "${REPO}files/ws.service" || echo "ERROR: Gagal mengunduh ws.service."
    chmod +x /etc/systemd/system/ws.service
    chmod +x /usr/bin/ws
    chmod 644 /usr/bin/tun.conf # Permission untuk file konfigurasi
    echo "Mengelola layanan ws..."
    systemctl disable ws || echo "INFO: Gagal mendisable layanan ws (mungkin belum aktif)."
    systemctl stop ws || echo "INFO: Gagal menghentikan layanan ws (mungkin belum berjalan)."
    systemctl enable ws || echo "ERROR: Gagal mengaktifkan layanan ws."
    systemctl start ws || echo "ERROR: Gagal memulai layanan ws."
    # Unduh GeoIP/GeoSite data
    echo "Mengunduh data GeoIP dan GeoSite..."
    wget -q -O /usr/local/share/xray/geosite.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" || echo "ERROR: Gagal mengunduh geosite.dat."
    wget -q -O /usr/local/share/xray/geoip.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" || echo "ERROR: Gagal mengunduh geoip.dat."
    echo "Mengunduh ftvpn binary..."
    wget -O /usr/sbin/ftvpn "${REPO}files/ftvpn" || echo "ERROR: Gagal mengunduh ftvpn binary."
    chmod +x /usr/sbin/ftvpn
    # Aturan iptables untuk BitTorrent (dibiarkan seperti asli)
    echo "Menerapkan aturan iptables untuk memblokir BitTorrent..."
    iptables -A FORWARD -m string --string "get_peers" --algo bm -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 1."
    iptables -A FORWARD -m string --string "announce_peer" --algo bm -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 2."
    iptables -A FORWARD -m string --string "find_node" --algo bm -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 3."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 4."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent protocol" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 5."
    iptables -A FORWARD -m string --algo bm --string "peer_id=" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 6."
    iptables -A FORWARD -m string --algo bm --string ".torrent" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 7."
    iptables -A FORWARD -m string --algo bm --string "announce.php?passkey=" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 8."
    iptables -A FORWARD -m string --algo bm --string "torrent" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 9."
    iptables -A FORWARD -m string --algo bm --string "announce" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 10."
    iptables -A FORWARD -m string --algo bm --string "info_hash" -j DROP || echo "WARNING: Gagal menambahkan aturan iptables 11."
    # Simpan dan muat ulang aturan
    echo "Menyimpan dan memuat ulang aturan iptables..."
    iptables-save > /etc/iptables.up.rules || echo "ERROR: Gagal menyimpan aturan iptables."
    iptables-restore -t < /etc/iptables.up.rules || echo "ERROR: Gagal memuat ulang aturan iptables."
    netfilter-persistent save || echo "ERROR: Gagal menyimpan konfigurasi netfilter."
    netfilter-persistent reload || echo "ERROR: Gagal memuat ulang konfigurasi netfilter."
    cd
    apt autoclean -y || echo "WARNING: Gagal menjalankan autoclean."
    apt autoremove -y || echo "WARNING: Gagal menjalankan autoremove."
    print_success "ePro WebSocket Proxy"
    echo "========== ins_epro SELESAI =========="
}

function ins_restart(){
    echo "========== MENJALANKAN ins_restart =========="
    clear
    print_install "Restarting All Services"
    # Restart services menggunakan systemctl
    echo "Merestart layanan..."
    systemctl daemon-reload || echo "ERROR: Gagal memuat ulang daemon systemd."
    for svc in nginx ssh dropbear fail2ban vnstat haproxy cron netfilter-persistent ws xray; do
         echo "Merestart layanan: $svc"
         systemctl restart "$svc" || echo "ERROR: Gagal merestart layanan $svc."
    done
    # Enable services
    echo "Mengaktifkan layanan..."
    for svc in nginx ssh dropbear fail2ban vnstat cron haproxy netfilter-persistent ws xray rc-local; do
        echo "Mengaktifkan layanan: $svc"
        systemctl enable "$svc" || echo "ERROR: Gagal mengaktifkan layanan $svc."
    done
    # Clear history
    history -c
    echo "unset HISTFILE" >> /etc/profile
    # Cleanup downloaded files
    cd
    rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh
    echo "File sementara dihapus."
    print_success "All Services"
    echo "========== ins_restart SELESAI =========="
}

function menu(){
    echo "========== MENJALANKAN menu =========="
    clear
    print_install "Memasang Menu Packet"
    echo "Mengunduh dan mengekstrak menu..."
    wget -O /root/menu.zip "${REPO}Features/menu.zip" || echo "ERROR: Gagal mengunduh menu.zip."
    unzip menu.zip || echo "ERROR: Gagal mengekstrak menu.zip."
    chmod +x menu/*
    mv menu/* /usr/local/sbin/
    rm -rf menu /root/menu.zip
    echo "Menu dipindahkan ke /usr/local/sbin."
    print_success "Menu Packet"
    echo "========== menu SELESAI =========="
}

function profile(){
    echo "========== MENJALANKAN profile =========="
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
    echo ".profile root diperbarui."
    # Tambahkan cron jobs (menggunakan crontab alih-alih menulis langsung ke /etc/crontab)
    # Backup cron (asumsi bot-backup script ada)
    echo "Menambahkan cron job untuk backup..."
    (crontab -l 2>/dev/null; echo "0 0 * * * root bot-backup") | crontab - || echo "WARNING: Gagal menambahkan cron job backup."
    # Expire check (asumsi xp script ada)
    echo "Menambahkan cron job untuk pengecekan expire..."
    (crontab -l 2>/dev/null; echo "0 3 * * * root xp") | crontab - || echo "WARNING: Gagal menambahkan cron job expire."
    # Clean lock (asumsi clean_lock.sh script ada)
    echo "Menambahkan cron job untuk pembersihan lock..."
    (crontab -l 2>/dev/null; echo "0 3 */3 * * root clean_lock.sh >> /var/log/reset_xray_lock.log 2>&1") | crontab - || echo "WARNING: Gagal menambahkan cron job clean lock."
    # Log cleaning
    echo "Menambahkan cron job untuk pembersihan log..."
    (crontab -l 2>/dev/null; echo "*/10 * * * * root /usr/local/sbin/clearlog") | crontab - || echo "WARNING: Gagal menambahkan cron job clearlog."
    # Daily reboot (akan dihapus dan diganti dengan prompt)
    echo "Menambahkan cron job untuk reboot harian..."
    (crontab -l 2>/dev/null; echo "9 3 * * * root /sbin/reboot") | crontab - || echo "WARNING: Gagal menambahkan cron job reboot."
    # Nginx log rotation
    echo "Menambahkan cron job untuk rotasi log Nginx..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/nginx/access.log") | crontab - || echo "WARNING: Gagal menambahkan cron job rotasi log Nginx."
    # Xray log rotation
    echo "Menambahkan cron job untuk rotasi log Xray..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/xray/access.log") | crontab - || echo "WARNING: Gagal menambahkan cron job rotasi log Xray."
    # Add shells
    echo "/bin/false" >>/etc/shells
    echo "/usr/sbin/nologin" >>/etc/shells
    echo "Shell /bin/false dan /usr/sbin/nologin ditambahkan ke /etc/shells."
    # Setup rc.local for iptables rules on boot
    cat >/etc/rc.local <<EOF
#!/bin/sh -e
# rc.local for additional boot-time commands
# Restart netfilter-persistent to apply rules if needed
systemctl restart netfilter-persistent 2>/dev/null
exit 0
EOF
    chmod +x /etc/rc.local
    echo "/etc/rc.local diperbarui."
    # Determine reboot time format (logic kept as is)
    AUTOREB=$(cat /home/daily_reboot 2>/dev/null || echo "5") # Default to 5 if file not found
    SETT=11
    if [ "$AUTOREB" -gt "$SETT" ]; then
        TIME_DATE="PM"
    else
        TIME_DATE="AM"
    fi
    echo "Waktu reboot harian: $AUTOREB (format: $TIME_DATE)"
    print_success "Profile and Cron Jobs"
    echo "========== profile SELESAI =========="
}

function enable_services(){
    echo "========== MENJALANKAN enable_services =========="
    clear
    print_install "Enable Core Services"
    echo "Mengaktifkan layanan inti..."
    systemctl daemon-reload || echo "ERROR: Gagal memuat ulang daemon systemd."
    systemctl start netfilter-persistent || echo "ERROR: Gagal memulai netfilter-persistent."
    systemctl enable --now rc-local || echo "ERROR: Gagal mengaktifkan rc-local."
    systemctl enable --now cron || echo "ERROR: Gagal mengaktifkan cron."
    systemctl enable --now netfilter-persistent || echo "ERROR: Gagal mengaktifkan netfilter-persistent."
    systemctl restart nginx || echo "ERROR: Gagal merestart nginx."
    systemctl restart xray || echo "ERROR: Gagal merestart xray."
    systemctl restart cron || echo "ERROR: Gagal merestart cron."
    systemctl restart haproxy || echo "ERROR: Gagal merestart haproxy."
    print_success "Enable Core Services"
    clear
    echo "========== enable_services SELESAI =========="
}

function ins_backup() {
    echo "========== MENJALANKAN ins_backup =========="
    clear
    print_install "Memasang Backup Server"
    # Cek apakah wondershaper sudah terinstal via package manager
    if ! command -v wondershaper &> /dev/null; then
        echo "wondershaper tidak ditemukan di paket, mengkompilasi dari sumber..."
        apt install -y git make || echo "ERROR: Gagal menginstal dependensi build untuk wondershaper."
        cd /tmp || exit 1
        git clone https://github.com/magnific0/wondershaper.git || echo "ERROR: Gagal mengkloning repositori wondershaper."
        cd wondershaper || exit 1
        sudo make install || echo "ERROR: Gagal mengkompilasi/menginstal wondershaper."
        cd / || exit 1
        rm -rf /tmp/wondershaper
        echo "wondershaper berhasil dikompilasi dan diinstal."
    else
        echo "wondershaper sudah terinstal via package manager."
    fi
    # Instal rclone
    echo "Menginstal rclone..."
    apt install -y rclone || echo "ERROR: Gagal menginstal rclone."
    # Konfigurasi rclone (non-interaktif, lalu timpa)
    echo "Mengkonfigurasi rclone (non-interaktif)..."
    printf "q
" | rclone config # Ini hanya keluar dari config
    echo "Mengunduh konfigurasi rclone..."
    wget -O /root/.config/rclone/rclone.conf "${REPO}cfg_conf_js/rclone.conf" || echo "ERROR: Gagal mengunduh konfigurasi rclone."
    # Buat placeholder file
    touch /home/files
    echo "File placeholder /home/files dibuat."
    # Instal utilitas mail
    echo "Menginstal utilitas mail..."
    apt install -y msmtp-mta ca-certificates bsd-mailx || echo "ERROR: Gagal menginstal utilitas mail."
    # Konfigurasi msmtp (PERINGATAN: Kredensial ter-hardcode!)
    echo "Mengkonfigurasi msmtp (PERINGATAN: Kredensial ter-hardcode!)..."
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
    echo "Konfigurasi msmtp diperbarui dan permission diatur ke 600."
    # Unduh dan jalankan ipserver script (asumsi diperlukan)
    echo "Mengunduh dan menjalankan ipserver script..."
    wget -q -O /etc/ipserver "${REPO}files/ipserver" && bash /etc/ipserver || echo "WARNING: Gagal menjalankan ipserver script."
    print_success "Backup Server"
    echo "========== ins_backup SELESAI =========="
}

function udp_mini(){
    echo "========== MENJALANKAN udp_mini =========="
    print_install "Memasang Service limit Quota"

    # --- Bagian limit.sh ---
    # Modifikasi untuk Ubuntu 24: Pastikan limit.sh menggunakan netcat-openbsd dan python3
    # Perbaiki URL dengan menambahkan https://
    echo "Mengunduh dan menjalankan limit.sh..."
    wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/limit.sh && chmod +x limit.sh && ./limit.sh
    # Asumsi limit.sh menangani instalasi netcat-openbsd dan dependensi lainnya dengan benar untuk Ubuntu 24
    
    # --- Bagian limit-ip ---
    echo "Mengunduh limit-ip..."
    # Perbaiki URL dengan menambahkan https://
    wget -q -O /usr/bin/limit-ip "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/limit-ip"
    # Perbaiki permission hanya untuk file yang diunduh
    chmod +x /usr/bin/limit-ip
    # Perbaiki line endings jika diperlukan (opsional, tergantung sumber file)
    # sed -i 's/\r$//' /usr/bin/limit-ip 

    # --- Bagian Layanan VMIP/VLIP/TRIP (files-ip) ---
    # Catatan: Pastikan skrip files-ip (yang dipanggil oleh layanan ini) kompatibel dengan Ubuntu 24 (python3, netcat-openbsd)
    echo "Membuat dan mengaktifkan layanan vmip, vlip, trip..."
    for service_name in vmip vlip trip; do
        cat >/etc/systemd/system/${service_name}.service << EOF
[Unit]
Description=My ${service_name^^} Service
After=network.target

[Service]
# Pertimbangkan untuk menggunakan direktori yang lebih sesuai daripada /root
WorkingDirectory=/root 
# Pastikan files-ip ada dan dapat dieksekusi, serta kompatibel (python3, netcat-openbsd)
ExecStart=/usr/bin/files-ip ${service_name}
Restart=always
RestartSec=5
User=root # Atau user non-root yang sesuai jika memungkinkan
# StandardError=journal # Untuk debugging jika diperlukan

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl restart ${service_name}
        systemctl enable ${service_name}
        echo "Layanan ${service_name} dibuat, direstart, dan diaktifkan."
    done

    # --- Bagian UDP-Mini ---
    echo "Membuat direktori dan mengunduh udp-mini..."
    mkdir -p /usr/local/kyt/
    # Perbaiki URL dengan menambahkan https://
    wget -q -O /usr/local/kyt/udp-mini "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/udp-mini"
    chmod +x /usr/local/kyt/udp-mini

    echo "Mengunduh dan mengelola layanan udp-mini..."
    # Unduh file layanan dengan nama yang diharapkan
    # Asumsi nama file di repo adalah udp-mini-1.service, dll.
    for i in {1..3}; do
        # Perbaiki URL dengan menambahkan https://
        wget -q -O /etc/systemd/system/udp-mini-${i}.service "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/udp-mini-${i}.service"
    done

    # Restart dan enable layanan (menggunakan nama yang diunduh dan disimpan)
    for i in {1..3}; do
        systemctl daemon-reload
        systemctl stop udp-mini-${i} 2>/dev/null # Hapus dulu jika ada
        systemctl disable udp-mini-${i} 2>/dev/null # Disable dulu jika ada
        
        # Enable dan start layanan
        systemctl enable udp-mini-${i}
        systemctl start udp-mini-${i}
        
        if systemctl is-active --quiet udp-mini-${i}; then
            echo "Layanan udp-mini-${i} berhasil diaktifkan dan dimulai."
        else
            echo "WARNING: Gagal memulai layanan udp-mini-${i}. Periksa status layanan."
        fi
    done

    print_success "files Quota Service"
    echo "========== udp_mini SELESAI =========="
}

function password_default() {
    # Fungsi ini kosong dalam skrip asli, mungkin untuk keperluan tertentu nanti
    # Atau bisa diisi dengan konfigurasi password default jika diperlukan
    echo "Fungsi password_default dipanggil (kosong)."
    :
}

function restart_system() {
    echo "========== MENJALANKAN restart_system =========="
CHATID="5162695441"
TOKEN_BOT="7117869623:AAHBmgzOUsmHBjcm5TFir9JmaZ_X7ynMoF4"
TIMES=30
    # --- Periksa apakah konfigurasi Telegram tersedia ---
    if [[ -z "$CHATID" || -z "$TOKEN_BOT" ]]; then
        echo "WARNING: Konfigurasi Telegram tidak lengkap (CHATID atau TOKEN_BOT kosong)."
        echo "         Notifikasi Telegram dilewati."
        echo "========== restart_system SELESAI (tanpa notifikasi) =========="
        return 0
    fi

    # Bangun URL API Telegram (Pastikan tidak ada spasi)
    local URL="https://api.telegram.org/bot${TOKEN_BOT}/sendMessage"

    # --- Ambil informasi yang diperlukan ---
    local ipsaya=$(wget -qO- ipinfo.io/ip)
    if [[ -z "$ipsaya" ]]; then
        echo "WARNING: Gagal mendapatkan IP publik."
        ipsaya="Tidak Diketahui"
    fi

    # --- Perbaikan: Ambil domain dari /etc/xray/domain ---
    local domain="$DOMAIN"
    if [ -z "$domain" ]; then
        domain="Tidak Ditemukan"
        echo "WARNING: Domain tidak ditemukan di /etc/xray/domain untuk notifikasi Telegram."
    fi

    # Format tanggal dan waktu
    local DATE_FORMAT=$(date '+%d-%m-%Y')
    local TIME_FORMAT=$(date '+%H:%M:%S')

    # --- Ambil informasi pengguna dan expired dari repo ---
    local USRSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $2}' | head -n 1)
    local EXPSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $3}' | head -n 1)

    # --- Tampilkan Password atau Pesan Placeholder ---
    if [[ -z "$passwd" ]]; then
        local passwd_display="<i>(Tidak diubah/digunakan saat ini)</i>"
    else
        local passwd_display="<code>$passwd</code>"
    fi

    # --- Membangun pesan teks dengan variasi emoji ---
    local TEXT="<b>✅ INSTALASI WENDY VPN SELESAI ✅</b>

🖥️ <b>INFORMASI VPS</b> 🖥️
🆔 <b>ID :</b> <code>$USRSC</code>
🌐 <b>Domain :</b> <code>$domain</code>
🌍 <b>Wildcard :</b> <code>*.$domain</code>
📅 <b>Tanggal :</b> <code>$DATE_FORMAT</code>
🕘 <b>Waktu :</b> <code>$TIME_FORMAT</code>
📡 <b>IP VPS :</b> <code>$ipsaya</code>
⏳ <b>Exp Sc :</b> <code>$EXPSC</code>

🔐 <b>Akun Login</b> 🔐
👤 <b>Username :</b> <code>root</code>
🔑 <b>Password :</b> $passwd_display

💾 <b>Simpan informasi ini baik-baik!</b> 💾
<i>Informasi ini tidak akan dikirim ulang.</i>

📞 <b>Dukungan & Kontak</b> 📞
💬 Telegram: @WendiVpn
📱 WhatsApp: +6283153170199
"

    # --- Membangun reply markup ---
    local REPLY_MARKUP='{"inline_keyboard":[[{"text":"🌐 Website","url":"https://t.me/wendivpn"},{"text":"🛠 Kontak","url":"https://wa.me/6283153170199"}]]}'

    # --- Mengirim pesan melalui curl ---
    echo "Mengirim notifikasi ke Telegram (Chat ID: $CHATID)..."
    local CURL_OUTPUT
    CURL_OUTPUT=$(curl -s --max-time "$TIMES" \
         --data-urlencode "chat_id=$CHATID" \
         -d "disable_web_page_preview=1" \
         --data-urlencode "text=$TEXT" \
         -d "parse_mode=html" \
         --data-urlencode "reply_markup=$REPLY_MARKUP" \
         "$URL" 2>&1) # Redirect stderr ke output untuk debugging jika perlu
    local CURL_EXIT_CODE=$?

    # --- Periksa hasil curl ---
    if [ $CURL_EXIT_CODE -ne 0 ]; then
        echo "❌ Gagal mengirim notifikasi ke Telegram (Exit Code: $CURL_EXIT_CODE)."
        echo "   Output curl: $CURL_OUTPUT"
    else
        # Periksa apakah Telegram mengembalikan error dalam respons JSON (jika jq tersedia)
        if command -v jq >/dev/null 2>&1; then
            if echo "$CURL_OUTPUT" | jq -e .ok > /dev/null 2>&1; then
                if [ "$(echo "$CURL_OUTPUT" | jq -r .ok)" = "true" ]; then
                    echo "✅ Notifikasi Telegram berhasil dikirim."
                else
                    local ERROR_CODE=$(echo "$CURL_OUTPUT" | jq -r .error_code 2>/dev/null || echo "N/A")
                    local DESCRIPTION=$(echo "$CURL_OUTPUT" | jq -r .description 2>/dev/null || echo "N/A")
                    echo "❌ Gagal mengirim notifikasi ke Telegram (API Error)."
                    echo "   Kode Error: $ERROR_CODE"
                    echo "   Deskripsi: $DESCRIPTION"
                fi
            else
                 echo "⚠️ Respons tidak valid dari API Telegram. Mungkin berhasil, tapi periksa Telegram Anda."
                 echo "   Respons: $CURL_OUTPUT"
            fi
        else
            # Jika jq tidak tersedia, lakukan pengecekan dasar
            if echo "$CURL_OUTPUT" | grep -q '"ok":true'; then
                 echo "✅ Notifikasi Telegram berhasil dikirim (berdasarkan output)."
            elif echo "$CURL_OUTPUT" | grep -q '"ok":false'; then
                 echo "❌ Gagal mengirim notifikasi ke Telegram (berdasarkan output)."
                 echo "   Respons: $CURL_OUTPUT"
            else
                 # Tidak ada indikasi jelas sukses/gagal, asumsikan sukses atau beri peringatan
                 echo "⚠️ Respons tidak jelas dari API Telegram. Mungkin berhasil, tapi periksa Telegram Anda."
                 echo "   Respons: $CURL_OUTPUT"
            fi
        fi
    fi
    echo "========== restart_system SELESAI =========="
}


function install_openvpn() {
    echo "========== MENJALANKAN install_openvpn =========="
    print_install "Menginstall OpenVPN"

    # 1. Instal paket OpenVPN dari repositori resmi (Direkomendasikan untuk Ubuntu 24.04)
    echo "Menginstal paket openvpn dari repositori..."
    apt update -y > /dev/null 2>&1 # Pastikan daftar paket terbaru
    apt install -y openvpn || { echo "ERROR: Gagal menginstal paket openvpn."; print_error "OpenVPN (Instalasi Paket)"; echo "========== install_openvpn GAGAL =========="; return 1; }
    print_success "Instalasi Paket OpenVPN"

    # 2. Unduh dan Jalankan Skrip Konfigurasi Kustom
    #    Asumsi: Skrip ini melakukan konfigurasi lanjutan seperti mengekstrak template,
    #            mengatur sertifikat, dan mungkin membuat file konfigurasi di /etc/openvpn/server/
    echo "Mengunduh dan menjalankan skrip konfigurasi kustom..."
    # Perbaiki URL dengan menambahkan https://
    if wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/openvpn -O /root/openvpn_setup.sh; then
        chmod +x /root/openvpn_setup.sh
        if /root/openvpn_setup.sh; then
            echo "Skrip konfigurasi kustom berhasil dijalankan."
        else
            echo "WARNING: Gagal menjalankan skrip konfigurasi kustom (/root/openvpn_setup.sh). Periksa log atau skrip tersebut."
            # Tidak langsung keluar, karena instalasi paket berhasil
        fi
        # Bersihkan skrip sementara
        rm -f /root/openvpn_setup.sh
    else
        echo "WARNING: Gagal mengunduh skrip konfigurasi kustom (openvpn). Konfigurasi dasar mungkin tidak lengkap."
        # Tidak langsung keluar, karena instalasi paket berhasil
    fi

    # 3. Aktifkan dan Restart Layanan OpenVPN menggunakan systemd
    #    Asumsi: Skrip konfigurasi membuat file /etc/openvpn/server/server.conf
    echo "Mengaktifkan dan merestart layanan OpenVPN (server)..."
    
    # Aktifkan layanan agar otomatis start saat boot
    if ! systemctl enable openvpn-server@server; then
        echo "WARNING: Gagal mengaktifkan layanan openvpn-server@server."
    fi

    # Restart layanan untuk menerapkan konfigurasi
    if systemctl restart openvpn-server@server; then
        echo "Layanan openvpn-server@server berhasil direstart."
    else
        echo "WARNING: Gagal merestart layanan openvpn-server@server. Pastikan konfigurasi sudah dibuat dengan benar."
        # Tidak langsung keluar, karena instalasi paket berhasil
    fi

    print_success "OpenVPN"
    echo "========== install_openvpn SELESAI =========="
}

# --- Fungsi Utama Install ---
function install(){
    echo "========== MENJALANKAN FUNGSI INSTALL UTAMA =========="
    clear
    pasang_domain
    first_setup
    base_package
    make_folder_xray
    profile
    password_default
    pasang_ssl
    nginx_install
    install_openvpn
    install_xray
    ssh
    udp_mini
    ssh_slow
    ins_SSHD
    ins_dropbear
    ins_vnstat
    ins_backup
    ins_swab
    ins_Fail2ban
    ins_epro
    menu
    ins_restart
    enable_services
    restart_system
    echo "========== FUNGSI INSTALL UTAMA SELESAI =========="
}

# --- Bagian Akhir Skrip ---
echo "========== MEMULAI PROSES INSTALASI =========="
install # Jalankan fungsi install utama

# --- Final Cleanup ---
echo "========== MEMULAI FINAL CLEANUP =========="
echo ""
history -c
# Hapus file-file sementara yang spesifik
rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh /root/random.sh /root/menu.zip /root/domain
# Hapus direktori sementara jika ada
# --- Final Output dan Reboot Bersyarat ---
secs_to_human "$(($(date +%s) - ${start}))"
sudo hostnamectl set-hostname "$username" # Pastikan $username didefinisikan
echo "Hostname diatur ke: $username"
# Tampilkan pesan sukses
clear
# --- Final Output dan Reboot Otomatis ---
clear
echo -e ""
echo -e "\033[96m===============================\033[0m"
echo -e "\033[92m        INSTALL SUCCESS\033[0m"
echo -e "\033[96m===============================\033[0m"
echo -e ""
echo "========== SETUP SELESAI =========="
echo "Sistem akan reboot sekarang secara otomatis..."
echo -e "\033[93mSystem setup is complete.\033[0m"
echo -e "\033[93mRebooting server in 5 seconds...\033[0m"

# Tunggu 5 detik sebelum reboot (opsional, agar user sempat membaca pesan)
sleep 5

# Reboot otomatis tanpa intervensi
reboot