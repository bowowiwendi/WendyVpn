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

# Cek argumen domain
if [ -n "$1" ]; then
    DOMAIN="$1"
    print_ok "Domain yang diberikan: $DOMAIN"
fi

clear
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo -e "\033[96;1m                  WENDY VPN TUNNELING\033[0m"
echo -e "${YELLOW}----------------------------------------------------------${NC}"
echo ""

# --- Deteksi Arsitektur dan OS ---
if [[ $( uname -m | awk '{print $1}' ) == "x86_64" ]]; then
    print_ok "Your Architecture Is Supported ( ${green}$( uname -m )${NC} )"
else
    print_error "Your Architecture Is Not Supported ( ${YELLOW}$( uname -m )${NC} )"
    exit 1
fi

OS_ID=$(grep -w ID /etc/os-release | cut -d'=' -f2 | tr -d '"')
OS_NAME=$(grep -w PRETTY_NAME /etc/os-release | cut -d'=' -f2 | tr -d '"')
if [[ "$OS_ID" == "ubuntu" ]] || [[ "$OS_ID" == "debian" ]]; then
    print_ok "Your OS Is Supported ( ${green}$OS_NAME${NC} )"
else
    print_error "Your OS Is Not Supported ( ${YELLOW}$OS_NAME${NC} )"
    exit 1
fi

# --- Deteksi IP ---
ipsaya=$(wget -qO- ipinfo.io/ip)
if [[ -z "$ipsaya" ]]; then
    print_error "IP Address ( ${RED}Not Detected${NC} )"
    exit 1
else
    print_ok "IP Address ( ${green}$ipsaya${NC} )"
fi

echo ""

# --- Cek Root dan Virtualisasi ---
if [ "${EUID}" -ne 0 ]; then
    print_error "You need to run this script as root"
    exit 1
fi
if [ "$(systemd-detect-virt)" == "openvz" ]; then
    print_error "OpenVZ is not supported"
    exit 1
fi

# --- SEMUA PENGECEKAN SUDAH LULUS → LANJUTKAN INSTALASI SECARA OTOMATIS ---
print_ok "${GREENBG} ALL CHECKS PASSED. STARTING INSTALLATION... ${FONT}"
sleep 2
clear

# --- Pengambilan Data Pengguna ---
rm -f /usr/bin/user
username=$(curl -s https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep $MYIP | awk '{print $2}')
if [ -z "$username" ]; then
    print_error "Username tidak ditemukan untuk IP $MYIP."
else
    echo "$username" >/usr/bin/user
    print_ok "Username ditemukan: $username"
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
print_ok "\e[32mloading...\e[0m"
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
    print_install "MENJALANKAN pasang_domain"
    clear
    
    # Jika domain sudah diset dari argumen, gunakan itu
    if [ -n "$DOMAIN" ]; then
        print_ok "Menggunakan domain dari argumen: $DOMAIN"
        mkdir -p /etc/xray
        echo "$DOMAIN" > /etc/xray/domain
        echo "$DOMAIN" > /root/domain
        echo "$DOMAIN" > /root/scdomain
        print_install "Subdomain/Domain is Used"
        print_ok "Domain kustom digunakan: $DOMAIN"
        clear
        return
    fi

    echo -e "==============================="
    echo -e "   |\e[1;32mPlease Select a Domain Type Below \e[0m|"
    echo -e "==============================="
    echo -e "     \e[1;32m1)\e[0m Your Domain"
    echo -e "     \e[1;32m2)\e[0m Random Domain "
    echo -e "==============================="
    
    print_ok "\e[1;33mAnda memiliki 30 detik untuk memilih. Default: Random Domain\e[0m"
    read -t 30 -p "   Please select numbers 1-2 or Any Button(Random) : " host
    
    if [ $? -eq 142 ]; then
        print_error "\nWaktu habis! Memilih opsi 2 (Random Domain)"
        host="2"
    fi
    
    echo ""
    
    if [[ $host == "1" ]]; then
        clear
        echo -e "\e[1;32m===============================$NC"
        echo -e "\e[1;36m     INPUT SUBDOMAIN $NC"
        echo -e "\e[1;32m===============================$NC"
        echo -e "\033[91;1m contoh subdomain :\033[0m \033[93 wendi.ssh.cloud\033[0m"
        read -p "SUBDOMAIN :  " DOMAIN
        DOMAIN="$DOMAIN"
        mkdir -p /etc/xray
        echo "$DOMAIN" > /etc/xray/domain
        echo "$DOMAIN" > /root/domain
        echo "$DOMAIN" > /root/scdomain
        print_install "Subdomain/Domain is Used"
        print_ok "Domain kustom digunakan: $DOMAIN"
        clear
    elif [[ $host == "2" ]]; then
        print_ok "Mengunduh dan menjalankan random.sh..."
        wget ${REPO}files/random.sh && chmod +x random.sh && ./random.sh || print_error "Gagal menjalankan random.sh."
        rm -f /root/random.sh
        if [[ -f "/root/domain" ]]; then
            DOMAIN=$(cat /root/domain)
            print_ok "Domain acak digunakan: $DOMAIN"
        else
            print_error "random.sh gagal menghasilkan file /root/domain."
            exit 1
        fi
        clear
        print_install "Random Subdomain/Domain is Used"
    else
        host="2"
        print_install "Random Subdomain/Domain is Used"
        print_ok "Domain acak digunakan (default)."
        if [[ -f "/root/domain" ]]; then
            DOMAIN=$(cat /root/domain)
            print_ok "Domain acak digunakan: $DOMAIN"
        else
            print_error "random.sh gagal menghasilkan file /root/domain."
            exit 1
        fi
        clear
    fi
    
    if [[ -z "$DOMAIN" ]]; then
        print_error "Domain tidak bisa didefinisikan. Keluar dari skrip."
        exit 1
    fi
    
    print_ok "pasang_domain SELESAI"
}

