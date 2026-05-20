#!/bin/bash
export HOME=/root
export TERM=xterm
NC='\e[0m'
Repo1="https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip"
EMAIL="bowowiwendi@gmail.com"
USER="bowowiwendi"
git="git@github.com:bowowiwendi/ipvps.git"
TIMES="10"
CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
URL="https://api.telegram.org/bot$KEY/sendMessage"

# Clear the screen
clear

# Install git if not installed
[[ ! -f /usr/bin/git ]] && apt install git -y &> /dev/null

# Create and prepare the ipvps directory
rm -rf /root/ipvps
mkdir -p /root/ipvps
wget -q -O /root/ipvps/ip "${Repo1}" &> /dev/null

# Prompt for old and new IP
read -p "  Input IP Lama/Old: " ip1
read -p "  Input IP Baru/New: " ip2

# Extract name and expiration date from the old IP
name=$(curl -sS ${Repo1} | grep $ip1 | awk '{print $2}')
exp=$(curl -sS ${Repo1} | grep $ip1 | awk '{print $3}')

# Replace the old IP with the new one
sed -i "s/^### $name $exp $ip1/### $name $exp $ip2/g" /root/ipvps/ip

# Commit and push changes to GitHub
cd /root/ipvps
git config --global user.email "${EMAIL}" &> /dev/null
git config --global user.name "${USER}" &> /dev/null
rm -rf .git &> /dev/null
git init &> /dev/null
git add . &> /dev/null
git commit -m "update file" &> /dev/null
git branch -M main &> /dev/null
git remote add origin ${git}
git push -f origin main &> /dev/null

# Send notification to Telegram
TEXT2="
<code>───────────────────────────</code>
        ✨SUCCES CHANGE  IP REGIST✨
<code>───────────────────────────</code>
USERNAME       : <code>$name</code>
IP LAMA/OLD    : $ip1
IP BARU/NEW    : $ip2
<code>───────────────────────────</code>
"
curl -s --max-time $TIMES -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT2&parse_mode=html" $URL >/dev/null

# Clean up
rm -rf /root/ipvps