#!/bin/bash
apt install jq curl -y
domain=ssh-prem.xyz
sub=$(</dev/urandom tr -dc a-z0-9 | head -c5)
IP=$(wget --timeout=30 --tries=2 -qO- icanhazip.com)
# Kredensial Cloudflare TIDAK ditulis lagi di dalam script ini.
# WAJIB diisi oleh pemilik VPS sendiri sebelum memakai fitur DNS/Cloudflare:
# buat file /root/.cf_key berisi dua baris:
#   CF_ID=email-akun-cloudflare-kamu
#   CF_KEY=global-api-key-kamu
# Alternatif: ekspor variabel CF_ID dan CF_KEY dari lingkungan (environment).
CF_ID="${CF_ID:-}"
CF_KEY="${CF_KEY:-}"
if [ -f /root/.cf_key ]; then
    . /root/.cf_key
fi
dns=${sub}.${domain}
wilcard=*.${dns}
set -euo pipefail
#domain
echo "Updating DNS for ${dns}..."
ZONE=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones?name=${domain}&status=active" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

RECORD=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records?name=${dns}" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

if [[ "${#RECORD}" -le 10 ]]; then
     RECORD=$(curl --connect-timeout 30 -sLX POST "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${dns}'","content":"'${IP}'","ttl":120,"proxied":false}' | jq -r .result.id)
fi

RESULT=$(curl --connect-timeout 30 -sLX PUT "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records/${RECORD}" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${dns}'","content":"'${IP}'","ttl":120,"proxied":false}')
#wilcard
ZONE=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones?name=${domain}&status=active" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

RECORD=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records?name=${wilcard}" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

if [[ "${#RECORD}" -le 10 ]]; then
     RECORD=$(curl --connect-timeout 30 -sLX POST "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${wilcard}'","content":"'${IP}'","ttl":120,"proxied":false}' | jq -r .result.id)
fi

RESULT=$(curl --connect-timeout 30 -sLX PUT "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records/${RECORD}" \
     -H "X-Auth-Email: ${CF_ID}" \
     -H "X-Auth-Key: ${CF_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${wilcard}'","content":"'${IP}'","ttl":120,"proxied":false}')
     
echo $dns > /etc/xray/scdomain
echo $dns > /etc/v2ray/domain
echo $dns > /root/domain
echo $dns > /root/scdomain
echo $dns > /etc/xray/domain
echo "IP=" >> /var/lib/kyt/ipvps.conf
cd
