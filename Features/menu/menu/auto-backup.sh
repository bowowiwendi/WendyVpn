#!/bin/bash
BIBlack='\033[1;90m'      # Black
BIRed='\033[1;91m'        # Red
BIGreen='\033[1;92m'      # Green
BIYellow='\033[1;93m'     # Yellow
BIBlue='\033[1;94m'       # Blue
BIPurple='\033[1;95m'     # Purple
BICyan='\033[1;96m'       # Cyan
BIWhite='\033[1;97m'      # White
UWhite='\033[4;37m'       # White
On_IPurple='\033[0;105m'  #
On_IRed='\033[0;101m'
IBlack='\033[0;90m'       # Black
IRed='\033[0;91m'         # Red
IGreen='\033[0;92m'       # Green
IYellow='\033[0;93m'      # Yellow
IBlue='\033[0;94m'        # Blue
IPurple='\033[0;95m'      # Purple
ICyan='\033[0;96m'        # Cyan
IWhite='\033[0;97m'       # White
NC='\e[0m'

# // Export Color & Information
export RED='\033[0;31m'
export GREEN='\033[0;32m'
export YELLOW='\033[0;33m'
export BLUE='\033[0;34m'
export PURPLE='\033[0;35m'
export CYAN='\033[0;36m'
export LIGHT='\033[0;37m'
export NC='\033[0m'

