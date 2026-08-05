#!/bin/bash
CHATID=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 3)
KEY=$(grep -E "^#bot# " "/etc/bot/.bot.db" | cut -d ' ' -f 2)
TIME="10"
URL="https://api.telegram.org/bot$KEY/sendMessage"
clear
echo -e ""
echo -e "\033[96;1m============================\033[0m"
echo -e "\033[93;1m  INPUT DOMAIN N SUB/WILCARD "
echo -e "\033[96;1m============================\033[0m"
read -p "Masukkan email Cloudflare: " CF_EMAIL
read -p "Masukkan API Key Cloudflare: " CF_API_KEY
read -p "Masukkan subdomain (contoh: 'sub'): " SUBDOMAIN
read -p "Masukkan domain utama (contoh: 'example.com'): " DOMAIN
read -p "Masukan IP (contoh: '192.168.1.1'): " IP
echo -e ""
WILDOMAIN="$SUBDOMAIN.$DOMAIN"
wilcard="*.$WILDOMAIN"
set -euo pipefail
#domain
echo "Updating DNS for $WILDOMAIN..."
echo "Mengambil Zone ID untuk domain $DOMAIN..."
response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" \
     -H "Content-Type: application/json")

ZONE=$(echo "$response" | jq -r '.result[0].id')

if [[ -z "$ZONE" || "$ZONE" == "null" ]]; then
    echo "Gagal mengambil Zone ID. Pastikan domain $DOMAIN terdaftar di Cloudflare."
    exit 1
else
    echo "Zone ID ditemukan: $ZONE"
fi

