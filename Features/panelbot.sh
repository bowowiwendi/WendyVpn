#!/bin/bash
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[0;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export LIGHT='\033[0;37m'
export NC='\033[0m'

cybervpn_service=$(systemctl status cybervpn | grep Active | awk '{print $3}' | cut -d "(" -f2 | cut -d ")" -f1)
function hapus-bot(){
clear
dateFromServer=$(curl -v --insecure --silent https://google.com/ 2>&1 | grep Date | sed -e 's/< Date: //')
biji=`date +"%Y-%m-%d" -d "$dateFromServer"`
red() { echo -e "\\033[32;1m${*}\\033[0m"; }
clear
fun_bar() {
    CMD[0]="$1"
    CMD[1]="$2"
    (
        [[ -e $HOME/fim ]] && rm $HOME/fim
        ${CMD[0]} -y >/dev/null 2>&1
        ${CMD[1]} -y >/dev/null 2>&1
        touch $HOME/fim
    ) >/dev/null 2>&1 &
    tput civis
    echo -ne "  \033[0;33mPlease Wait Loading \033[1;37m- \033[0;33m["
    while true; do
        for ((i = 0; i < 18; i++)); do
            echo -ne "\033[0;32m🚥"
            sleep 0.1s
        done
        [[ -e $HOME/fim ]] && rm $HOME/fim && break
        echo -e "\033[0;33m]"
        sleep 1s
        tput cuu1
        tput dl1
        echo -ne "  \033[0;33mPlease Wait Loading \033[1;37m- \033[0;33m["
    done
    echo -e "\033[0;33m]\033[1;37m -\033[1;32m OK !\033[1;37m"
    tput cnorm
}
res1() {
    systemctl stop cybervpn
    rm -rf /usr/bin/nenen
    rm -rf /etc/systemd/system/cybervpn.service
    systemctl disable cybervpn
}
netfilter-persistent
clear
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "      HAPUS BOT PANEL SELER     "|lolcat
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e ""
echo -e "  \033[1;91m hapus bot service\033[1;37m"
fun_bar 'res1'
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
}

#!/bin/bash

function up() {

echo "Memulai proses update bot..."

# Hentikan service bot
systemctl stop cybervpn

# Backup var.txt
cp /media/cybervpn/var.txt /tmp/var.txt.backup
cp /media/cybervpn/database.db /tmp/database.db

# Update files
cd /media/
rm -rf cybervpn
wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/cybervpn.zip
unzip cybervpn.zip
rm -rf cybervpn.zip
cd cybervpn

# Restore var.txt
cp /tmp/var.txt.backup /media/cybervpn/var.txt
cp /tmp/database.db /media/cybervpn/database.db 

# Update dependencies
pip3 install -r requirements.txt
pip install pillow
pip3 install aiohttp
pip3 install paramiko

# Restart service
systemctl daemon-reload
systemctl start cybervpn

echo "Update selesai!"
echo "Bot telah diperbarui dan dijalankan kembali"
}
# STATUS SERVICE  SQUID 
if [[ $cybervpn_service == "running" ]]; then 
   status_cybervpn=" ${GREEN}Running ${NC}"
else
   status_cybervpn="${RED}  Not Running ${NC}"
fi
clear
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m${NC}"
echo -e "\E[44;1;39m            ⇱ bot panel Telegram⇲             \E[0m"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m${NC}"
echo -e "${LIGHT}"
echo -e "STATUS  BOT: $cybervpn_service"
echo -e "1.START BOT"
echo -e "2.STOP BOT"
echo -e "3.Edit bot/id telegram/notif"
echo -e "4.HAPUS BOT"
echo -e "5.CREATE BOT"
echo -e "6.UPDATE BOT"
echo -e "0.BACK TO MENU"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m${NC}"
read -p "PILIH NOMOR:" bro

case $bro in
01 | 1) clear ; systemctl restart cybervpn && panelbot.sh ;;
02 | 2) clear ; systemctl stop cybervpn && panelbot.sh ;;
03 | 3) clear ; nano /media/cybervpn/var.txt ;;
04 | 4) clear ; hapus-bot && panelbot.sh ;;
05 | 5) clear ; bot_sell.sh ;;
06 | 6) clear ; up ;;
00 | 0) clear ; menu ;;
*) clear ; menu ;;
esac
