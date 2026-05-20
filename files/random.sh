#!/bin/bash

setup_cloudflare_dns() {
    # Update dan install packages
    apt update && apt install -y jq curl
    
    # Configuration
    local domain="sahvip.web.id"
    local sub=$(</dev/urandom tr -dc a-z0-9 | head -c5)
    local IP=$(wget -qO- icanhazip.com)
    local CF_KEY="dc7a32077573505cc082f4be752509a5c5a3e"
    local CF_ID="bowowiwendi@gmail.com"
    local dns="$sub.$domain"
    
    set -euo pipefail
    
    # Get Zone ID
    echo "⏳ Configuring Cloudflare DNS records..."
    local response=$(curl -sLX GET "https://api.cloudflare.com/client/v4/zones?name=$domain&status=active" \
    -H "X-Auth-Email: $CF_ID" \
    -H "X-Auth-Key: $CF_KEY" \
    -H "Content-Type: application/json")
    local zone_id=$(echo "$response" | jq -r .result[0].id)
    if [[ -z "$zone_id" || "$zone_id" == "null" ]]; then
        echo "❌ Failed to get zone ID for $domain"
        exit 1
    fi
    
    # Create A Record
    echo "🔧 Creating A record for $dns..."
    response=$(curl -sLX POST "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records" \
    -H "X-Auth-Email: $CF_ID" \
    -H "X-Auth-Key: $CF_KEY" \
    -H "Content-Type: application/json" \
    --data '{"type":"A","name":"'$dns'","content":"'$IP'","ttl":120,"proxied":false}')
    local record_id=$(echo "$response" | jq -r .result.id)
    if [[ -z "$record_id" || "$record_id" == "null" ]]; then
        echo "❌ Failed to create A record for $dns"
        echo "$response"
        exit 1
    fi
    
    # Save domain info
    mkdir -p /etc/xray
    echo "IP=" >> /var/lib/kyt/ipvps.conf
    echo $dns > /etc/xray/scdomain
    echo $dns > /etc/xray/domain
    echo $dns > /root/domain
    
    echo "✅ DNS setup completed successfully!"
    echo "Domain: $dns"
    echo "IP: $IP"
}

# Jalankan fungsi
setup_cloudflare_dns