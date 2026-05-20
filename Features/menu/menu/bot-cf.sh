#!/bin/bash

# Konfigurasi
API_TOKEN="your_cloudflare_api_token"
ZONE_ID="your_zone_id"
DOMAIN="example.com"  # Ganti dengan domain Anda

# Fungsi untuk menampilkan bantuan
usage() {
  echo "Usage: $0 [list|add|delete] [wildcard_pattern] [ip_address]"
  echo "Example:"
  echo "  $0 list '*'"               # List semua records
  echo "  $0 add '*.example.com' 1.2.3.4"  # Tambahkan wildcard record
  echo "  $0 delete '*.example.com'" # Hapus wildcard record
  exit 1
}

# Fungsi untuk list DNS records berdasarkan wildcard
list_records() {
  wildcard=$1
  echo "Listing records matching: $wildcard"
  curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$wildcard" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" | jq .
}

# Fungsi untuk menambahkan DNS record
add_record() {
  wildcard=$1
  ip_address=$2
  echo "Adding record: $wildcard -> $ip_address"
  curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"A\",\"name\":\"$wildcard\",\"content\":\"$ip_address\",\"ttl\":120,\"proxied\":false}" | jq .
}

# Fungsi untuk menghapus DNS record
delete_record() {
  wildcard=$1
  echo "Deleting records matching: $wildcard"
  records=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$wildcard" \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[].id')

  for record_id in $records; do
    echo "Deleting record ID: $record_id"
    curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$record_id" \
      -H "Authorization: Bearer $API_TOKEN" \
      -H "Content-Type: application/json" | jq .
  done
}

# Main script
if [ $# -lt 1 ]; then
  usage
fi

ACTION=$1
WILDCARD=$2
IP_ADDRESS=$3

case $ACTION in
  list)
    list_records "$WILDCARD"
    ;;
  add)
    if [ -z "$WILDCARD" ] || [ -z "$IP_ADDRESS" ]; then
      echo "Error: Wildcard and IP address are required for adding a record."
      usage
    fi
    add_record "$WILDCARD" "$IP_ADDRESS"
    ;;
  delete)
    if [ -z "$WILDCARD" ]; then
      echo "Error: Wildcard is required for deleting a record."
      usage
    fi
    delete_record "$WILDCARD"
    ;;
  *)
    echo "Error: Invalid action."
    usage
    ;;
esac