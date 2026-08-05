#!/bin/bash
export HOME=/root
export TERM=xterm
REPO="https://raw.githubusercontent.com/bowowiwendi/ipvps/main/main/ip"
EMAIL="bowowiwendi@gmail.com"
USER="bowowiwendi"
function notif-exp(){
TIME="10"
CHATID="5162695441"
KEY="6778508111:AAGmlVVILOA0z4kgLHoA1gD7Hf-maAi9vCQ"
URL="https://api.telegram.org/bot$KEY/sendMessage"
TEXT="<code>──────────────────────────────────</code>
<b>⚠️ YOUR VPS EXPIRED ⚠️</b>
<code>──────────────────────────────────</code>
USER        : $user
VPS IP      : $ip
DATE        : $exp
<code>──────────────────────────────────</code>
"
curl -s --max-time $TIME -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT&parse_mode=html" $URL >/dev/null
}
data=($(curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep '^###' | awk '{print $2}'))  # Mengubah menjadi array
now=$(date +"%Y-%m-%d")
for user in "${data[@]}"; do
    exp=$(curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep -w "^### $user" | awk '{print $3}')
    # Tambahkan kondisi untuk melewati pengguna dengan status "lifetime"
    if [[ "$exp" == "lifetime" ]]; then
        continue
    fi
    ip=$(curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep -w "^### $user" | awk '{print $4}')
    d1=$(date -d "$exp" +%s)
    d2=$(date -d "$now" +%s)
    exp2=$(((d1 - d2) / 86400))
    if [[ "$exp2" -le "2" || "$exp2" -le "1" || "$exp2" -eq "0" ]]; then  # Ubah dari 0 menjadi 1
        notif-exp
    fi
done
