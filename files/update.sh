#!/bin/bash
clear
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e " \e[1;97;101m             UPDATE SCRIPT              \e[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"

cd /tmp
rm -rf menu menu.zip

echo -e "\033[0;33m[1/4] Downloading menu...\033[0m"
wget -q "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/Features/menu.zip"
if [ $? -ne 0 ]; then
    echo -e "\033[1;31m Download FAILED\033[0m"
    exit 1
fi

echo -e "\033[0;33m[2/4] Extracting...\033[0m"
unzip -q -o menu.zip
if [ ! -f menu/menu ]; then
    echo -e "\033[1;31m Extract FAILED\033[0m"
    exit 1
fi

echo -e "\033[0;33m[3/4] Installing to /usr/local/sbin...\033[0m"
chmod +x menu/* 2>/dev/null
mkdir -p /usr/local/sbin
cp menu/* /usr/local/sbin/ 2>/dev/null

echo -e "\033[0;33m[4/4] Cleaning up...\033[0m"
rm -rf menu menu.zip

echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[1;32m ✓ Update selesai\033[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
read -n 1 -s -r -p "Press [ Enter ] to back on menu"
menu
