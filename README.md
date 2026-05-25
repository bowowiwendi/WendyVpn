# WendyVpn — Multi-Port VPN Tunnel & Telegram Bot

All-in-one VPN tunneling script with Telegram bot management (kyt). Supports SSH, VMess, VLess, Trojan, Shadowsocks, OpenVPN, and SlowDNS.

## Installation

### 1. System Prep
```bash
# Debian
apt update -y && apt upgrade -y && apt dist-upgrade -y && reboot

# Ubuntu
apt update && apt upgrade -y && update-grub && sleep 2 && reboot
```

### 2. Install Script
```bash
sysctl -w net.ipv6.conf.all.disable_ipv6=1 && sysctl -w net.ipv6.conf.default.disable_ipv6=1 && apt update -y && apt upgrade -y && apt install -y bzip2 gzip coreutils screen curl unzip && apt install lolcat -y && gem install lolcat && wget -q https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/setup-main.sh && chmod +x setup-main.sh && sed -i -e 's/\r$//' setup-main.sh && screen -S setupku ./setup-main.sh
```

### 3. Bot Telegram (kyt)
```bash
wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/refs/heads/ABSTRAK/bot/install.sh && chmod +x install.sh && ./install.sh
```

### 4. Update Script
```bash
wget https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/files/update.sh && chmod +x update.sh && ./update.sh
```

## Features

| Feature | Description |
|---|---|
| Multi-protocol | SSH WS/TLS, VMess, VLess, Trojan, Shadowsocks, OpenVPN, SlowDNS |
| Telegram Bot | User panel, top-up via QRIS (bayar.gg), admin management |
| Auto Backup | Database bot dikirim ke admin 2x sehari via Telegram |
| Restore DB | Restore database bot dari file Telegram |
| Payment | QRIS otomatis via bayar.gg API |
| Trial System | 1-hour free trial per user per day |

## Supported OS & Arch

| OS | Versions |
|---|---|
| Ubuntu | 20.04, 22.04, 24.04+ |
| Debian | 10, 11, 12+ |

| Architecture | Support |
|---|---|
| x86_64 | ✅ |
| aarch64 / arm64 | ✅ |

## Port Info

```
- TROJAN WS         443, 8443
- TROJAN GRPC       443, 8443
- SHADOWSOCKS WS    443, 8443
- SHADOWSOCKS GRPC  443, 8443
- VLESS WSS         443, 8443
- VLESS GRPC        443, 8443
- VLESS NONTLS      80, 8080, 8880, 2082
- VMESS WS          443, 8443
- VMESS GRPC        443, 8443
- VMESS NONTLS      80, 8080, 8880, 2082
- SSH WS / TLS      443, 8443
- SSH NON TLS       8880, 80, 8080, 2082, 2095, 2086
- OVPN SSL/TCP      1194
- SLOWDNS           5300
```

## Bot Commands (Telegram)

| Command | Description |
|---|---|
| `/menu` | Admin panel |
| `/start` | User panel |
| Setting → **📦 DB Backup** | Auto backup database ke admin |
| Setting → **📦 DB Backup → Restore DB** | Restore database dari file |

## Contact

- Telegram: [@WendiVpn](https://t.me/WendiVpn)
- WhatsApp: 083153170199