RECORD=$(curl -sLX GET "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records?name=$WILDOMAIN" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

if [[ "${#RECORD}" -le 10 ]]; then
     RECORD=$(curl -sLX POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'$WILDOMAIN'","content":"'${IP}'","ttl":120,"proxied":false}' | jq -r .result.id)
fi

RESULT=$(curl -sLX PUT "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records/${RECORD}" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'$WILDOMAIN'","content":"'${IP}'","ttl":120,"proxied":false}')

RECORD1=$(curl -sLX GET "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records?name=${wilcard}" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" | jq -r .result[0].id)

if [[ "${#RECORD1}" -le 10 ]]; then
     RECORD1=$(curl -sLX POST "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${wilcard}'","content":"'${IP}'","ttl":120,"proxied":false}' | jq -r .result.id)
fi

RESULT=$(curl -sLX PUT "https://api.cloudflare.com/client/v4/zones/$ZONE/dns_records/${RECORD1}" \
     -H "X-Auth-Email: ${CF_EMAIL}" \
     -H "X-Auth-Key: ${CF_API_KEY}" \
     -H "Content-Type: application/json" \
     --data '{"type":"A","name":"'${wilcard}'","content":"'${IP}'","ttl":120,"proxied":false}')

# Langkah 1: Dapatkan Account ID
echo "Mengambil Account ID..."
response=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" \
     -H "Content-Type: application/json")

CF_ACCOUNT_ID=$(echo "$response" | jq -r '.result[0].id')

if [[ -z "$CF_ACCOUNT_ID" || "$CF_ACCOUNT_ID" == "null" ]]; then
    echo "Gagal mengambil Account ID. Pastikan email dan API Token benar."
    exit 1
else
    echo "Account ID ditemukan: $CF_ACCOUNT_ID"
fi

# Langkah 2: Dapatkan Zone ID berdasarkan domai
generate_worker_name() {
    local random_number=$((RANDOM % 1000))  # Angka acak antara 0 dan 99
    echo "my-worker-${random_number}"
}

# Konfigurasi
WORKER_NAME=$(generate_worker_name) 
WORKER_SCRIPT="worker.js"

# Fungsi untuk membuat file worker.js jika tidak ada
create_worker_script() {
    cat <<EOF > "$WORKER_SCRIPT"
addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
    return new Response('Hello, world!', {
        headers: { 'content-type': 'text/plain' },
    });
}
EOF
    echo "File $WORKER_SCRIPT telah dibuat dengan konten default."
}

# Periksa apakah file worker.js ada
if [[ ! -f "$WORKER_SCRIPT" ]]; then
    echo "File $WORKER_SCRIPT tidak ditemukan."
    create_worker_script  # Buat file worker.js
fi

# Langkah 1: Deploy Worker
echo "Deploying Worker..."
response=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/scripts/$WORKER_NAME" \
          -H "X-Auth-Email: $CF_EMAIL" \
          -H "X-Auth-Key: $CF_API_KEY" \
          -H "Content-Type: application/javascript" \
          --data-binary "@$WORKER_SCRIPT")

if [[ $(echo "$response" | jq -r '.success') == "true" ]]; then
    echo "Worker deployed successfully!"
else
    echo "Failed to deploy worker. Error:"
    echo "$response" | jq
    exit 1
fi

# Daftar custom domain yang ingin diikat
CUSTOM_DOMAINS=("support.zoom.us" "zoomcares.zoom.us" "partner.zoom.us" "gomarketplacecontent-cf.zoom.us" "ava.game.naver.com" "blog.webex.com" "graph.instagram.com" "io.ruangguru.com" "investors.spotify.com" "zoomgov.com" "zaintest.vuclip.com" "cache.netflix.com" "quiz.vidio.com" "quiz.staging.vidio.com" "investor.fb.com" "bimbel.ruangguru.com" "cf.shopee.co.id.sea-sw.swiftserve.com" "api.blibli.com" "bakrie.ac.id" "unnes.ac.id" "fikom.esaunggul.ac.id")

# Loop untuk mengikat setiap custom domain
for CUSTOM_DOMAIN in "${CUSTOM_DOMAINS[@]}"; do
    echo "Binding custom domain: $CUSTOM_DOMAIN..."

    # Langkah 1: Bind Custom Domain to Worker
    response=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/domains" \
         -H "X-Auth-Email: $CF_EMAIL" \
         -H "X-Auth-Key: $CF_API_KEY" \
         -H "Content-Type: application/json" \
         --data "{\"zone_id\":\"$ZONE\",\"hostname\":\"${CUSTOM_DOMAIN}.${WILDOMAIN}\",\"service\":\"$WORKER_NAME\",\"environment\":\"production\"}")

    if [[ $(echo "$response" | jq -r '.success') == "true" ]]; then
        echo "Custom domain $CUSTOM_DOMAIN bound successfully!"
    else
        echo "Failed to bind custom domain $CUSTOM_DOMAIN. Error:"
        echo "$response" | jq
    fi
done
echo "Custom domain binding process completed!"
        # Tunggu 5 menit (300 detik)
        echo "Menunggu 5 menit sebelum menghapus worker..."
        sleep 300  # 300 detik = 5 menit

        # Langkah 2: Hapus Worker
        echo "Menghapus worker $WORKER_NAME..."
        delete_response=$(curl -s -X DELETE "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/workers/scripts/$WORKER_NAME" \
             -H "X-Auth-Email: $CF_EMAIL" \
             -H "X-Auth-Key: $CF_API_KEY")

        if [[ $(echo "$delete_response" | jq -r '.success') == "true" ]]; then
            echo "Worker $WORKER_NAME berhasil dihapus!"
        else
            echo "Gagal menghapus worker $WORKER_NAME. Error:"
            echo "$delete_response" | jq
        fi
echo "Proses binding dan penghapusan worker selesai!"

# Menyalin output ke clipboard
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "🍀SUCCESSFULLY POINTING🍀"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "🌹SUBDOMAIN   : $dns" 
echo -e "🏵️WILCARD    : $wilcard" 
echo -e "🌺IP SERVER  : $IP" 
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
function notif_poin() {
CHATID="$CHATID"
KEY="$KEY"
TIME="$TIME"
URL="$URL"
TEXT="
<code>◇━━━━━━━━━━━━━━◇</code>
<b>   ⚠️POINTING NOTIF⚠️ </b>
<b>     Add Domain New  </b>
<code>◇━━━━━━━━━━━━━━◇</code>
<b>IP VPS :</b> <code>$IP </code>
<b>DOMAIN :</b> <code>$dns </code>
<b>WILCARD :</b> <code>$wilcard </code>
<code>◇━━━━━━━━━━━━━━◇</code>
<code>NEW ADD DOMAIN</code>
<code>BY BOT : @WENDIVPN_BOT</code>
"
curl -s --max-time $TIME -d "chat_id=$CHATID&disable_web_page_preview=1&text=$TEXT&parse_mode=html" $URL >/dev/null
}
notif_poin