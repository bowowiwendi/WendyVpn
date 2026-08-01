#!/bin/bash
clear
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e " \e[1;97;101m             UPDATE SCRIPT              \e[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"

REPO="https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/"
BK=/root/backup-config
mkdir -p "$BK"

cd /tmp
rm -rf menu menu.zip

echo -e "\033[0;33m[1/6] Downloading menu...\033[0m"
wget -q "${REPO}Features/menu.zip"
if [ $? -ne 0 ]; then
    echo -e "\033[1;31m Download FAILED\033[0m"
    exit 1
fi

echo -e "\033[0;33m[2/6] Extracting & installing menu...\033[0m"
unzip -q -o menu.zip
if [ ! -f menu/menu ]; then
    echo -e "\033[1;31m Extract FAILED\033[0m"
    exit 1
fi
chmod +x menu/* 2>/dev/null
mkdir -p /usr/local/sbin
cp menu/* /usr/local/sbin/ 2>/dev/null

echo -e "\033[0;33m[3/6] Backing up configs...\033[0m"
cp /etc/haproxy/haproxy.cfg "$BK/haproxy.cfg.bak" 2>/dev/null
cp /etc/nginx/conf.d/xray.conf "$BK/xray.conf.bak" 2>/dev/null
cp /etc/nginx/nginx.conf "$BK/nginx.conf.bak" 2>/dev/null
cp /usr/local/bin/wendy-api.py "$BK/wendy-api.py.bak" 2>/dev/null
cp /usr/bin/tun.conf "$BK/tun.conf.bak" 2>/dev/null
echo -e "\033[1;32m ✓ Backup saved to $BK\033[0m"

echo -e "\033[0;33m[4/6] Updating core config (nginx + haproxy + ws)...\033[0m"
domain=$(cat /etc/xray/domain 2>/dev/null || echo "")

# nginx.conf + xray.conf
wget -q -O /etc/nginx/nginx.conf "${REPO}cfg_conf_js/nginx.conf" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "\033[1;31m ✗ nginx.conf download failed, restore backup\033[0m"
    cp "$BK/nginx.conf.bak" /etc/nginx/nginx.conf 2>/dev/null
fi
wget -q -O /etc/nginx/conf.d/xray.conf "${REPO}cfg_conf_js/xray.conf" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "\033[1;31m ✗ xray.conf download failed, restore backup\033[0m"
    cp "$BK/xray.conf.bak" /etc/nginx/conf.d/xray.conf 2>/dev/null
elif [ -n "$domain" ]; then
    sed -i "s/xxx/${domain}/g" /etc/nginx/conf.d/xray.conf 2>/dev/null
fi

# Hapus default site nginx agar tidak berebut port 80/443 dengan haproxy
rm -f /etc/nginx/sites-enabled/* /etc/nginx/sites-available/default 2>/dev/null

# Fix port 80/443 di SEMUA nginx config lain (pindah ke 81/8443)
NGINX_CONF=$(grep -rlE 'listen (80|443)' /etc/nginx/ 2>/dev/null)
if [ -n "$NGINX_CONF" ]; then
    echo -e "\033[1;33m  Nginx pakai 80/443 → pindah ke 81/8443\033[0m"
    while IFS= read -r f; do
        sed -i \
            -e 's/listen\s*80\b/listen 81/g' \
            -e 's/listen\s*443\s*ssl/listen 8443 ssl/g' \
            -e 's/\[::]:80/\[::]:81/g' \
            -e 's/\[::]:443 ssl/\[::]:8443 ssl/g' "$f" 2>/dev/null
    done <<< "$NGINX_CONF"
fi

# Systemd: nginx jalan SETELAH haproxy (anti race port di boot)
mkdir -p /etc/systemd/system/nginx.service.d
cat > /etc/systemd/system/nginx.service.d/order.conf << 'SYSDFIX'
[Unit]
After=haproxy.service
Wants=haproxy.service
SYSDFIX
systemctl daemon-reload 2>/dev/null

# haproxy.cfg + cert gabungan
wget -q -O /etc/haproxy/haproxy.cfg "${REPO}cfg_conf_js/haproxy.cfg" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "\033[1;31m ✗ haproxy.cfg download failed, restore backup\033[0m"
    cp "$BK/haproxy.cfg.bak" /etc/haproxy/haproxy.cfg 2>/dev/null
else
    [ -n "$domain" ] && sed -i "s/xxx/${domain}/g" /etc/haproxy/haproxy.cfg 2>/dev/null
    sed -i '/^[[:space:]]*chroot/d' /etc/haproxy/haproxy.cfg 2>/dev/null
    cat /etc/xray/xray.crt /etc/xray/xray.key 2>/dev/null | tee /etc/haproxy/hap.pem >/dev/null
fi

# ws tunnel + service
wget -q -O /usr/bin/ws "${REPO}files/ws" 2>/dev/null && chmod +x /usr/bin/ws
wget -q -O /usr/bin/tun.conf "${REPO}cfg_conf_js/tun.conf" 2>/dev/null || cp "$BK/tun.conf.bak" /usr/bin/tun.conf 2>/dev/null
wget -q -O /etc/systemd/system/ws.service "${REPO}files/ws.service" 2>/dev/null && chmod +x /etc/systemd/system/ws.service
wget -q -O /etc/systemd/system/runn.service "${REPO}files/runn.service" 2>/dev/null && chmod +x /etc/systemd/system/runn.service
systemctl daemon-reload 2>/dev/null

echo -e "\033[0;33m[5/6] Validating & restarting services...\033[0m"
# nginx: validasi dulu, rollback jika gagal
nginx -t >/dev/null 2>&1
if [ $? -eq 0 ]; then
    systemctl restart nginx 2>/dev/null && echo -e "\033[1;32m ✓ nginx updated & restarted\033[0m" || echo -e "\033[1;31m ✗ nginx restart failed\033[0m"
else
    echo -e "\033[1;31m ✗ Nginx config error, restore backup\033[0m"
    cp "$BK/xray.conf.bak" /etc/nginx/conf.d/xray.conf 2>/dev/null
    cp "$BK/nginx.conf.bak" /etc/nginx/nginx.conf 2>/dev/null
    nginx -t >/dev/null 2>&1 && systemctl restart nginx 2>/dev/null
fi

# haproxy: validasi, rollback jika gagal
haproxy -c -f /etc/haproxy/haproxy.cfg >/dev/null 2>&1
if [ $? -eq 0 ]; then
    systemctl restart haproxy 2>/dev/null && echo -e "\033[1;32m ✓ haproxy updated & restarted\033[0m" || echo -e "\033[1;31m ✗ haproxy restart failed\033[0m"
else
    echo -e "\033[1;31m ✗ Config invalid, restore backup\033[0m"
    cp "$BK/haproxy.cfg.bak" /etc/haproxy/haproxy.cfg 2>/dev/null
    systemctl restart haproxy 2>/dev/null
fi

systemctl restart ws 2>/dev/null || true

echo -e "\033[0;33m[5.5/6] Running auto-fix (dropbear + wendy-api)...\033[0m"
wget -qO /usr/bin/fix_all.sh "${REPO}files/fix_all.sh" && chmod +x /usr/bin/fix_all.sh && /usr/bin/fix_all.sh || echo -e "\033[1;31m Auto-fix gagal, tetap lanjut\033[0m"

echo -e "\033[0;33m[6/6] Cleaning up...\033[0m"
rm -rf menu menu.zip

echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
echo -e "\033[1;32m ✓ Update selesai: menu + semua config layanan terbaru\033[0m"
echo -e "\033[1;36m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\033[0m"
read -n 1 -s -r -p "Press [ Enter ] to back on menu"
menu
