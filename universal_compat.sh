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

# ============================================================
# 4. Deteksi OS (Debian & Ubuntu, semua versi)
#    Mengisi: COMPAT_OS_ID, COMPAT_OS_VER, COMPAT_OS_CODENAME
# ============================================================
compat_detect_os() {
    COMPAT_OS_ID="unknown"; COMPAT_OS_VER="0"; COMPAT_OS_CODENAME=""
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        COMPAT_OS_ID="${ID:-unknown}"
        COMPAT_OS_VER="${VERSION_ID:-0}"
        COMPAT_OS_CODENAME="${VERSION_CODENAME:-}"
    fi
    export COMPAT_OS_ID COMPAT_OS_VER COMPAT_OS_CODENAME
}
compat_detect_os

# Bandingkan versi: compat_ver_ge "22.04" -> true jika OS_VER >= 22.04
compat_ver_ge() {
    [ "$(printf '%s\n%s' "$1" "$COMPAT_OS_VER" | sort -V | head -n1)" = "$1" ]
}

# ============================================================
# 5. Install paket apt yang portable lintas versi
#    compat_apt_install pkg1 [pkg2 ...]  -> install semua (gagal -> return 1)
#    compat_apt_try "paket-a" "paket-b"  -> coba berurutan, berhenti saat sukses
# ============================================================
compat_apt_install() {
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends "$@" \
        || DEBIAN_FRONTEND=noninteractive apt-get install -y "$@"
}
compat_apt_try() {
    local p
    for p in "$@"; do
        if apt-cache show "$p" >/dev/null 2>&1; then
            if compat_apt_install "$p" >/dev/null 2>&1; then
                return 0
            fi
        fi
    done
    return 1
}
# Nama paket yang berbeda antar versi:
#   7zip (Ubuntu 24.04+/Debian 13+) vs p7zip-full (lama)
compat_install_7zip()   { compat_apt_try "7zip" "p7zip-full"; }
#   netfilter-persistent (baru) vs iptables-persistent (lama)
compat_install_netfilter() { compat_apt_try "netfilter-persistent" "iptables-persistent"; }
# Simpan aturan firewall dengan perintah yang tersedia
compat_firewall_save() {
    if command -v netfilter-persistent >/dev/null 2>&1; then
        netfilter-persistent save >/dev/null 2>&1
    elif command -v iptables-persistent >/dev/null 2>&1; then
        iptables-persistent save >/dev/null 2>&1
    else
        mkdir -p /etc/iptables
        iptables-save > /etc/iptables/rules.v4 2>/dev/null
        ip6tables-save > /etc/iptables/rules.v6 2>/dev/null
    fi
}

# ============================================================
# 6. pip yang aman di semua versi (PEP 668: Debian 12+/Ubuntu 23.04+)
#    compat_pip_install -r requirements.txt  /  compat_pip_install flask
# ============================================================
compat_pip_install() {
    if pip3 install "$@" >/dev/null 2>&1; then return 0; fi
    # pip baru menolak install ke system python tanpa flag ini
    if pip3 install --break-system-packages "$@" >/dev/null 2>&1; then return 0; fi
    return 1
}

# ============================================================
# 7. Kontrol service yang portable (systemctl -> service -> init.d)
#    compat_service restart ssh
# ============================================================
compat_service() {
    local action="$1" name="$2"
    if command -v systemctl >/dev/null 2>&1 && [ -d /run/systemd/system ]; then
        systemctl "$action" "$name" 2>/dev/null && return 0
    fi
    if command -v service >/dev/null 2>&1; then
        service "$name" "$action" 2>/dev/null && return 0
    fi
    if [ -x "/etc/init.d/$name" ]; then
        "/etc/init.d/$name" "$action" 2>/dev/null && return 0
    fi
    return 1
}

# ============================================================
# 8. Unit OpenVPN yang portable
#    Debian <=10 pakai openvpn@, Debian 11+/Ubuntu 20.04+ pakai openvpn-server@
#    compat_openvpn_unit server-tcp  -> "openvpn-server@server-tcp" atau "openvpn@server-tcp"
# ============================================================
compat_openvpn_unit() {
    local inst="$1"
    if [ -f /lib/systemd/system/openvpn-server@.service ] || [ -f /etc/systemd/system/openvpn-server@.service ]; then
        echo "openvpn-server@${inst}"
    else
        echo "openvpn@${inst}"
    fi
}

# ============================================================
# 9. Pastikan python3-venv tersedia (dibutuhkan venv di Debian 12+/Ubuntu 24.04)
# ============================================================
compat_ensure_venv() {
    if python3 -c "import venv" 2>/dev/null; then return 0; fi
    compat_apt_install python3-venv >/dev/null 2>&1
    python3 -c "import venv" 2>/dev/null
}
