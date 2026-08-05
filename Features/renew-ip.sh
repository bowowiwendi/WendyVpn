#!/bin/bash
export HOME=/root
export TERM=xterm
# Warna untuk output
NC='\e[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELL='\033[1;33m'
Blue="\033[1;36m"
grenbo="\033[1;95m"
BGX="\033[42m"
END='\e[0m'

# Konfigurasi
REPO="https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip"
EMAIL="bowowiwendi@gmail.com"
USER="bowowiwendi"
TIMES="10"

# Ambil informasi tanggal dari server Google
dateFromServer=$(curl -v --insecure --silent https://google.com/ 2>&1 | grep Date | sed -e 's/< Date: //')
now=$(date +"%Y-%m-%d" -d "$dateFromServer")

# Konfigurasi bot Telegram
CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
URL="https://api.telegram.org/bot$KEY/sendMessage"

# Bersihkan direktori dan buat yang baru
rm -rf /root/ipvps
mkdir -p /root/ipvps
wget -q -O /root/ipvps/ip "${REPO}" &> /dev/null

# Input dari pengguna
read -p "  Input User  : " user
read -p "  Input Days  : " days

# Ambil informasi nama dan tanggal kedaluwarsa dari IP yang dimasukkan
ip=$(curl -sS ${REPO} | grep $user | awk '{print $4}')
exp=$(curl -sS ${REPO} | grep $user | awk '{print $3}')
d1=$(date -d "$exp" +%s)
d2=$(date -d "$now" +%s)
exp2=$(( (d1 - d2) / 86400 ))
exp3=$(($exp2 + $days))
exp4=$(date -d "$exp3 days" +"%Y-%m-%d")

# Perbarui tanggal kedaluwarsa di file IP
sed -i "s/^### $user $exp $ip/### $user $exp4 $ip/g" /root/ipvps/ip

# Commit dan push perubahan ke GitHub
cd /root/ipvps
git config --global user.email "${EMAIL}" &> /dev/null
git config --global user.name "${USER}" &> /dev/null
rm -rf .git &> /dev/null
git init &> /dev/null
git add . &> /dev/null
git commit -m "update file" &> /dev/null
git branch -M main &> /dev/null
git remote add origin git@github.com:bowowiwendi/ipvps.git
git push -f origin main &> /dev/null

# Kirim notifikasi ke Telegram
TEXT="
<code>───────────────────────────</code>
     ✨SUCCES RENEW  IP VPS✨
<code>───────────────────────────</code>
USERNAME       : <code>$user</code>
IP Address     : $ip
Expired On     : $exp4
<code>───────────────────────────</code>
"
curl -s --max-time $TIMES -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT&parse_mode=html" $URL >/dev/null

# Bersihkan direktori
rm -rf /root/ipvps