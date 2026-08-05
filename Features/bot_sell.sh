#!/bin/bash
function checking_sc() {
    MYIP=$(curl -sS ipv4.icanhazip.com)
    IZIN=$(curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | awk '{print $4}')

    if echo "$IZIN" | grep -wq "$MYIP"; then
        echo "IZIN DITERIMA "
    else
        echo -e "\e[38;5;162m────────────────────────────────────────────\033[0m"
        echo -e "\033[44m          404 NOT FOUND AUTOSCRIPT          \033[0m"
        echo -e "\e[38;5;162m────────────────────────────────────────────\033[0m"
        echo -e ""
        echo -e "           \e[38;5;196mPERMISSION DENIED !\033[0m"
        echo -e "  \033[0;36mYour VPS IP $MYIP has been banned.\033[0m"
        echo -e "    \033[0;36mBuy access permissions for scripts.\033[0m"
        echo -e "            \033[0;36mContact Admin :\033[0m"
        echo -e "     \033[2;32mWhatsApp\033[0m https://wa.me/6283153170199"
        echo -e "\e[38;5;162m────────────────────────────────────────────\033[0m"
        exit 1  # Exit with non-zero status to indicate failure // Lunatix
    fi
}

checking_sc

MYIP=$(curl -sS ipv4.icanhazip.com)
#install
cp /media/cybervpn/var.txt /tmp
cp /root/cybervpn/var.txt /tmp
rm -rf cybervpn
apt update && apt upgrade -y
apt install python3 python3-pip -y
apt install sqlite3 -y
cd /media/
rm -rf cybervpn
wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/bot/cybervpn.zip
unzip cybervpn.zip
cd cybervpn
rm var.txt
rm database.db
pip3 install -r requirements.txt
pip install pillow
pip3 install aiohttp
pip3 install paramiko
#isi data
nsdom=$(cat /root/nsdomain)
domain=$(cat /etc/xray/domain)
clear
clear
echo
echo "INSTALL BOT CREATE SSH via TELEGRAM"
read -e -p "[*] Input Your Id Telegram :" admin
read -e -p "[*] Input Your bot Telegram :" token
read -e -p "[*] Input username Telegram :" user

if [[ ${c} != "0" ]]; then
  echo "${d}" >/etc/bot/${token}
fi
DATADB=$(cat /etc/bot/.bot.db | grep "^#bot#" | grep -w "${token}" | awk '{print $2}')
if [[ "${DATADB}" != '' ]]; then
  sed -i "/\b${token}\b/d" /etc/bot/.bot.db
fi
echo "#bot# ${token} ${admin}" >>/etc/bot/.bot.db

cat > /media/cybervpn/var.txt << END
ADMIN="$admin"
BOT_TOKEN="$token"
DOMAIN="$domain"
DNS="$nsdom"
PUB="7fbd1f8aa0abfe15a7903e837f78aba39cf61d36f183bd604daa2fe4ef3b7b59"
OWN="$user"
SALDO="100000"
END

clear
echo "Done"
echo "Your Data Bot"
echo -e "==============================="
echo "Api Token     : $token"
echo "ID            : $admin"
echo "DOMAIN        : $domain"
echo -e "==============================="
echo "Setting done"
rm -f /usr/bin/nenen
echo -e '#!/bin/bash\ncd /media/\npython3 -m cybervpn' > /usr/bin/nenen
chmod 777 /usr/bin/nenen
cat > /etc/systemd/system/cybervpn.service << END
[Unit]
Description=Simple CyberVPN - @CyberVPN
After=network.target

[Service]
WorkingDirectory=/root
ExecStart=/usr/bin/nenen
Restart=always

[Install]
WantedBy=multi-user.target

END
systemctl daemon-reload
systemctl start cybervpn
systemctl enable cybervpn

clear
echo "downloading asset"
cp /tmp/var.txt /media/cybervpn
rm -rf bot.sh
clear
clear
echo " Installations complete, type /menu on your bot "
rm /media/cybervpn.zip

# Tambahkan fitur untuk menghapus file bot yang terinstall
