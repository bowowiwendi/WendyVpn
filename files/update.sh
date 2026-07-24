# Decrypted by WV | FUSCATOR
# Github- https://github.com/bowowiwendi/Absurd

# Install dependencies first (prevents broken update)
apt-get install -y p7zip-full unzip wget 2>/dev/null || true
apt-get install -y 7zip 2>/dev/null || true
rm -rf /usr/bin/enc
cd /tmp
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
cd /tmp
wget -q https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/Features/menu.zip || return 1
wget -q -O /usr/bin/enc "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/enc/encrypt" ; chmod +x /usr/bin/enc
7z e -paskykenza123 menu.zip -y >/dev/null 2>&1 || true
unzip -o menu.zip >/dev/null 2>&1 || true
[ -f menu/menu ] || { echo "Extract failed"; exit 1; }
chmod +x menu/* 2>/dev/null
enc menu/* 2>/dev/null || true
rm -rf /usr/local/sbin
mkdir -p /usr/local/sbin
mv menu/* /usr/local/sbin/ 2>/dev/null || cp -r menu/* /usr/local/sbin/ 2>/dev/null
rm -rf menu menu.zip
rm -rf update.sh
rm -rf *
}
netfilter-persistent
clear
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e " \e[1;97;101m             UPDATE SCRIPT              \e[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e ""
echo -e "  \033[1;91m update script service\033[1;37m"
fun_bar 'res1'
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e ""
read -n 1 -s -r -p "Press [ Enter ] to back on menu"
menu
