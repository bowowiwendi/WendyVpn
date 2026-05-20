#!/bin/bash
Green_font_prefix="\033[32m" && Red_font_prefix="\033[31m" && Green_background_prefix="\033[42;37m" && Red_background_prefix="\033[41;37m" && Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[ON]${Font_color_suffix}"
Error="${Red_font_prefix}[OFF]${Font_color_suffix}"
cek=$(grep -c -E "^# BEGIN_Del" /etc/crontab)
if [[ "$cek" = "1" ]]; then
sts="${Info}"
else
sts="${Error}"
fi
#recovery
cok=$(grep -c -E "^# BEGIN_LOCK" /etc/crontab)
if [[ "$cok" = "1" ]]; then
sts1="${Info}"
else
sts1="${Error}"
fi

cik=$(grep -c -E "^# BEGIN_SC" /etc/crontab)
if [[ "$cik" = "1" ]]; then
sts2="${Info}"
else
sts2="${Error}"
fi
clear
echo -e ""
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│$NC  AUTO DEL EXPIRED AKUN $sts          $NC" 
echo -e "\033[1;93m│$NC  AUTO RECOVERY EXPIRED AKUN $sts1          $NC" 
echo -e "\033[1;93m│$NC  NOTIF EXP VPS $sts2             $NC" 
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│  ${green}1.${NC} \033[0;36mAUTO DEL ONLY${NC}"
echo -e "\033[1;93m│  ${green}2.${NC} \033[0;36mAUTO RECOVERY${NC}"
echo -e "\033[1;93m│  ${green}3.${NC} \033[0;36mOFF AUTO TOOL${NC}"
echo -e "\033[1;93m│  ${green}4.${NC} \033[0;36mDELET USER EXPIRED${NC}"
echo -e "\033[1;93m│  ${green}5.${NC} \033[0;36mON NOTIF EXP VPS${NC}"
echo -e "\033[1;93m│  ${green}6.${NC} \033[0;36mOFF NOTIF EXP VPS${NC}"
echo -e "\033[1;93m│  ${green}0.${NC} \033[0;36mBACK TO EXIT MENU \033[1;32m<\033[1;33m<\033[1;31m<\033[1;31m$NC \E[0m\033[0;34m "
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
read -p " Select menu : " opt
echo -e ""
case $opt in
1 | 01)
clear
sed -i "/^# BEGIN_LOCK/,/^# END_LOCK/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_Del
0 0 * * * root xp
# END_Del
EOF
service cron restart
sleep 1
echo -e "Auto-Del Sucsesfully Set By \e[32m1 Hour Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Tekan tombol apa saja untuk kembali ke menu"
auto-delet.sh
;;
2 | 02)
clear
sed -i "/^# BEGIN_Del/,/^# END_Del/d" /etc/crontab
cat << EOF >> /etc/crontab
# BEGIN_LOCK
0 0 * * * root recovery.sh
# END_LOCK
EOF
service cron restart
sleep 1
echo -e "Auto-LOCK Sucsesfully Set By \e[32m1 Hour Period\e[0m"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Tekan tombol apa saja untuk kembali ke menu"
auto-delet.sh
;;
3 | 03)
clear
sed -i "/^# BEGIN_LOCK/,/^# END_LOCK/d" /etc/crontab
sed -i "/^# BEGIN_Del/,/^# END_Del/d" /etc/crontab
echo -e "OFF Auto-TOOL Sucsesfully"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Tekan tombol apa saja untuk kembali ke menu"
auto-delet.sh
;;
4 | 04)
clear
xp
;;
5 | 05)
clear
cat << EOF >> /etc/crontab
# BEGIN_SC
0 0 * * * root xpsc.sh
# END_SC
EOF
service cron restart
sleep 1
echo -e "ON Notif Expired Vps Sucsesfully "
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Tekan tombol apa saja untuk kembali ke menu"
auto-delet.sh
;;
6 | 06)
clear
sed -i "/^# BEGIN_SC/,/^# END_SC/d" /etc/crontab
echo -e "OFF NOTIF EXPIRED VPS"
echo -e "\033[1;93m======================================\033[0m"
read -n 1 -s -r -p "Tekan tombol apa saja untuk kembali ke menu"
auto-delet.sh
;;
0 | 00)
clear
menu
;;
x)
exit
;;
esac

