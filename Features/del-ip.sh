#!/bin/bash
export HOME=/root
export TERM=xterm
# Warna untuk output
NC='\e[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELL='\033[1;33m'
Blue="\033[1;36m"
gray="\e[1;30m"
grenbo="\033[1;95m"
BGX="\033[42m"
END='\e[0m'

# Mengambil tanggal dari server
dateFromServer=$(curl -v --insecure --silent https://google.com/ 2>&1 | grep Date | sed -e 's/< Date: //')
date_list=$(date +"%Y-%m-%d" -d "$dateFromServer")

# Konfigurasi repo dan variabel
REPO="https://github.com/bowowiwendi/ipvps.git"
REPO2="https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip"
EMAIL="bowowiwendi@gmail.com"
USER="bowowiwendi"

# Konfigurasi bot Telegram
TIMES="10"
CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
URL="https://api.telegram.org/bot$KEY/sendMessage"

# Membersihkan dan membuat direktori
rm -rf /root/ipvps
mkdir -p /root/ipvps
wget -q -O /root/ipvps/ip "${REPO2}" &> /dev/null || { echo "Failed to download IP list"; exit 1; }

# Meminta input dari pengguna
read -p "   Input User : " name

# Mencari nama dan tanggal kedaluwarsa berdasarkan IP
ip=$(grep "$name" /root/ipvps/ip | awk '{print $4}')
exp=$(grep "$name" /root/ipvps/ip | awk '{print $3}')

# Menghapus entri IP dari file
if [[ ${exp} == 'lifetime' ]]; then
    sed -i "/^#& $name $exp $ip/d" /root/ipvps/ip
else
    sed -i "/^### $name $exp $ip/d" /root/ipvps/ip
fi

# Mengunggah perubahan ke GitHub
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

# Mengirim notifikasi ke Telegram
TEXT2="
<code>───────────────────────────</code>
✨SUCCES DELETE IP VPS✨
<code>───────────────────────────</code>
Name.            : $name
IP Address     : $ip
<code>───────────────────────────</code>
"
curl -s --max-time $TIMES -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT2&parse_mode=html" $URL >/dev/null

# Membersihkan direktori
rm -rf /root/ipvps