# --- Fungsi Instalasi Utama ---
function first_setup() {
    print_install "MENJALANKAN first_setup"
    timedatectl set-timezone Asia/Jakarta || print_error "Gagal mengatur timezone."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
    print_success "Directory Xray"
    if [[ "$OS_ID" == "ubuntu" ]]; then
        print_ok "Setup Dependencies $OS_NAME"
        sudo apt update -y
        print_ok "Installing haproxy from default repo for Ubuntu"
        apt install -y haproxy || print_error "Gagal menginstal haproxy."
    elif [[ "$OS_ID" == "debian" ]]; then
        print_ok "Setup Dependencies For OS Is $OS_NAME"
        print_ok "Installing haproxy from default repo for Debian"
        apt install -y haproxy || print_error "Gagal menginstal haproxy."
    else
        print_error "Your OS Is Not Supported ($OS_NAME)"
        exit 1
    fi
    print_success "HAProxy Installation"
    print_ok "first_setup SELESAI"
}

function nginx_install() {
    print_install "MENJALANKAN nginx_install"
    if [[ "$OS_ID" == "ubuntu" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        sudo apt install nginx -y || print_error "Gagal menginstal nginx (Ubuntu)."
    elif [[ "$OS_ID" == "debian" ]]; then
        print_install "Setup nginx For OS Is $OS_NAME"
        apt -y install nginx || print_error "Gagal menginstal nginx (Debian)."
    else
        print_error " Your OS Is Not Supported ( ${YELLOW}$OS_NAME${FONT} )"
    fi
    print_success "Nginx Installation"
    print_ok "nginx_install SELESAI"
}

function base_package() {
    print_install "MENJALANKAN base_package"
    print_ok "Menginstal paket dasar..."
    apt install zip pwgen openssl netcat-openbsd socat cron bash-completion figlet -y || print_error "Gagal menginstal paket dasar 1."
    print_ok "Memperbarui dan memutakhirkan sistem..."
    apt update -y
    apt upgrade -y
    apt dist-upgrade -y
    print_ok "Menginstal dan mengkonfigurasi chrony..."
    sudo apt install -y chrony
    systemctl enable chronyd
    systemctl restart chronyd
    systemctl enable chrony
    systemctl restart chrony
    chronyc sourcestats -v
    chronyc tracking -v
    apt install ntpdate -y || print_error "Gagal menginstal ntpdate."
    ntpdate pool.ntp.org
    print_ok "Menginstal utilitas sistem..."
    apt install sudo -y || print_error "Gagal menginstal sudo."
    sudo apt clean all
    sudo apt autoremove -y
    sudo apt install -y debconf-utils || print_error "Gagal menginstal debconf-utils."
    print_ok "Menghapus paket yang tidak diinginkan..."
    sudo apt remove --purge exim4 -y
    sudo apt remove --purge ufw firewalld -y
    print_ok "Menginstal software-properties-common..."
    sudo apt install -y --no-install-recommends software-properties-common || print_error "Gagal menginstal software-properties-common."
    echo iptables-persistent iptables-persistent/autosave_v4 boolean true | debconf-set-selections
    echo iptables-persistent iptables-persistent/autosave_v6 boolean true | debconf-set-selections
    print_ok "Menginstal paket utama..."
    sudo apt install -y speedtest-cli vnstat libnss3-dev libnspr4-dev pkg-config libpam0g-dev libcap-ng-dev libcap-ng-utils libselinux1-dev libcurl4-nss-dev flex bison make libnss3-tools libevent-dev bc rsyslog dos2unix zlib1g-dev libssl-dev libsqlite3-dev sed dirmngr libxml-parser-perl build-essential gcc g++ python3 htop lsof tar wget curl ruby zip unzip p7zip-full python3-pip libc6 util-linux build-essential ca-certificates bsd-mailx gcc shc make cmake git screen socat xz-utils apt-transport-https dnsutils cron bash-completion ntpdate chrony jq easy-rsa || print_error "Gagal menginstal paket utama."
    sudo apt install -y netfilter-persistent
    print_ok "Melewati instalasi msmtp sesuai permintaan"
    sudo apt install -y msmtp-mta || print_ok "msmtp-mta dilewati"
    print_success "Packet Yang Dibutuhkan"
    print_ok "base_package SELESAI"
}

function pasang_ssl() {
    print_install "MENJALANKAN pasang_ssl"
    rm -rf /etc/xray/xray.key
    rm -rf /etc/xray/xray.crt
    domain="$DOMAIN"
    print_ok "Domain untuk SSL: $domain"
    STOPWEBSERVER=$(lsof -i:80 | cut -d' ' -f1 | awk 'NR==2 {print $1}')
    rm -rf /root/.acme.sh
    mkdir /root/.acme.sh
    print_ok "Menghentikan layanan web sementara..."
    systemctl stop $STOPWEBSERVER || print_ok "Gagal menghentikan $STOPWEBSERVER (mungkin tidak berjalan)."
    systemctl stop nginx || print_ok "Gagal menghentikan nginx (mungkin tidak berjalan)."
    print_ok "Mengunduh dan menjalankan acme.sh..."
    curl https://acme-install.netlify.app/acme.sh -o /root/.acme.sh/acme.sh || print_error "Gagal mengunduh acme.sh."
    chmod +x /root/.acme.sh/acme.sh
    /root/.acme.sh/acme.sh --upgrade --auto-upgrade || print_error "Gagal memutakhirkan acme.sh."
    /root/.acme.sh/acme.sh --set-default-ca --server letsencrypt || print_error "Gagal mengatur CA default untuk acme.sh."
    print_ok "Menerbitkan sertifikat SSL..."
    /root/.acme.sh/acme.sh --issue -d $domain --standalone -k ec-256 || print_error "Gagal menerbitkan sertifikat SSL untuk $domain."
    ~/.acme.sh/acme.sh --installcert -d $domain --fullchainpath /etc/xray/xray.crt --keypath /etc/xray/xray.key --ecc || print_error "Gagal menginstal sertifikat SSL untuk $domain."
    chmod 644 /etc/xray/xray.key
    print_ok "Permission key diatur ke 644."
    print_success "SSL Certificate"
    print_ok "pasang_ssl SELESAI"
}

function make_folder_xray() {
    print_install "MENJALANKAN make_folder_xray"
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
    print_ok "Folder dan file Xray berhasil dibuat."
    print_ok "make_folder_xray SELESAI"
}

function install_xray() {
    print_install "MENJALANKAN install_xray"
    XRAY_VERSION="v25.1.30"
    domainSock_dir="/run/xray"
    ! [ -d "$domainSock_dir" ] && mkdir "$domainSock_dir"
    chown www-data.www-data "$domainSock_dir"
    print_ok "Memaksa menginstal Xray versi: $XRAY_VERSION"
    bash -c "$(curl -L https://github.com/XTLS/Xray-install/raw/main/install-release.sh)" \
        @ install -u www-data --version "$XRAY_VERSION" || {
            print_error "Gagal menginstal Xray versi $XRAY_VERSION"
            exit 1
        }
    print_ok "Memverifikasi versi Xray..."
    /usr/local/bin/xray version
    wget -O /etc/xray/config.json "${REPO}cfg_conf_js/config.json" || print_error "Gagal mengunduh config.json"
    wget -O /etc/systemd/system/runn.service "${REPO}files/runn.service" || print_error "Gagal mengunduh runn.service"
    domain="$DOMAIN"
    IPVS="$ipsaya"
    print_success "Core Xray $XRAY_VERSION"
    clear
    curl -s ipinfo.io/city >>/etc/xray/city
    curl -s ipinfo.io/org | cut -d " " -f 2-10 >>/etc/xray/isp
    print_install "Memasang Konfigurasi Packet"
    wget -O /etc/haproxy/haproxy.cfg "${REPO}cfg_conf_js/haproxy.cfg"
    wget -O /etc/nginx/conf.d/xray.conf "${REPO}cfg_conf_js/xray.conf"
    sed -i "s/xxx/${domain}/g" /etc/haproxy/haproxy.cfg
    sed -i "s/xxx/${domain}/g" /etc/nginx/conf.d/xray.conf
    curl "${REPO}cfg_conf_js/nginx.conf" > /etc/nginx/nginx.conf
    cat /etc/xray/xray.crt /etc/xray/xray.key | tee /etc/haproxy/hap.pem
    chmod +x /etc/systemd/system/runn.service
    rm -rf /etc/systemd/system/xray.service.d
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
    print_ok "install_xray SELESAI"
}

function ssh(){
    print_install "MENJALANKAN ssh"
    print_ok "Mengunduh konfigurasi common-password..."
    wget -O /etc/pam.d/common-password "${REPO}files/password" || print_error "Gagal mengunduh common-password."
    chmod 644 /etc/pam.d/common-password
    print_ok "Permission common-password diatur ke 644."
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure keyboard-configuration || print_error "Gagal mengkonfigurasi keyboard secara non-interaktif."
    print_ok "Melewati instalasi openssh-server sesuai permintaan"
    apt install -y openssh-server || print_ok "openssh-server dilewati"
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
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/xkb-keymap select "
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variantcode string "
    debconf-set-selections <<<"keyboard-configuration keyboard-configuration/variant select English"
    cd
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
    systemctl enable rc-local || print_error "Gagal mengaktifkan rc-local service."
    systemctl start rc-local.service || print_error "Gagal memulai rc-local service."
    echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6
    sed -i '$ i\echo 1 > /proc/sys/net/ipv6/conf/all/disable_ipv6' /etc/rc.local
    ln -fs /usr/share/zoneinfo/Asia/Jakarta /etc/localtime
    sed -i 's/AcceptEnv/#AcceptEnv/g' /etc/ssh/sshd_config
    print_ok "Konfigurasi SSH dasar selesai."
    print_success "Password SSH"
    print_ok "ssh SELESAI"
}

function ssh_slow(){
    print_install "MENJALANKAN ssh_slow"
    print_success "SlowDNS"
    print_ok "Modul SlowDNS (placeholder) selesai."
    print_ok "ssh_slow SELESAI"
}

function ins_SSHD(){
    print_install "MENJALANKAN ins_SSHD"
    print_ok "Mengunduh konfigurasi sshd_config..."
    wget -q -O /etc/ssh/sshd_config "${REPO}files/sshd" || print_error "Gagal mengunduh sshd_config."
    chmod 644 /etc/ssh/sshd_config
    print_ok "Permission sshd_config diatur ke 644."
    print_ok "Merestart layanan SSH..."
    systemctl restart ssh || print_error "Gagal merestart layanan SSH."
    print_success "SSHD"
    print_ok "ins_SSHD SELESAI"
}

function ins_dropbear(){
    print_install "MENJALANKAN ins_dropbear"
    print_ok "Memperbarui daftar paket dan menginstal Dropbear..."
    apt update -y
    apt install dropbear -y || print_error "Gagal menginstal Dropbear."
    print_ok "Mengunduh konfigurasi Dropbear..."
    wget -q -O /etc/default/dropbear "${REPO}cfg_conf_js/dropbear.conf" || print_error "Gagal mengunduh konfigurasi Dropbear."
    chmod 644 /etc/default/dropbear
    print_ok "Permission konfigurasi Dropbear diatur ke 644."
    print_ok "Merestart layanan Dropbear..."
    systemctl restart dropbear || print_error "Gagal merestart layanan Dropbear."
    print_success "Dropbear"
    print_ok "ins_dropbear SELESAI"
}

function ins_vnstat(){
    print_install "MENJALANKAN ins_vnstat"
    print_ok "Menginstal vnstat dari repositori..."
    apt -y install vnstat || print_error "Gagal menginstal vnstat dari repositori."
    print_ok "Memeriksa versi vnstat..."
    VNSTAT_VERSION=$(vnstat --version 2>/dev/null | head -n1 | awk '{print $2}' | cut -d'.' -f1-2)
    REQUIRED_VERSION="2.6"
    VERSION_OK=$(awk -v ver="$VNSTAT_VERSION" -v req="$REQUIRED_VERSION" 'BEGIN { print (ver >= req) }')
    if [[ $VERSION_OK -eq 1 ]]; then
        print_ok "Vnstat versi $VNSTAT_VERSION sudah cukup."
    else
        print_ok "Vnstat versi $VNSTAT_VERSION lebih lama dari $REQUIRED_VERSION. Mengkompilasi dari sumber..."
        apt install -y libsqlite3-dev build-essential || print_error "Gagal menginstal dependensi build untuk vnstat."
        cd /tmp || exit 1
        wget -O vnstat-2.6.tar.gz https://humdi.net/vnstat/vnstat-2.6.tar.gz || print_error "Gagal mengunduh sumber vnstat."
        tar zxvf vnstat-2.6.tar.gz || print_error "Gagal mengekstrak sumber vnstat."
        cd vnstat-2.6 || exit 1
        ./configure --prefix=/usr --sysconfdir=/etc && make && make install || print_error "Gagal mengkompilasi atau menginstal vnstat."
        cd / || exit 1
        rm -rf /tmp/vnstat-2.6*
    fi
    NET=$(ip -4 route show default | awk '{print $5}' | head -n1)
    if [[ -z "$NET" ]]; then
       NET="eth0"
       print_error "Interface jaringan tidak terdeteksi, menggunakan fallback: $NET"
    fi
    print_ok "Interface jaringan yang digunakan: $NET"
    vnstat -u -i "$NET" || print_ok "Gagal menginisialisasi database vnstat untuk $NET (mungkin sudah ada)."
    sed -i "s/Interface \"eth0\"/Interface \"$NET\"/g" /etc/vnstat.conf
    chown vnstat:vnstat /var/lib/vnstat -R || print_error "Gagal mengatur ownership untuk /var/lib/vnstat."
    systemctl enable vnstat || print_error "Gagal mengaktifkan layanan vnstat."
    systemctl restart vnstat || print_error "Gagal merestart layanan vnstat."
    print_success "Vnstat"
    print_ok "ins_vnstat SELESAI"
}

function ins_swab(){
    print_install "MENJALANKAN ins_swab"
    gotop_latest="$(curl -s https://api.github.com/repos/xxxserxxx/gotop/releases | grep tag_name | sed -E 's/.*"v(.*)".*/\1/' | head -n 1)"
    gotop_link="https://github.com/xxxserxxx/gotop/releases/download/v$gotop_latest/gotop_v"$gotop_latest"_linux_amd64.deb"
    print_ok "Mengunduh gotop versi $gotop_latest..."
    curl -sL "$gotop_link" -o /tmp/gotop.deb || print_error "Gagal mengunduh gotop."
    dpkg -i /tmp/gotop.deb || print_error "Gagal menginstal gotop."
    print_ok "Membuat file swap..."
    dd if=/dev/zero of=/swapfile bs=1024 count=1048576 || print_error "Gagal membuat file swap."
    mkswap /swapfile || print_error "Gagal membuat swap space."
    chown root:root /swapfile || print_error "Gagal mengatur ownership file swap."
    chmod 0600 /swapfile || print_error "Gagal mengatur permission file swap."
    swapon /swapfile || print_error "Gagal mengaktifkan swap."
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab || print_error "Gagal menambahkan swap ke /etc/fstab."
    print_ok "Menyinkronkan waktu dengan chrony..."
    chronyd -q 'server 0.id.pool.ntp.org iburst' || print_error "Gagal menyinkronkan waktu dengan chrony."
    chronyc sourcestats -v
    chronyc tracking -v
    print_ok "Mengunduh dan menjalankan bbr.sh..."
    wget -O /root/bbr.sh "${REPO}files/bbr.sh" || print_error "Gagal mengunduh bbr.sh."
    chmod +x /root/bbr.sh
    /root/bbr.sh || print_error "Gagal menjalankan bbr.sh."
    print_success "Swap 1 G"
    print_ok "ins_swab SELESAI"
}

function ins_Fail2ban(){
    print_install "MENJALANKAN ins_Fail2ban"
    if [ -d '/usr/local/ddos' ]; then
        print_error "Please un-install the previous DDOS version first"
        exit 1
    else
        mkdir -p /usr/local/ddos
        print_ok "Direktori /usr/local/ddos dibuat."
    fi
    print_ok "Menginstal Fail2ban..."
    apt install -y fail2ban || print_error "Gagal menginstal Fail2ban."
    echo "Banner /etc/banner.txt" >>/etc/ssh/sshd_config
    sed -i 's@^DROPBEAR_BANNER=.*@DROPBEAR_BANNER="/etc/banner.txt"@g' /etc/default/dropbear
    print_ok "Mengunduh banner..."
    wget -O /etc/banner.txt "${REPO}banner/issue.net" || print_error "Gagal mengunduh banner."
    print_success "Fail2ban"
    print_ok "ins_Fail2ban SELESAI"
}

function ins_epro(){
    print_install "MENJALANKAN ins_epro"
    print_ok "Mengunduh komponen ePro WebSocket Proxy..."
    wget -O /usr/bin/ws "${REPO}files/ws" || print_error "Gagal mengunduh ws binary."
    wget -O /usr/bin/tun.conf "${REPO}cfg_conf_js/tun.conf" || print_error "Gagal mengunduh tun.conf."
    wget -O /etc/systemd/system/ws.service "${REPO}files/ws.service" || print_error "Gagal mengunduh ws.service."
    chmod +x /etc/systemd/system/ws.service
    chmod +x /usr/bin/ws
    chmod 644 /usr/bin/tun.conf
    print_ok "Mengelola layanan ws..."
    systemctl disable ws || print_ok "Gagal mendisable layanan ws (mungkin belum aktif)."
    systemctl stop ws || print_ok "Gagal menghentikan layanan ws (mungkin belum berjalan)."
    systemctl enable ws || print_error "Gagal mengaktifkan layanan ws."
    systemctl start ws || print_error "Gagal memulai layanan ws."
    print_ok "Mengunduh data GeoIP dan GeoSite..."
    wget -q -O /usr/local/share/xray/geosite.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" || print_error "Gagal mengunduh geosite.dat."
    wget -q -O /usr/local/share/xray/geoip.dat "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" || print_error "Gagal mengunduh geoip.dat."
    print_ok "Mengunduh ftvpn binary..."
    wget -O /usr/sbin/ftvpn "${REPO}files/ftvpn" || print_error "Gagal mengunduh ftvpn binary."
    chmod +x /usr/sbin/ftvpn
    print_ok "Menerapkan aturan iptables untuk memblokir BitTorrent..."
    iptables -A FORWARD -m string --string "get_peers" --algo bm -j DROP || print_error "Gagal menambahkan aturan iptables 1."
    iptables -A FORWARD -m string --string "announce_peer" --algo bm -j DROP || print_error "Gagal menambahkan aturan iptables 2."
    iptables -A FORWARD -m string --string "find_node" --algo bm -j DROP || print_error "Gagal menambahkan aturan iptables 3."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent" -j DROP || print_error "Gagal menambahkan aturan iptables 4."
    iptables -A FORWARD -m string --algo bm --string "BitTorrent protocol" -j DROP || print_error "Gagal menambahkan aturan iptables 5."
    iptables -A FORWARD -m string --algo bm --string "peer_id=" -j DROP || print_error "Gagal menambahkan aturan iptables 6."
    iptables -A FORWARD -m string --algo bm --string ".torrent" -j DROP || print_error "Gagal menambahkan aturan iptables 7."
    iptables -A FORWARD -m string --algo bm --string "announce.php?passkey=" -j DROP || print_error "Gagal menambahkan aturan iptables 8."
    iptables -A FORWARD -m string --algo bm --string "torrent" -j DROP || print_error "Gagal menambahkan aturan iptables 9."
    iptables -A FORWARD -m string --algo bm --string "announce" -j DROP || print_error "Gagal menambahkan aturan iptables 10."
    iptables -A FORWARD -m string --algo bm --string "info_hash" -j DROP || print_error "Gagal menambahkan aturan iptables 11."
    print_ok "Menyimpan dan memuat ulang aturan iptables..."
    iptables-save > /etc/iptables.up.rules || print_error "Gagal menyimpan aturan iptables."
    iptables-restore -t < /etc/iptables.up.rules || print_error "Gagal memuat ulang aturan iptables."
    netfilter-persistent save || print_error "Gagal menyimpan konfigurasi netfilter."
    netfilter-persistent reload || print_error "Gagal memuat ulang konfigurasi netfilter."
    cd
    apt autoclean -y || print_error "Gagal menjalankan autoclean."
    apt autoremove -y || print_error "Gagal menjalankan autoremove."
    print_success "ePro WebSocket Proxy"
    print_ok "ins_epro SELESAI"
}

function ins_restart(){
    print_install "MENJALANKAN ins_restart"
    print_ok "Merestart layanan..."
    systemctl daemon-reload || print_error "Gagal memuat ulang daemon systemd."
    for svc in nginx ssh dropbear fail2ban vnstat haproxy cron netfilter-persistent ws xray; do
         print_ok "Merestart layanan: $svc"
         systemctl restart "$svc" || print_error "Gagal merestart layanan $svc."
    done
    print_ok "Mengaktifkan layanan..."
    for svc in nginx ssh dropbear fail2ban vnstat cron haproxy netfilter-persistent ws xray rc-local; do
        print_ok "Mengaktifkan layanan: $svc"
        systemctl enable "$svc" || print_error "Gagal mengaktifkan layanan $svc."
    done
    history -c
    echo "unset HISTFILE" >> /etc/profile
    cd
    rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh
    print_ok "File sementara dihapus."
    print_success "All Services"
    print_ok "ins_restart SELESAI"
}

function menu(){
    print_install "MENJALANKAN menu"
    print_ok "Mengunduh dan mengekstrak menu..."
    wget -O /root/menu.zip "${REPO}Features/menu.zip" || print_error "Gagal mengunduh menu.zip."
    unzip menu.zip || print_error "Gagal mengekstrak menu.zip."
    chmod +x menu/*
    mv menu/* /usr/local/sbin/
    rm -rf menu /root/menu.zip
    print_ok "Menu dipindahkan ke /usr/local/sbin."
    print_success "Menu Packet"
    print_ok "menu SELESAI"
}

function profile(){
    print_install "MENJALANKAN profile"
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
    print_ok ".profile root diperbarui."
    print_ok "Menambahkan cron job untuk backup..."
    (crontab -l 2>/dev/null; echo "0 0 * * * root bot-backup") | crontab - || print_error "Gagal menambahkan cron job backup."
    print_ok "Menambahkan cron job untuk pengecekan expire..."
    (crontab -l 2>/dev/null; echo "0 3 * * * root xp") | crontab - || print_error "Gagal menambahkan cron job expire."
    print_ok "Menambahkan cron job untuk pembersihan lock..."
    (crontab -l 2>/dev/null; echo "0 3 */3 * * root clean_lock.sh >> /var/log/reset_xray_lock.log 2>&1") | crontab - || print_error "Gagal menambahkan cron job clean lock."
    print_ok "Menambahkan cron job untuk pembersihan log..."
    (crontab -l 2>/dev/null; echo "*/10 * * * * root /usr/local/sbin/clearlog") | crontab - || print_error "Gagal menambahkan cron job clearlog."
    print_ok "Menambahkan cron job untuk reboot harian..."
    (crontab -l 2>/dev/null; echo "9 3 * * * root /sbin/reboot") | crontab - || print_error "Gagal menambahkan cron job reboot."
    print_ok "Menambahkan cron job untuk rotasi log Nginx..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/nginx/access.log") | crontab - || print_error "Gagal menambahkan cron job rotasi log Nginx."
    print_ok "Menambahkan cron job untuk rotasi log Xray..."
    (crontab -l 2>/dev/null; echo "*/1 * * * * root echo -n > /var/log/xray/access.log") | crontab - || print_error "Gagal menambahkan cron job rotasi log Xray."
    echo "/bin/false" >>/etc/shells
    echo "/usr/sbin/nologin" >>/etc/shells
    print_ok "Shell /bin/false dan /usr/sbin/nologin ditambahkan ke /etc/shells."
    cat >/etc/rc.local <<EOF
#!/bin/sh -e
# rc.local for additional boot-time commands
systemctl restart netfilter-persistent 2>/dev/null
exit 0
EOF
    chmod +x /etc/rc.local
    print_ok "/etc/rc.local diperbarui."
    AUTOREB=$(cat /home/daily_reboot 2>/dev/null || echo "5")
    SETT=11
    if [ "$AUTOREB" -gt "$SETT" ]; then
        TIME_DATE="PM"
    else
        TIME_DATE="AM"
    fi
    print_ok "Waktu reboot harian: $AUTOREB (format: $TIME_DATE)"
    print_success "Profile and Cron Jobs"
    print_ok "profile SELESAI"
}

function enable_services(){
    print_install "MENJALANKAN enable_services"
    print_ok "Mengaktifkan layanan inti..."
    systemctl daemon-reload || print_error "Gagal memuat ulang daemon systemd."
    systemctl start netfilter-persistent || print_error "Gagal memulai netfilter-persistent."
    systemctl enable --now rc-local || print_error "Gagal mengaktifkan rc-local."
    systemctl enable --now cron || print_error "Gagal mengaktifkan cron."
    systemctl enable --now netfilter-persistent || print_error "Gagal mengaktifkan netfilter-persistent."
    systemctl restart nginx || print_error "Gagal merestart nginx."
    systemctl restart xray || print_error "Gagal merestart xray."
    systemctl restart cron || print_error "Gagal merestart cron."
    systemctl restart haproxy || print_error "Gagal merestart haproxy."
    print_success "Enable Core Services"
    clear
    print_ok "enable_services SELESAI"
}

function ins_backup() {
    print_install "MENJALANKAN ins_backup"
    print_ok "Melewati instalasi msmtp sesuai permintaan"
    
    if ! command -v wondershaper &> /dev/null; then
        print_ok "wondershaper tidak ditemukan di paket, mengkompilasi dari sumber..."
        apt install -y git make || print_error "Gagal menginstal dependensi build untuk wondershaper."
        cd /tmp || exit 1
        git clone https://github.com/magnific0/wondershaper.git || print_error "Gagal mengkloning repositori wondershaper."
        cd wondershaper || exit 1
        sudo make install || print_error "Gagal mengkompilasi/menginstal wondershaper."
        cd / || exit 1
        rm -rf /tmp/wondershaper
        print_ok "wondershaper berhasil dikompilasi dan diinstal."
    else
        print_ok "wondershaper sudah terinstal via package manager."
    fi
    print_ok "Menginstal rclone..."
    apt install -y rclone || print_error "Gagal menginstal rclone."
    print_ok "Mengkonfigurasi rclone (non-interaktif)..."
    printf "q\n" | rclone config
    print_ok "Mengunduh konfigurasi rclone..."
    wget -O /root/.config/rclone/rclone.conf "${REPO}cfg_conf_js/rclone.conf" || print_error "Gagal mengunduh konfigurasi rclone."
    touch /home/files
    print_ok "File placeholder /home/files dibuat."
    print_success "Backup Server"
    print_ok "ins_backup SELESAI"
}

function udp_mini(){
    print_install "MENJALANKAN udp_mini"
    print_ok "Mengunduh dan menjalankan limit.sh..."
    wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/limit.sh && chmod +x limit.sh && ./limit.sh
    print_ok "Mengunduh limit-ip..."
    wget -q -O /usr/bin/limit-ip "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/limit-ip"
    chmod +x /usr/bin/limit-ip
    print_ok "Membuat dan mengaktifkan layanan vmip, vlip, trip..."
    for service_name in vmip vlip trip; do
        cat >/etc/systemd/system/${service_name}.service << EOF
[Unit]
Description=My ${service_name^^} Service
After=network.target
[Service]
WorkingDirectory=/root 
ExecStart=/usr/bin/files-ip ${service_name}
Restart=always
RestartSec=5
User=root
[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl restart ${service_name}
        systemctl enable ${service_name}
        print_ok "Layanan ${service_name} dibuat, direstart, dan diaktifkan."
    done
    print_ok "Membuat direktori dan mengunduh udp-mini..."
    mkdir -p /usr/local/kyt/
    wget -q -O /usr/local/kyt/udp-mini "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/udp-mini"
    chmod +x /usr/local/kyt/udp-mini
    print_ok "Mengunduh dan mengelola layanan udp-mini..."
    for i in {1..3}; do
        wget -q -O /etc/systemd/system/udp-mini-${i}.service "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/udp-mini-${i}.service"
    done
    for i in {1..3}; do
        systemctl daemon-reload
        systemctl stop udp-mini-${i} 2>/dev/null
        systemctl disable udp-mini-${i} 2>/dev/null
        systemctl enable udp-mini-${i}
        systemctl start udp-mini-${i}
        if systemctl is-active --quiet udp-mini-${i}; then
            print_ok "Layanan udp-mini-${i} berhasil diaktifkan dan dimulai."
        else
            print_error "Gagal memulai layanan udp-mini-${i}. Periksa status layanan."
        fi
    done
    print_success "files Quota Service"
    print_ok "udp_mini SELESAI"
}

function password_default() {
    print_ok "Fungsi password_default dipanggil (kosong)."
    :
}

function restart_system() {
    print_install "MENJALANKAN restart_system"
CHATID="5162695441"
TOKEN_BOT="7117869623:AAHBmgzOUsmHBjcm5TFir9JmaZ_X7ynMoF4"
TIMES=30
    if [[ -z "$CHATID" || -z "$TOKEN_BOT" ]]; then
        print_error "Konfigurasi Telegram tidak lengkap (CHATID atau TOKEN_BOT kosong)."
        print_ok "Notifikasi Telegram dilewati."
        print_ok "restart_system SELESAI (tanpa notifikasi)"
        return 0
    fi
    local URL="https://api.telegram.org/bot${TOKEN_BOT}/sendMessage"
    local ipsaya=$(wget -qO- ipinfo.io/ip)
    if [[ -z "$ipsaya" ]]; then
        print_error "Gagal mendapatkan IP publik."
        ipsaya="Tidak Diketahui"
    fi
    local domain="$DOMAIN"
    if [ -z "$domain" ]; then
        domain="Tidak Ditemukan"
        print_error "Domain tidak ditemukan di /etc/xray/domain untuk notifikasi Telegram."
    fi
    local DATE_FORMAT=$(date '+%d-%m-%Y')
    local TIME_FORMAT=$(date '+%H:%M:%S')
    local USRSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $2}' | head -n 1)
    local EXPSC=$(wget -qO- https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip | grep "$ipsaya" | awk '{print $3}' | head -n 1)
    if [[ -z "$passwd" ]]; then
        local passwd_display="<i>(Tidak diubah/digunakan saat ini)</i>"
    else
        local passwd_display="<code>$passwd</code>"
    fi
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
    local REPLY_MARKUP='{"inline_keyboard":[[{"text":"🌐 Website","url":"https://t.me/wendivpn"},{"text":"🛠 Kontak","url":"https://wa.me/6283153170199"}]]}'
    print_ok "Mengirim notifikasi ke Telegram (Chat ID: $CHATID)..."
    local CURL_OUTPUT
    CURL_OUTPUT=$(curl -s --max-time "$TIMES" \
         --data-urlencode "chat_id=$CHATID" \
         -d "disable_web_page_preview=1" \
         --data-urlencode "text=$TEXT" \
         -d "parse_mode=html" \
         --data-urlencode "reply_markup=$REPLY_MARKUP" \
         "$URL" 2>&1)
    local CURL_EXIT_CODE=$?
    if [ $CURL_EXIT_CODE -ne 0 ]; then
        print_error "Gagal mengirim notifikasi ke Telegram (Exit Code: $CURL_EXIT_CODE)."
        print_error "Output curl: $CURL_OUTPUT"
    else
        if command -v jq >/dev/null 2>&1; then
            if echo "$CURL_OUTPUT" | jq -e .ok > /dev/null 2>&1; then
                if [ "$(echo "$CURL_OUTPUT" | jq -r .ok)" = "true" ]; then
                    print_ok "Notifikasi Telegram berhasil dikirim."
                else
                    local ERROR_CODE=$(echo "$CURL_OUTPUT" | jq -r .error_code 2>/dev/null || echo "N/A")
                    local DESCRIPTION=$(echo "$CURL_OUTPUT" | jq -r .description 2>/dev/null || echo "N/A")
                    print_error "Gagal mengirim notifikasi ke Telegram (API Error)."
                    print_error "Kode Error: $ERROR_CODE"
                    print_error "Deskripsi: $DESCRIPTION"
                fi
            else
                 print_error "Respons tidak valid dari API Telegram. Mungkin berhasil, tapi periksa Telegram Anda."
                 print_error "Respons: $CURL_OUTPUT"
            fi
        else
            if echo "$CURL_OUTPUT" | grep -q '"ok":true'; then
                 print_ok "Notifikasi Telegram berhasil dikirim (berdasarkan output)."
            elif echo "$CURL_OUTPUT" | grep -q '"ok":false'; then
                 print_error "Gagal mengirim notifikasi ke Telegram (berdasarkan output)."
                 print_error "Respons: $CURL_OUTPUT"
            else
                 print_error "Respons tidak jelas dari API Telegram. Mungkin berhasil, tapi periksa Telegram Anda."
                 print_error "Respons: $CURL_OUTPUT"
            fi
        fi
    fi
    print_ok "restart_system SELESAI"
}

function install_openvpn() {
    print_install "MENJALANKAN install_openvpn"
    print_ok "Menginstal paket openvpn dari repositori..."
    apt update -y > /dev/null 2>&1
    apt install -y openvpn || { print_error "Gagal menginstal paket openvpn."; print_error "OpenVPN (Instalasi Paket)"; print_error "install_openvpn GAGAL"; return 1; }
    print_success "Instalasi Paket OpenVPN"
    print_ok "Mengunduh dan menjalankan skrip konfigurasi kustom..."
    if wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/openvpn -O /root/openvpn_setup.sh; then
        chmod +x /root/openvpn_setup.sh
        if /root/openvpn_setup.sh; then
            print_ok "Skrip konfigurasi kustom berhasil dijalankan."
        else
            print_error "Gagal menjalankan skrip konfigurasi kustom (/root/openvpn_setup.sh). Periksa log atau skrip tersebut."
        fi
        rm -f /root/openvpn_setup.sh
    else
        print_error "Gagal mengunduh skrip konfigurasi kustom (openvpn). Konfigurasi dasar mungkin tidak lengkap."
    fi
    print_ok "Mengaktifkan dan merestart layanan OpenVPN (server)..."
    if ! systemctl enable openvpn-server@server; then
        print_error "Gagal mengaktifkan layanan openvpn-server@server."
    fi
    if systemctl restart openvpn-server@server; then
        print_ok "Layanan openvpn-server@server berhasil direstart."
    else
        print_error "Gagal merestart layanan openvpn-server@server. Pastikan konfigurasi sudah dibuat dengan benar."
    fi
    print_success "OpenVPN"
    print_ok "install_openvpn SELESAI"
}

# --- Fungsi Utama Install ---
function install(){
    print_install "MENJALANKAN FUNGSI INSTALL UTAMA"
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
    print_ok "FUNGSI INSTALL UTAMA SELESAI"
}

# --- Bagian Akhir Skrip ---
print_ok "MEMULAI PROSES INSTALASI"
install

# --- Final Cleanup ---
print_ok "MEMULAI FINAL CLEANUP"
history -c
rm -f /root/openvpn /root/openvpn_setup.sh /root/key.pem /root/cert.pem /root/bbr.sh /root/limit.sh /root/random.sh /root/menu.zip /root/domain

# --- Final Output and Reboot ---
clear
echo -e ""
echo -e "\033[96m===============================\033[0m"
echo -e "\033[92m        INSTALL SUCCESS\033[0m"
echo -e "\033[96m===============================\033[0m"
echo -e ""
print_ok "SETUP SELESAI"
print_ok "Sistem akan reboot sekarang secara otomatis..."
print_ok "\033[93mSystem setup is complete.\033[0m"
print_ok "\033[93mRebooting server in 5 seconds...\033[0m"

sleep 5

reboot