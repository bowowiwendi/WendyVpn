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
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m${NC}"
read -p "PILIH NOMOR:" bro

case $bro in
01 | 1) clear ; systemctl restart cybervpn && panelbot ;;
02 | 2) clear ; systemctl stop cybervpn && panelbot ;;
03 | 3) clear ; nano /root/cybervpn/var.txt ;;
100) clear ; $up2u ;;
00 | 0) clear ; menu ;;
*) clear ; menu ;;
esac
