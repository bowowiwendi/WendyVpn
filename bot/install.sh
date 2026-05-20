wget https://github.com/bowowiwendi/backup/raw/refs/heads/main/Botdo.zip
mv Botdo /usr/bin/
rm -rf Botdo.zip
pip3.8 install -r /usr/bin/Botdo/requirements.txt
cd /usr/bin
clear
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\e[1;97;101m               ADD BOT DO VPS              \e[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "${grenbo}Tutorial Creat Bot and ID Telegram${NC}"
echo -e "${grenbo}[*] Creat Bot and Token Bot : @BotFather${NC}"
echo -e "${grenbo}[*] Info Id Telegram : @MissRose_bot , perintah /info${NC}"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
read -rp "[*] Input your Bot Name : " -e NAME
read -rp "[*] Input your Bot Token : " -e TOKEN 
read -rp "[*] Input Your Id Telegram : " -e ADMINS
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
sed -i 's/"NAME": "[^"]*"/"NAME": "${NAME}"/' Botdo/config.json
sed -i 's/"TOKEN": "[^"]*"/"TOKEN": "${TOKEN}"/' Botdo/config.json
sed -i 's/"ADMINS": \[[^]]*\]/"ADMINS": [${ADMINS}]/' Botdo/config.json
cat > /etc/systemd/system/Botdo.service << END
[Unit]
Description=Simple Botdo - @Botdo
After=network.target

[Service] 
WorkingDirectory=/usr/bin/
ExecStart=/usr/bin/python3 -m Botdo
Restart=always

[Install]
WantedBy=multi-user.target
END

systemctl start Botdo.service 
systemctl enable Botdo.service
systemctl restart Botdo.service
read -n 1 -s -r -p "SELESAI Press [ Enter ] to back menu bot"



