#!/bin/bash
# Update hanya file script menu, tanpa menyentuh service VPN (nginx/haproxy)
echo "Sedang mengunduh pembaruan skrip..."
wget -qO /tmp/menu-update.zip "https://github.com/bowowiwendi/WendyVpn/raw/ABSTRAK/Features/menu.zip"
unzip -o /tmp/menu-update.zip -d /tmp/menu-extracted/
cp -rf /tmp/menu-extracted/menu/* /usr/bin/
chmod +x /usr/bin/*
rm -rf /tmp/menu-update.zip /tmp/menu-extracted/
echo "Update skrip berhasil! Layanan VPN tetap aman."
