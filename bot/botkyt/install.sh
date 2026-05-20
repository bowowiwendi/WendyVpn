#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Bot KYT Installer - WendyVPN
# Public Bot dengan Sistem Level & Saldo
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GREEN="\e[92;1m"
RED="\033[1;31m"
YELLOW="\033[33m"
BLUE="\033[36m"
NC="\033[0m"

clear
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}       INSTALL BOT KYT - WENDY VPN         ${NC}"
echo -e "${GREEN}    Public Bot + Saldo + Multi Server       ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check root
if [ "${EUID}" -ne 0 ]; then
    echo -e "${RED}[ERROR] Jalankan sebagai root!${NC}"
    exit 1
fi

# Install dependencies
echo -e "${YELLOW}[*] Menginstal dependencies...${NC}"
apt update -y
apt install -y python3 python3-pip sqlite3 git

# Create bot directory
echo -e "${YELLOW}[*] Menyiapkan direktori bot...${NC}"
rm -rf /media/botkyt
mkdir -p /media/botkyt

# Download bot files
REPO="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/botkyt"

echo -e "${YELLOW}[*] Mengunduh file bot...${NC}"
for file in __main__.py config.py database.py handlers.py admin_handlers.py keyboards.py formatter.py decorators.py vpn_manager.py payment.py requirements.txt; do
    wget -q -O /media/botkyt/$file "${REPO}/$file" || echo -e "${RED}Gagal mengunduh $file${NC}"
done

# Install Python dependencies
echo -e "${YELLOW}[*] Menginstal Python packages...${NC}"
cd /media/botkyt
pip3 install -r requirements.txt

# Input configuration
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}         KONFIGURASI BOT                   ${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}Tutorial: Buat bot di @BotFather${NC}"
echo -e "${YELLOW}Cek ID di @MissRose_bot (perintah /info)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -rp "[*] Input Bot Token     : " BOT_TOKEN
read -rp "[*] Input ID Telegram   : " ADMIN_ID
read -rp "[*] Input Domain VPS    : " DOMAIN
read -rp "[*] Input API Key bayar.gg (kosongkan jika belum): " BAYAR_KEY

# Write configuration
cat > /media/botkyt/var.txt << END
BOT_TOKEN="${BOT_TOKEN}"
ADMIN="${ADMIN_ID}"
DOMAIN="${DOMAIN}"
DNS=""
PUB=""
BAYAR_API_KEY="${BAYAR_KEY}"
END

# Create systemd service
echo -e "${YELLOW}[*] Membuat service systemd...${NC}"
cat > /etc/systemd/system/botkyt.service << END
[Unit]
Description=Bot KYT - WendyVPN Telegram Store
After=network.target

[Service]
WorkingDirectory=/media/botkyt
ExecStart=/usr/bin/python3 -m botkyt
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
END

# Enable and start service
echo -e "${YELLOW}[*] Mengaktifkan dan memulai bot...${NC}"
systemctl daemon-reload
systemctl enable botkyt
systemctl start botkyt

# Verify
sleep 2
if systemctl is-active --quiet botkyt; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}     ✅ BOT KYT BERHASIL DIINSTALL!        ${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "Bot Token  : ${GREEN}${BOT_TOKEN}${NC}"
    echo -e "Admin ID   : ${GREEN}${ADMIN_ID}${NC}"
    echo -e "Domain     : ${GREEN}${DOMAIN}${NC}"
    echo -e "Bayar.gg   : ${GREEN}${BAYAR_KEY:-Belum diset}${NC}"
    echo ""
    echo -e "${YELLOW}Ketik /start di bot Telegram Anda!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
else
    echo -e "${RED}[ERROR] Bot gagal dijalankan!${NC}"
    echo -e "${YELLOW}Cek log: journalctl -u botkyt -f${NC}"
fi

echo ""
echo -e "${YELLOW}Perintah berguna:${NC}"
echo -e "  systemctl status botkyt   - Cek status"
echo -e "  systemctl restart botkyt  - Restart bot"
echo -e "  systemctl stop botkyt     - Stop bot"
echo -e "  journalctl -u botkyt -f   - Lihat log"
echo ""
