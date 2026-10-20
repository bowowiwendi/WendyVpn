#!/bin/bash

set -euo pipefail

setup_cloudflare_dns() {
    # Update dan install packages
    apt update && apt install -y jq curl || true

    # Configuration
    local IP=$(wget --timeout=30 --tries=2 -qO- icanhazip.com)
    [[ -n "$IP" ]] || { echo "❌ Gagal mendapatkan IP publik"; exit 1; }

    # Kredensial Cloudflare TIDAK ditulis lagi di dalam script ini.
    # WAJIB diisi oleh pemilik VPS sendiri sebelum memakai fitur DNS/Cloudflare:
    # buat file /root/.cf_key berisi dua baris:
    #   CF_ID=email-akun-cloudflare-kamu
    #   CF_KEY=global-api-key-kamu
    # Alternatif: ekspor variabel CF_ID dan CF_KEY dari lingkungan (environment).
    local CF_ID="${CF_ID:-}"
    local CF_KEY="${CF_KEY:-}"
    if [ -f /root/.cf_key ]; then
        . /root/.cf_key
    fi
    local sub=$(</dev/urandom tr -dc a-z0-9 | head -c5)

    # Pilih zone aktif pertama dari daftar (bisa dioverride via CF_DOMAIN)
    local domain=""
    local zone_id=""
    local zones=("${CF_DOMAIN:-hamidstore.my.id}" hamidstore.my.id shifastore.my.id)
    for d in "${zones[@]}"; do
        echo "⏳ Cek zone $d..."
        local response=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones?name=$d&status=active" \
            -H "X-Auth-Email: $CF_ID" \
            -H "X-Auth-Key: $CF_KEY" \
            -H "Content-Type: application/json")
        zone_id=$(echo "$response" | jq -r .result[0].id 2>/dev/null || true)
        if [[ -n "$zone_id" && "$zone_id" != "null" ]]; then
            domain="$d"
            break
        fi
    done
    if [[ -z "$domain" ]]; then
        echo "❌ Tidak ada zone aktif yang tersedia (periksa CF_DOMAIN / API key)."
        exit 1
    fi
    echo "✅ Zone dipakai: $domain"

    local dns="$sub.$domain"

    echo "🔧 Creating A record for $dns..."
    response=$(curl --connect-timeout 30 -sLX POST "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records" \
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
    mkdir -p /etc/xray /var/lib/kyt
    echo "IP=$IP" > /var/lib/kyt/ipvps.conf
    echo $dns > /etc/xray/scdomain
    echo $dns > /etc/xray/domain
    echo $dns > /root/domain

    echo "✅ DNS setup completed successfully!"
    echo "Domain: $dns"
    echo "IP: $IP"
}

# Jalankan fungsi
setup_cloudflare_dns
