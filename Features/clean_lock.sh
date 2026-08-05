#!/bin/bash

# File target
LOCK_FILE="/etc/xray/.lock.db"

# Hapus file jika ada
if [ -f "$LOCK_FILE" ]; then
    rm -f "$LOCK_FILE"
    echo "[$(date)] File $LOCK_FILE dihapus."
fi

# Buat file baru dengan konten yang ditentukan
cat > "$LOCK_FILE" <<EOF
#vmess
#vless
#trojan
#ss
EOF

echo "[$(date)] File $LOCK_FILE telah direset."