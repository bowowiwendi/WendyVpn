#!/bin/bash
apt update && apt install -y jq curl

# Configuration
domain="sahvip.web.id"
sub=$(</dev/urandom tr -dc a-z0-9 | head -c5)
IP=$(wget -qO- icanhazip.com)
CF_KEY="dc7a32077573505cc082f4be752509a5c5a3e"
CF_ID="bowowiwendi@gmail.com"

dns="${sub}.${domain}"

set -euo pipefail

# Cloudflare API Functions
get_zone_id() {
    response=$(curl -sLX GET "https://api.cloudflare.com/client/v4/zones?name=${domain}&status=active" \
    -H "X-Auth-Email: ${CF_ID}" \
    -H "X-Auth-Key: ${CF_KEY}" \
    -H "Content-Type: application/json")
    zone_id=$(echo "$response" | jq -r .result[0].id)
    if [[ -z "$zone_id" || "$zone_id" == "null" ]]; then
        echo "❌ Failed to get zone ID for ${domain}"
        exit 1
    fi
    echo "$zone_id"
}

create_record() {
    local type=$1 name=$2 content=$3
    response=$(curl -sLX POST "https://api.cloudflare.com/client/v4/zones/${ZONE}/dns_records" \
    -H "X-Auth-Email: ${CF_ID}" \
    -H "X-Auth-Key: ${CF_KEY}" \
    -H "Content-Type: application/json" \
    --data '{"type":"'${type}'","name":"'${name}'","content":"'${content}'","ttl":120,"proxied":false}')
    record_id=$(echo "$response" | jq -r .result.id)
    if [[ -z "$record_id" || "$record_id" == "null" ]]; then
        echo "❌ Failed to create ${type} record for ${name}"
        echo "$response"
        exit 1
    fi
    echo "$record_id"
}

# Main DNS Setup
echo "⏳ Configuring Cloudflare DNS records..."
ZONE=$(get_zone_id)

echo "🔧 Creating A record for ${dns}..."
create_record A "${dns}" "${IP}"

# Save domain info
mkdir -p /etc/xray
echo "IP=" >> /var/lib/kyt/ipvps.conf
echo ${dns} > /etc/xray/scdomain
echo ${dns} > /etc/xray/domain
echo ${dns} > /root/domain

echo "✅ DNS Setup Complete!"
echo "   Subdomain: ${dns}"
echo "   Please wait for DNS propagation (5-15 minutes)"