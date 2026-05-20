grenbo="\e[92;1m"
NC='\033[0m'
clear
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│$NC          MENU MANAGER RECOVERY          $NC"|lolcat
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e "\033[1;93m┌──────────────────────────────────────────┐\033[0m"
echo -e "\033[1;93m│  ${grenbo}1.${NC} \033[0;36mRENEW VMESS ${NC}"
echo -e "\033[1;93m│  ${grenbo}2.${NC} \033[0;36mRENEW VLESS ${NC}"
echo -e "\033[1;93m│  ${grenbo}3.${NC} \033[0;36mRENEW TROJAN${NC}"
echo -e "\033[1;93m│  ${grenbo}4.${NC} \033[0;36mDELET VMESS ${NC}"
echo -e "\033[1;93m│  ${grenbo}5.${NC} \033[0;36mDELET VLESS ${NC}"
echo -e "\033[1;93m│  ${grenbo}6.${NC} \033[0;36mDELET TROJAN${NC}"
echo -e "\033[1;93m│  ${grenbo}7.${NC} \033[0;36mDELET ALL USER IN RECOVRY ${NC}"
echo -e "\033[1;93m│  ${grenbo}x.${NC} \033[0;36mComeBack${NC}"
echo -e "\033[1;93m└──────────────────────────────────────────┘\033[0m"
echo -e ""
read -p " Select options >>>   "  opt
echo -e   ""
case $opt in
01 | 1) clear ; revm.sh ;;
02 | 2) clear ; revl.sh ;;
03 | 3) clear ; retr.sh ;;
04 | 4) clear ; delrevm.sh ;;
05 | 5) clear ; delrevl.sh ;;
06 | 6) clear ; delretr.sh ;;
07 | 7) clear ; delallxray.sh;;
00 | 0) clear ; menu ;;
*) clear ; menu ;;
esac