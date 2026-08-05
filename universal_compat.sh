#!/bin/bash
# Function: Universal Compatibility Wrapper
# Compatibility: Ubuntu 20-24+, Debian 10-12+

# 1. Mendeteksi & Menginstal Dependensi Dasar (Net-tools)
check_net_tools() {
    if ! command -v ifconfig &> /dev/null; then
        echo "[INFO] ifconfig tidak ditemukan, menginstal net-tools untuk kompatibilitas..."
        apt-get update && apt-get install -y net-tools iproute2 >/dev/null 2>&1
    fi
}

# 2. Python Venv Wrapper (PEP 668 Compatibility)
# Penggunaan: run_python_bot "direktori_bot" "perintah_pip"
run_python_bot() {
    local BOT_DIR=$1
    local PIP_CMD=$2
    
    if [ ! -d "$BOT_DIR/venv" ]; then
        echo "[INFO] Membuat virtual environment di $BOT_DIR..."
        python3 -m venv "$BOT_DIR/venv"
    fi
    
    source "$BOT_DIR/venv/bin/activate"
    if [ -n "$PIP_CMD" ]; then
        pip install --upgrade pip >/dev/null 2>&1
        pip install $PIP_CMD >/dev/null 2>&1
    fi
}

# 3. Alias untuk perintah deprecated agar skrip lama tetap jalan
setup_compat_aliases() {
    if command -v ip &> /dev/null; then
        alias ifconfig='ip addr' 2>/dev/null
        alias route='ip route' 2>/dev/null
    fi
}

# Inisialisasi
check_net_tools
setup_compat_aliases