# // Export Banner Status Information
export EROR="[${RED} EROR ${NC}]"
export INFO="[${YELLOW} INFO ${NC}]"
export OKEY="[${GREEN} OKEY ${NC}]"
export PENDING="[${YELLOW} PENDING ${NC}]"
export SEND="[${YELLOW} SEND ${NC}]"
export RECEIVE="[${YELLOW} RECEIVE ${NC}]"
clear
red='\e[1;31m'
green='\e[0;32m'
NC='\e[0m'
MYIP=$(wget -qO- icanhazip.com);
echo "Checking VPS"
IP=$(curl -sS ipv4.icanhazip.com)
domain=$(cat /etc/xray/domain)
date=$(date +"%Y-%m-%d")
Green_font_prefix="\033[32m" && Red_font_prefix="\033[31m" && Green_background_prefix="\033[42;37m" && Red_background_prefix="\033[41;37m" && Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[ON]${Font_color_suffix}"
Error="${Red_font_prefix}[OFF]${Font_color_suffix}"
cek=$(grep -c -E "^# BEGIN_Backup" /etc/crontab)
if [[ "$cek" = "1" ]]; then
sts="${Info}"
else
sts="${Error}"
fi
function delNotif(){
clear
NUMBER_OF_CLIENTS=$(grep -c -E "^#bot# " "/etc/bot/bot.db")
if [[ ${NUMBER_OF_CLIENTS} == '0' ]]; then
    echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
    echo -e "      DELETE BOT NOTIF N BACKUP     "
    echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
    echo ""
    echo "Kamu tidak memiliki bot notif n backup"
    echo ""
    echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
    read -n 1 -s -r -p "Press [ Enter ] to back on menu"
    menu
fi

clear
CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
sed -i "/^#bot# $bottken $admin/d" /etc/bot/.bot.db
clear
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "     SUCCES DELETE BOT NOTIF N BACKUP    "
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo " Bot Token    : $KEY"
echo " ID Telegram  : $CHATID"
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo ""
read -n 1 -s -r -p "Press [ Enter ] to back on menu"
auto-backup.sh
}
function adBotNotif(){
clear
red() { echo -e "\\033[32;1m${*}\\033[0m"; }
RED='\033[0;31m'
NC='\e[0m'
gray="\e[1;30m"
Blue="\033[1;36m"
GREEN='\033[0;32m'
grenbo="\e[92;1m"
YELL='\033[0;33m'
BGX="\033[42m"

grenbo="\e[92;1m"
NC='\033[0m'
clear
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│$NC          ADD BOT NOTIF N BACKUP         $NC"
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
figlet "WendiVPN" 
read -rp "[*] BOT TOKEN   :  " -e bottoken 
read -rp "[*] ID TELEGRAM :  " -e admin
echo -e ""
clear
echo -e ""
echo -e ""
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "            is Preparing Bot......." 
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
echo -e ""
sleep 3
if [[ ${c} != "0" ]]; then
  echo "${d}" >/etc/bot/${bottoken}
fi
DATADB=$(cat /etc/bot/.bot.db | grep "^#bot#" | grep -w "${bottoken}" | awk '{print $2}')
if [[ "${DATADB}" != '' ]]; then
  sed -i "/\b${user}\b/d" /etc/bot/.bot.db
fi
echo "#bot# ${bottoken} ${admin}" >>/etc/bot/.bot.db
clear 
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "       SUCCES ADD BOT NOTIF N BACKUP       "
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
echo " Bot Token      : $bottoken"
echo " ID Telegram    : $admin"
echo -e ""
read -n 1 -s -r -p "Press [ Enter ] to back menu"
auto-backup.sh
}
clear
echo -e ""
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│$NC        MENU MANAGER AUTOBACKUP $sts          $NC" 
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│  ${green}1.${NC} \033[0;36mCeate BOT Backup n Notif"
echo -e "\033[1;93m│  ${green}2.${NC} \033[0;36mDelet BOT Backup n Notif"
echo -e "\033[1;93m│  ${green}3.${NC} \033[0;36mSet Auto-Backup 1 Hour Period"
echo -e "\033[1;93m│  ${green}4.${NC} \033[0;36mSet Auto-Backup 6 Hour Period"
echo -e "\033[1;93m│  ${green}5.${NC} \033[0;36mSet Auto-Backup 12 Hour Period"
echo -e "\033[1;93m│  ${green}6.${NC} \033[0;36mSet Auto-Backup 1 Day Period"
echo -e "\033[1;93m│  ${green}7.${NC} \033[0;36mSet Auto-Backup 1 Week Period"
echo -e "\033[1;93m│  ${green}8.${NC} \033[0;36mDeactivate Auto-Backup"
echo -e "\033[1;93m│  ${green}0.${NC} \033[0;36mBACK TO EXIT MENU \033[1;32m<\033[1;33m<\033[1;31m<\033[1;31m$NC \E[0m\033[0;34m "
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
read -p " Select menu : " opt
echo -e ""
case $opt in
1 | 01)
clear
adBotNotif
;;
2 | 02)
clear
delNotif
;;
3 | 03)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Backup
59 * * * * root bot-backup
# END_Backup
EOF
service cron restart
sleep 1
echo -e "Auto-BACKUP Sucsesfully Set By \e[32m1 Hour Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
4 | 04)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Backup
10 */6 * * * root bot-backup
# END_Backup
EOF
service cron restart
sleep 1
echo -e "Auto-BACKUP Sucsesfully Set By \e[32m6 Hour Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
5 | 05)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Backup
10 */12 * * * root bot-backup
# END_Backup
EOF
service cron restart
sleep 1
echo -e "Auto-BACKUP Sucsesfully Set By \e[32m12 Hour Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
6 | 06)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Backup
1 0 * * * root bot-backup
# END_Backup
EOF
service cron restart
sleep 1
echo -e "Auto-BACKUP Sucsesfully Set By \e[32m1 Day Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
7 | 07)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Backup
10 0 */7 * * root bot-backup
# END_Backup
EOF
service cron restart
sleep 1
echo -e "Auto-BACKUP Sucsesfully Set By \e[32m1 Week Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
8 | 08)
clear
sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
echo -e "Auto-BACKUP Sucsesfully \e[31mDeactivated ..!\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Press any key to back on menu"
auto-backup.sh
;;
0 | 00)
clear
menu
;;
x)
exit
;;
esac
