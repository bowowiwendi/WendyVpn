#!/bin/bash
export HOME=/root
export TERM=xterm
# Mengambil tanggal dari server
dateFromServer=$(curl -v --insecure --silent https://google.com/ 2>&1 | grep Date | sed -e 's/< Date: //')
date_list=$(date +"%Y-%m-%d" -d "$dateFromServer")

clear

# Konfigurasi repo dan variabel
Repo1="https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip"
EMAIL="bowowiwendi@gmail.com"
USER="bowowiwendi"

# Warna untuk output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Fungsi untuk mengirim log ke Telegram
function send_log() {
    local TIMES="10"
    local CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
    local KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
    local URL="https://api.telegram.org/bot$KEY/sendMessage"
    local TEXT="
<code>───────────────────────────</code>
 ✨SUCCES  REGISTERED IP VPS ✨
<code>───────────────────────────</code>
<code>USERNAME       : </code><code>$name</code>
<code>IP Address     : </code><code>$ip</code>
<code>Registered On  : </code><code>$today</code>
<code>Expired On     : </code><code>$exp2</code>
<code>───────────────────────────</code>
"
    curl -s --max-time $TIMES -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT&parse_mode=html" $URL >/dev/null
}

# Membuat direktori dan mengunduh daftar IP
today=$(date -d "0 days" +"%Y-%m-%d")
rm -rf /root/ipvps
mkdir -p /root/ipvps
wget -q -O /root/ipvps/ip "${Repo1}" &> /dev/null || { echo "Failed to download IP list"; exit 1; }

# Meminta input dari pengguna
read -p "  Input IP Address : " ip
read -p "  Input Username IP (Example : Wendy) : " name
read -p "  Input Expired Days : " exp

if [[ ${exp} == 'lifetime' ]]; then
    exp2="lifetime"
    sed -i '/#unli$/a\#& '"$name $exp2 $ip"'' /root/ipvps/ip  
else
    exp2=$(date -d "$exp days" +"%Y-%m-%d")
    sed -i '/#limit$/a\### '"$name $exp2 $ip"'' /root/ipvps/ip
fi

# Mengatur git dan mengunggah perubahan
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

# Mengirim log dan membersihkan
send_log
rm -rf /root/ipvps