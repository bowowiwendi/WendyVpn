#!/bin/bash
function send_log(){
    # Bot pertama
    CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
    KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
    TEXT="
◇━━━━━━━━━━━━━━━━━◇
    🔗GENERATE LINK BACKUP🔗
◇━━━━━━━━━━━━━━━━━◇
LINK BACKUP : $fix
◇━━━━━━━━━━━━━━━━━◇
"
    # Kirim ke bot pertama
    URL="https://api.telegram.org/bot$KEY/sendMessage"
    curl -s -X POST $URL --data-urlencode "chat_id=$CHATID" --data-urlencode "text=$TEXT" >/dev/null
}
clear
read -p "IP-YYYY-MM-DD :  " iptanggal
url=$(rclone link del:backup/WT-${iptanggal}.zip) 
id=(`echo $url | grep '^https' | cut -d'=' -f2`)
link="https://drive.google.com/u/4/uc?id=${id}&export=download"
fix=$(jq -nr --arg msg "$link" '$msg')
clear
send_log
echo -e "$link"