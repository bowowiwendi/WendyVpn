#!/bin/bash

set -euo pipefail

setup_cloudflare_dns() {
    # Update dan install packages
    apt update && apt install -y jq curl || true

    # Configuration
    local IP=$(wget --timeout=30 --tries=2 -qO- icanhazip.com)
    [[ -n "$IP" ]] || { echo "❌ Gagal mendapatkan IP publik"; exit 1; }

    # Kredensial Cloudflare TIDAK ditulis di dalam script ini.
    # WAJIB diisi oleh pemilik VPS sendiri sebelum memakai fitur DNS/Cloudflare:
    # buat file /root/.cf_key berisi salah satu pola berikut:
    #   CF_TOKEN=api-token-cloudflare-kamu            (cara token)
    # atau:
    #   CF_ID=email-akun-cloudflare-kamu
    #   CF_KEY=global-api-key-kamu
    # Alternatif: ekspor variabel-variabel itu dari lingkungan (environment).
    # CF_DOMAIN opsional: isi untuk memaksa satu domain tertentu; bila kosong,
    # script memilih otomatis dari daftar domain aktif di akun Cloudflare kamu.
    local CF_ID="${CF_ID:-}"
    local CF_KEY="${CF_KEY:-}"
    local CF_TOKEN="${CF_TOKEN:-}"
    if [ -f /root/.cf_key ]; then
        . /root/.cf_key
    fi
    local AUTH=()
    if [[ -n "$CF_TOKEN" ]]; then
        AUTH=(-H "Authorization: Bearer $CF_TOKEN")
    elif [[ -n "$CF_ID" && -n "$CF_KEY" ]]; then
        AUTH=(-H "X-Auth-Email: $CF_ID" -H "X-Auth-Key: $CF_KEY")
    else
        echo "❌ Kredensial Cloudflare belum diisi: buat /root/.cf_key berisi CF_TOKEN, atau CF_ID + CF_KEY."
        exit 1
    fi
    local sub=$(</dev/urandom tr -dc a-z0-9 | head -c5)

    # Ambil daftar zone aktif dari akun Cloudflare pemilik VPS ini, lalu pilih:
    # CF_DOMAIN bila diisi (divalidasi ada di daftar), selain itu zone pertama.
    echo "⏳ Mengambil daftar domain aktif dari akun Cloudflare kamu..."
    local zone_list=$(curl --connect-timeout 30 -sLX GET "https://api.cloudflare.com/client/v4/zones?status=active&per_page=50" \
        "${AUTH[@]}" \
        -H "Content-Type: application/json")
    local zone_count=$(echo "$zone_list" | jq -r '.result | length' 2>/dev/null || echo 0)
    if [[ "$zone_count" == "0" || "$zone_count" == "null" ]]; then
        echo "❌ Tidak ada domain aktif di akun Cloudflare ini (atau kredensial salah). Tambahkan domain ke Cloudflare dulu, atau periksa /root/.cf_key."
        exit 1
    fi
    local domain=""
    local zone_id=""
    if [[ -n "${CF_DOMAIN:-}" ]]; then
        zone_id=$(echo "$zone_list" | jq -r --arg d "$CF_DOMAIN" '.result[] | select(.name==$d) | .id' 2>/dev/null | head -1 || true)
        if [[ -n "$zone_id" && "$zone_id" != "null" ]]; then
            domain="$CF_DOMAIN"
        else
            echo "❌ CF_DOMAIN=$CF_DOMAIN tidak termasuk domain aktif akun ini. Yang tersedia:"
            echo "$zone_list" | jq -r '.result[].name' 2>/dev/null | sed 's/^/   - /'
            exit 1
        fi
    else
        domain=$(echo "$zone_list" | jq -r '.result[0].name' 2>/dev/null || true)
        zone_id=$(echo "$zone_list" | jq -r '.result[0].id' 2>/dev/null || true)
    fi
    if [[ -z "$domain" || -z "$zone_id" || "$zone_id" == "null" ]]; then
        echo "❌ Gagal menentukan domain Cloudflare."
        exit 1
    fi
    echo "✅ Domain dipakai: $domain (dari $zone_count domain aktif di akunmu)"

    local dns="$sub.$domain"

    echo "🔧 Creating A record for $dns..."
    local response=$(curl --connect-timeout 30 -sLX POST "https://api.cloudflare.com/client/v4/zones/$zone_id/dns_records" \
        "${AUTH[@]}" \
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
