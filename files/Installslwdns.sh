#!/bin/bash
# install-slowdns.sh - SlowDNS Installation Script (Fixed Version)
# Modifikasi utama:
# 1. Menggunakan port alternatif (5353) untuk SlowDNS
# 2. Menghindari konflik dengan port SSH default
# 3. Penanganan firewall yang lebih baik

# Fungsi untuk menampilkan header
show_header() {
    clear
    echo -e "\033[1;36m"
    echo "  ____     _          ____  _   _ ____  "
    echo " / ___|   | |   ___  |  _ \| \ | / ___| "
    echo " \___ \   | |  / _ \ | | | |  \| \___ \ "
    echo "  ___) |  | | |  __/ | |_| | |\  |___) |"
    echo " |____/   |_|  \___| |____/|_| \_|____/ "
    echo -e "\033[0m"
    echo "========================================"
    echo " SlowDNS Installation Script (v2.2)"
    echo "========================================"
    echo ""
}

# Fungsi untuk validasi IP
validate_ip() {
    local ip=$1
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Fungsi untuk validasi domain
validate_domain() {
    local domain=$1
    if [[ $domain =~ ^(([a-zA-Z0-9](-?[a-zA-Z0-9])*)\.)+[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Fungsi untuk memeriksa port yang sedang digunakan
check_port() {
    local port=$1
    if ss -tuln | grep -q ":${port} "; then
        echo -e "\033[1;31m❌ Port ${port} sudah digunakan oleh service lain\033[0m"
        ss -tulnp | grep ":${port} "
        return 1
    else
        return 0
    fi
}

# Main script
show_header

# Check root access
if [ "$(id -u)" != "0" ]; then
    echo -e "\033[1;31m❌ Error: Script harus dijalankan sebagai root\033[0m"
    exit 1
fi

# Port configuration
SLOWDNS_PORT=5353
SSH_CLIENT_PORT=2222
SSH_SERVER_PORT=2269

# Check port availability
echo "🔍 Memeriksa ketersediaan port..."
check_port $SLOWDNS_PORT || exit 1
check_port $SSH_CLIENT_PORT || exit 1
check_port $SSH_SERVER_PORT || exit 1

# Check existing domain config
if [ -f /etc/xray/domain ]; then
    full_domain=$(cat /etc/xray/domain)
    echo "ℹ️ Detected existing domain configuration: $full_domain"
    
    read -p "Gunakan domain yang terdeteksi? [Y/n]: " use_detected
    if [[ "$use_detected" =~ ^[Nn]$ ]]; then
        while true; do
            read -p "Masukkan domain lengkap (contoh: sub.domain.tld): " full_domain
            if validate_domain "$full_domain"; then
                break
            else
                echo -e "\033[1;31m❌ Format domain tidak valid. Contoh: sub.domain.tld\033[0m"
            fi
        done
    fi
else
    while true; do
        read -p "Masukkan domain lengkap (contoh: sub.domain.tld): " full_domain
        if validate_domain "$full_domain"; then
            break
        else
            echo -e "\033[1;31m❌ Format domain tidak valid. Contoh: sub.domain.tld\033[0m"
        fi
    done
fi

# Extract domain parts
IFS='.' read -ra domain_parts <<< "$full_domain"
subdomain="${domain_parts[0]}"
main_domain="${full_domain#$subdomain.}"

# Validasi tambahan domain
if [[ "$main_domain" == *.*.* ]]; then
    echo -e "\033[1;31m❌ Error: Format domain tidak valid. Hindari multiple TLD (.id.id)\033[0m"
    exit 1
fi

# Dapatkan IP server
IP=$(curl -s ipinfo.io/ip)
if ! validate_ip "$IP"; then
    echo -e "\033[1;31m❌ Error: Gagal mendapatkan alamat IP server ($IP tidak valid)\033[0m"
    exit 1
fi

# Cloudflare Configuration
CF_KEY="dc7a32077573505cc082f4be752509a5c5a3e"
CF_ID="bowowiwendi@gmail.com"

# Cloudflare API Functions
get_zone_id() {
    response=$(curl -sLX GET "https://api.cloudflare.com/client/v4/zones?name=${main_domain}&status=active" \
    -H "X-Auth-Email: ${CF_ID}" \
    -H "X-Auth-Key: ${CF_KEY}" \
    -H "Content-Type: application/json")
    
    if echo "$response" | jq -e '.success == true' >/dev/null; then
        echo "$response" | jq -r '.result[0].id'
    else
        echo -e "\033[1;31m❌ Error getting Zone ID: $(echo "$response" | jq -r '.errors[0].message')\033[0m"
        exit 1
    fi
}

create_record() {
    local type=$1 name=$2 content=$3
    echo -e "\n🔧 Creating ${type} record for ${name}..."
    response=$(curl -sLX POST "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records" \
    -H "X-Auth-Email: ${CF_ID}" \
    -H "X-Auth-Key: ${CF_KEY}" \
    -H "Content-Type: application/json" \
    --data '{"type":"'${type}'","name":"'${name}'","content":"'${content}'","ttl":120,"proxied":false}')
    
    if echo "$response" | jq -e '.success == true' >/dev/null; then
        echo -e "\033[1;32m✔️ Record created successfully\033[0m"
        echo "$response" | jq -r '.result.id'
    else
        echo -e "\033[1;31m❌ Error creating ${type} record: $(echo "$response" | jq -r '.errors[0].message')\033[0m"
        echo "Response: $response"
        exit 1
    fi
}

# Main DNS Setup
echo -e "\n⏳ Configuring Cloudflare DNS records..."
ZONE=$(get_zone_id)
echo "✔️ Zone ID: ${ZONE}"

# Create nameserver record (gunakan subdomain 'slowdns' sebagai standar)
ns_record="slowdns.${main_domain}"
create_record A "${ns_record}" "${IP}"

# Create NS delegation
create_record NS "${full_domain}" "${ns_record}"

# Save domain info
echo ${ns_record} > /root/nsdomain
echo ${full_domain} > /etc/xray/domain

echo -e "\n✅ DNS Setup Complete!"
echo "========================================"
echo "   Configuration Summary:"
echo "   Full Domain: ${full_domain}"
echo "   Main Domain: ${main_domain}"
echo "   Subdomain: ${subdomain}"
echo "   Nameserver: ${ns_record}"
echo "   Server IP: ${IP}"
echo "========================================"

# Install dependencies
echo -e "\n⏳ Installing dependencies..."
apt update -y
apt install -y python3 python3-dnslib net-tools dnsutils iptables jq

# Setup SlowDNS
echo -e "\n🔧 Configuring SlowDNS..."
mkdir -p /etc/slowdns
wget -qO /etc/slowdns/server.key "https://raw.githubusercontent.com/fisabiliyusri/SLDNS/main/slowdns/server.key"
wget -qO /etc/slowdns/server.pub "https://raw.githubusercontent.com/fisabiliyusri/SLDNS/main/slowdns/server.pub"
wget -qO /etc/slowdns/sldns-server "https://raw.githubusercontent.com/fisabiliyusri/SLDNS/main/slowdns/sldns-server"
wget -qO /etc/slowdns/sldns-client "https://raw.githubusercontent.com/fisabiliyusri/SLDNS/main/slowdns/sldns-client"
chmod +x /etc/slowdns/{sldns-server,sldns-client}

# Configure services
echo -e "\n📝 Creating service files..."

# Client Service
cat > /etc/systemd/system/client-sldns.service << EOF
[Unit]
Description=Client SlowDNS
After=network.target

[Service]
Type=simple
User=root
ExecStart=/etc/slowdns/sldns-client -udp 127.0.0.1:${SLOWDNS_PORT} --pubkey-file /etc/slowdns/server.pub $(cat /root/nsdomain) 127.0.0.1:${SSH_CLIENT_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Server Service
cat > /etc/systemd/system/server-sldns.service << EOF
[Unit]
Description=Server SlowDNS
After=network.target

[Service]
Type=simple
User=root
ExecStart=/etc/slowdns/sldns-server -udp :${SLOWDNS_PORT} -privkey-file /etc/slowdns/server.key $(cat /root/nsdomain) 127.0.0.1:${SSH_SERVER_PORT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Firewall rules
echo -e "\n🔥 Configuring firewall..."
iptables -I INPUT -p udp --dport ${SLOWDNS_PORT} -j ACCEPT
iptables -t nat -I PREROUTING -p udp --dport 53 -j REDIRECT --to-ports ${SLOWDNS_PORT}
iptables-save > /etc/iptables/rules.v4

# SSH Configuration
echo -e "\n🔒 Configuring SSH ports..."
if ! grep -q "^Port ${SSH_CLIENT_PORT}" /etc/ssh/sshd_config; then
    echo "Port ${SSH_CLIENT_PORT}" >> /etc/ssh/sshd_config
fi
if ! grep -q "^Port ${SSH_SERVER_PORT}" /etc/ssh/sshd_config; then
    echo "Port ${SSH_SERVER_PORT}" >> /etc/ssh/sshd_config
fi
sed -i 's/#AllowTcpForwarding yes/AllowTcpForwarding yes/g' /etc/ssh/sshd_config

# Restart SSH dengan port baru
echo "Restarting SSH service..."
systemctl restart ssh

# Enable services
echo -e "\n🚀 Starting services..."
systemctl daemon-reload
systemctl enable --now client-sldns server-sldns

echo -e "\n\033[1;32m✅ SlowDNS Installation Complete!\033[0m"
echo "========================================"
echo "   Service Status:"
echo "   - Client SlowDNS: systemctl status client-sldns"
echo "   - Server SlowDNS: systemctl status server-sldns"
echo ""
echo "   Port Configuration:"
echo "   - SlowDNS: UDP ${SLOWDNS_PORT}"
echo "   - SSH Client: ${SSH_CLIENT_PORT}"
echo "   - SSH Server: ${SSH_SERVER_PORT}"
echo "========================================"
echo -e "\n⚠️ Tunggu propagasi DNS (bisa memakan waktu beberapa menit hingga beberapa jam)"
echo "Cek dengan perintah:"
echo "   dig +short A ${ns_record}"
echo "   dig +short NS ${full_domain}"
echo -e "\n⚠️ Untuk mengakses SSH, gunakan port ${SSH_CLIENT_PORT} atau ${SSH_SERVER_PORT}"
