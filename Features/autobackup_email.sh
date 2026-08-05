#!/bin/bash
# SL
# ==========================================
# Color
RED='\033[0;31m'
NC='\033[0m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LIGHT='\033[0;37m'
# ==========================================
# Getting
clear
IP=$(wget -qO- ipinfo.io/ip)
date=$(date +"%Y-%m-%d")
Green_font_prefix="\033[32m" && Red_font_prefix="\033[31m" && Green_background_prefix="\033[42;37m" && Red_background_prefix="\033[41;37m" && Font_color_suffix="\033[0m"
Info="${Green_font_prefix}[ON]${Font_color_suffix}"
Error="${Red_font_prefix}[OFF]${Font_color_suffix}"

# Check cron status
cek=$(grep -c -E "^# BEGIN_Backup" /etc/crontab)
if [[ "$cek" = "1" ]]; then
    sts="${Info}"
else
    sts="${Error}"
fi

# Check and install dependencies
function check_dependencies() {
    if ! command -v msmtp &> /dev/null; then
        echo "Installing msmtp..."
        apt-get update && apt-get install -y msmtp mailutils
    fi
    if ! command -v mail &> /dev/null; then
        echo "Installing mailutils..."
        apt-get install -y mailutils
    fi
}

# Start autobackup
function start() {
    check_dependencies
    if [[ ! -f /home/email ]]; then
        echo "Please enter your email for receiving backups"
        read -rp "Email: " -e email
        echo "$email" > /home/email
    fi
    cat > /etc/crontab << EOF
# BEGIN_Backup
5 0 * * * root backup
# END_Backup
EOF
    systemctl restart cron
    sleep 1
    echo "Autobackup Has Been Started"
    echo "Data Will Be Backed Up Automatically at 00:05 GMT +7"
    exit 0
}

# Stop autobackup
function stop() {
    sed -i "/^# BEGIN_Backup/,/^# END_Backup/d" /etc/crontab
    systemctl restart cron
    sleep 1
    echo "Autobackup Has Been Stopped"
    if [[ -f /home/email ]]; then
        rm -f /home/email
    fi
    exit 0
}

# Change recipient email
function gantipenerima() {
    echo "Please enter your email for receiving backups"
    read -rp "Email: " -e email
    echo "$email" > /home/email
    echo "Recipient email updated successfully"
}

# Change sender email and configure msmtp
function gantipengirim() {
    echo "Please enter your Gmail address"
    read -rp "Email: " -e email
    echo "Please create an App Password for this Gmail account."
    echo "Follow these steps:"
    echo "1. Go to https://myaccount.google.com/security"
    echo "2. Enable 2-Step Verification if not already enabled"
    echo "3. Go to 'App passwords', select 'Mail' and 'Other', then generate"
    echo "4. Copy the 16-character App Password"
    read -rp "App Password: " -e pwdd
    rm -rf /etc/msmtprc
    cat > /etc/msmtprc <<EOF
defaults
tls on
tls_starttls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
account default
host smtp.gmail.com
port 587
auth on
user $email
from $email
password $pwdd
logfile /var/log/msmtp.log
EOF
    chmod 600 /etc/msmtprc
    chown root:root /etc/msmtprc
    touch /var/log/msmtp.log
    chmod 664 /var/log/msmtp.log
    echo "Sender email configuration updated"
}

# Test email sending
function testemail() {
    check_dependencies
    if [[ ! -f /home/email ]]; then
        echo "No recipient email set. Please set it first."
        gantipenerima
    fi
    if [[ ! -f /etc/msmtprc ]]; then
        echo "No sender email configured. Please configure it first."
        gantipengirim
    fi
    email=$(cat /home/email)
    echo -e "This is a test email from your VPS\nIP VPS: $IP\nDate: $date" | mail -s "Test Email from VPS" "$email"
    if [[ $? -eq 0 ]]; then
        echo "Test email sent successfully to $email"
    else
        echo "Failed to send test email. Check /var/log/msmtp.log for details."
        if [[ -f /var/log/msmtp.log ]]; then
            echo "Recent log entries:"
            tail -n 10 /var/log/msmtp.log
        fi
    fi
}

# Main menu
clear
echo -e "=============================="
echo -e "     Autobackup Data $sts     "
echo -e "=============================="
echo -e "1. Start Autobackup"
echo -e "2. Stop Autobackup"
echo -e "3. Change Recipient Email"
echo -e "4. Change Sender Email"
echo -e "5. Test Email Sending"
echo -e "=============================="
read -rp "Please Enter The Correct Number: " -e num
case $num in
1) start ;;
2) stop ;;
3) gantipenerima ;;
4) gantipengirim ;;
5) testemail ;;
*) clear ;;
esac