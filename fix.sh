#!/bin/bash
apt-get install dropbear -y >/dev/null 2>&1
wget -q -O /etc/default/dropbear "https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/cfg_conf_js/dropbear.conf"
chmod +x /etc/default/dropbear
/etc/init.d/dropbear restart
/etc/init.d/dropbear status
