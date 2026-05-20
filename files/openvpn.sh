#!/bin/bash
# Decrypted by LT | FUSCATOR
# Github- https://github.com/LunaticTunnel/Absurd  
# Disesuaikan untuk Ubuntu 24.04

export DEBIAN_FRONTEND=noninteractive
OS=`uname -m`;
MYIP=$(wget -qO- ipinfo.io/ip);
domain=$(cat /root/domain)
MYIP2="s/xxxxxxxxx/$domain/g";

function ovpn_install() {
    echo "Menginstal dan mengekstrak konfigurasi OpenVPN..."
    rm -rf /etc/openvpn
    mkdir -p /etc/openvpn
    # Perbaiki URL dengan menambahkan https://
    wget -O /etc/openvpn/vpn.zip "https://raw.githubusercontent.com/LunaticTunnel/Azerd/ABSTRAK/ovpn/vpn.zip" >/dev/null 2>&1
    unzip -d /etc/openvpn/ /etc/openvpn/vpn.zip
    rm -f /etc/openvpn/vpn.zip
    # Pastikan kepemilikan direktori easy-rsa benar
    if [ -d "/etc/openvpn/server/easy-rsa/" ]; then
        chown -R root:root /etc/openvpn/server/easy-rsa/
        echo "Kepemilikan /etc/openvpn/server/easy-rsa/ diatur ke root:root."
    else
        echo "Peringatan: Direktori /etc/openvpn/server/easy-rsa/ tidak ditemukan."
    fi
    echo "Instalasi OpenVPN awal selesai."
}

function config_easy() {
    echo "Mengkonfigurasi OpenVPN..."
    cd
    
    # Buat direktori plugin jika belum ada dan salin plugin PAM dengan penanganan error
    mkdir -p /usr/lib/openvpn/
    PLUGIN_SOURCE="/usr/lib/x86_64-linux-gnu/openvpn/plugins/openvpn-plugin-auth-pam.so"
    PLUGIN_DEST="/usr/lib/openvpn/openvpn-plugin-auth-pam.so"
    if [[ -f "$PLUGIN_SOURCE" ]]; then
        cp "$PLUGIN_SOURCE" "$PLUGIN_DEST"
        echo "Plugin PAM disalin ke $PLUGIN_DEST"
    else
        echo "Peringatan: Plugin PAM tidak ditemukan di $PLUGIN_SOURCE. Pastikan paket openvpn-plugin-auth-pam telah diinstal dan path-nya benar."
        # Catatan: Anda mungkin perlu menyesuaikan path dalam file konfigurasi .conf nanti jika penyalinan gagal
    fi
    chmod 755 /usr/lib/openvpn/ # Pastikan direktori dapat diakses
    
    # Aktifkan autostart (ini untuk konfigurasi lama, mungkin tidak diperlukan lagi)
    sed -i 's/#AUTOSTART="all"/AUTOSTART="all"/g' /etc/default/openvpn
    echo "Konfigurasi /etc/default/openvpn diperbarui."

    # Aktifkan dan mulai instance server spesifik
    # Pastikan server-tcp.conf dan server-udp.conf ada di /etc/openvpn/server/
    # Kita asumsikan nama file konfigurasinya adalah server-tcp.conf dan server-udp.conf
    echo "Mengaktifkan dan memulai layanan openvpn-server@server-tcp..."
    systemctl enable --now openvpn-server@server-tcp || echo "Peringatan: Gagal mengaktifkan/memulai openvpn-server@server-tcp"
    
    echo "Mengaktifkan dan memulai layanan openvpn-server@server-udp..."
    systemctl enable --now openvpn-server@server-udp || echo "Peringatan: Gagal mengaktifkan/memulai openvpn-server@server-udp"
    
    # Ganti /etc/init.d/openvpn restart dengan systemctl
    # Merestart instance spesifik yang telah diaktifkan:
    echo "Merestart layanan OpenVPN server..."
    systemctl restart openvpn-server@server-tcp || echo "Peringatan: Gagal merestart openvpn-server@server-tcp"
    systemctl restart openvpn-server@server-udp || echo "Peringatan: Gagal merestart openvpn-server@server-udp"
    # Atau, alternatifnya, restart semua instance server:
    # systemctl restart 'openvpn-server@*' || echo "Peringatan: Gagal merestart beberapa atau semua instance openvpn-server@*"
    
    echo "Konfigurasi OpenVPN selesai."
}

function make_follow() {
    echo "Mengkonfigurasi IP forwarding dan file .ovpn..."
    # Aktifkan IP forwarding
    echo 1 > /proc/sys/net/ipv4/ip_forward
    sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g' /etc/sysctl.conf
    echo "IP forwarding diaktifkan."

    # Buat file konfigurasi client
    cat > /etc/openvpn/tcp.ovpn <<-END
client
dev tun
proto tcp
remote xxxxxxxxx 1194
resolv-retry infinite
route-method exe
nobind
persist-key
persist-tun
auth-user-pass
comp-lzo
verb 3
END
    sed -i $MYIP2 /etc/openvpn/tcp.ovpn;

    cat > /etc/openvpn/udp.ovpn <<-END
client
dev tun
proto udp
remote xxxxxxxxx 2200
resolv-retry infinite
route-method exe
nobind
persist-key
persist-tun
auth-user-pass
comp-lzo
verb 3
END
    sed -i $MYIP2 /etc/openvpn/udp.ovpn;

    cat > /etc/openvpn/ws-ssl.ovpn <<-END
client
dev tun
proto tcp
remote xxxxxxxxx 443
resolv-retry infinite
route-method exe
nobind
persist-key
persist-tun
auth-user-pass
comp-lzo
verb 3
END
    sed -i $MYIP2 /etc/openvpn/ws-ssl.ovpn;

    cat > /etc/openvpn/ssl.ovpn <<-END
client
dev tun
proto tcp
remote xxxxxxxxx 443
resolv-retry infinite
route-method exe
nobind
persist-key
persist-tun
auth-user-pass
comp-lzo
verb 3
END
    sed -i $MYIP2 /etc/openvpn/ssl.ovpn;
    
    echo "File konfigurasi client (.ovpn) dibuat."
}

function cert_ovpn() {
    echo "Menambahkan sertifikat CA ke file .ovpn dan membuat arsip..."
    # Tambahkan CA cert ke file konfigurasi client
    echo '<ca>' >> /etc/openvpn/tcp.ovpn
    cat /etc/openvpn/server/ca.crt >> /etc/openvpn/tcp.ovpn
    echo '</ca>' >> /etc/openvpn/tcp.ovpn
    cp /etc/openvpn/tcp.ovpn /var/www/html/tcp.ovpn

    echo '<ca>' >> /etc/openvpn/udp.ovpn
    cat /etc/openvpn/server/ca.crt >> /etc/openvpn/udp.ovpn
    echo '</ca>' >> /etc/openvpn/udp.ovpn
    cp /etc/openvpn/udp.ovpn /var/www/html/udp.ovpn

    echo '<ca>' >> /etc/openvpn/ws-ssl.ovpn
    cat /etc/openvpn/server/ca.crt >> /etc/openvpn/ws-ssl.ovpn
    echo '</ca>' >> /etc/openvpn/ws-ssl.ovpn
    cp /etc/openvpn/ws-ssl.ovpn /var/www/html/ws-ssl.ovpn

    # PERBAIKI: Kesalahan ketik dan file yang salah disalin
    # SALAH: echo '</ca>' >> /etc/openvpn/ssl.ovpn # Ini menutup tag yang tidak dibuka
    # SALAH: cp /etc/openvpn/ws-ssl.ovpn /var/www/html/ssl.ovpn # Ini menyalin ws-ssl.ovpn ke ssl.ovpn
    # BENAR:
    echo '<ca>' >> /etc/openvpn/ssl.ovpn # Buka tag <ca>
    cat /etc/openvpn/server/ca.crt >> /etc/openvpn/ssl.ovpn
    echo '</ca>' >> /etc/openvpn/ssl.ovpn # Tutup tag <ca>
    cp /etc/openvpn/ssl.ovpn /var/www/html/ssl.ovpn # Salin file ssl.ovpn yang benar

    # Buat arsip ZIP
    cd /var/www/html/
    zip Kyt-Project.zip tcp.ovpn udp.ovpn ssl.ovpn ws-ssl.ovpn > /dev/null 2>&1
    cd
    
    # Buat halaman index.html
    cat <<'mySiteOvpn' > /var/www/html/index.html
<!DOCTYPE html>
<html lang="en">
<!-- Simple OVPN Download site -->
<head><meta charset="utf-8" /><title>OVPN Config Download</title><meta name="description" content="Server" /><meta content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" name="viewport" /><meta name="theme-color" content="#000000" /><link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.8.2/css/all.css"><link href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.3.1/css/bootstrap.min.css" rel="stylesheet"><link href="https://cdnjs.cloudflare.com/ajax/libs/mdbootstrap/4.8.3/css/mdb.min.css" rel="stylesheet"></head><body><div class="container justify-content-center" style="margin-top:9em;margin-bottom:5em;"><div class="col-md"><div class="view"><img src="https://openvpn.net/wp-content/uploads/openvpn.jpg" class="card-img-top"><div class="mask rgba-white-slight"></div></div><div class="card"><div class="card-body"><h5 class="card-title">Config List</h5><br /><ul class="list-group">
<li class="list-group-item justify-content-between align-items-center" style="margin-bottom:1em;"><p>TCP <span class="badge light-blue darken-4">Android/iOS/PC/Modem</span><br /><small></small></p><a class="btn btn-outline-success waves-effect btn-sm" href="https://IP-ADDRESSS:81/tcp.ovpn" style="float:right;"><i class="fa fa-download"></i> Download</a></li>
<li class="list-group-item justify-content-between align-items-center" style="margin-bottom:1em;"><p>UDP <span class="badge light-blue darken-4">Android/iOS/PC/Modem</span><br /><small></small></p><a class="btn btn-outline-success waves-effect btn-sm" href="https://IP-ADDRESSS:81/udp.ovpn" style="float:right;"><i class="fa fa-download"></i> Download</a></li>
<li class="list-group-item justify-content-between align-items-center" style="margin-bottom:1em;"><p>SSL <span class="badge light-blue darken-4">Android/iOS/PC/Modem</span><br /><small></small></p><a class="btn btn-outline-success waves-effect btn-sm" href="https://IP-ADDRESSS:81/ssl.ovpn" style="float:right;"><i class="fa fa-download"></i> Download</a></li>
<li class="list-group-item justify-content-between align-items-center" style="margin-bottom:1em;"><p> WS SSL <span class="badge light-blue darken-4">Android/iOS/PC/Modem</span><br /><small></small></p><a class="btn btn-outline-success waves-effect btn-sm" href="https://IP-ADDRESSS:81/ws-ssl.ovpn" style="float:right;"><i class="fa fa-download"></i> Download</a></li>
<li class="list-group-item justify-content-between align-items-center" style="margin-bottom:1em;"><p> ALL.zip <span class="badge light-blue darken-4">Android/iOS/PC/Modem</span><br /><small></small></p><a class="btn btn-outline-success waves-effect btn-sm" href="https://IP-ADDRESSS:81/Kyt-Project.zip" style="float:right;"><i class="fa fa-download"></i> Download</a></li>
</ul></div></div></div></div></body></html>
mySiteOvpn
    # Ganti placeholder IP dengan IP publik aktual
    sed -i "s|IP-ADDRESSS|$(curl -sS ifconfig.me)|g" /var/www/html/index.html
    echo "Sertifikat ditambahkan ke file .ovpn, arsip dibuat, dan halaman index.html diperbarui."
}

function install_ovpn() {
    echo "========== MENJALANKAN install_ovpn =========="
    ovpn_install
    config_easy
    make_follow
    # HAPUS baris berikut yang menyebabkan duplikasi:
    # make_follow
    cert_ovpn

    # HAPUS atau komentari baris-baris berikut yang tidak sesuai dan redundan:
    # systemctl enable openvpn # Tidak sesuai untuk instance spesifik
    # systemctl start openvpn   # Tidak sesuai untuk instance spesifik
    # /etc/init.d/openvpn restart # Diganti dengan systemctl

    # Restart layanan (seharusnya sudah dilakukan di config_easy, tapi tambahkan sebagai jaga-jaga)
    echo "Merestart layanan OpenVPN untuk memastikan..."
    systemctl restart openvpn-server@server-tcp || echo "Peringatan: Gagal merestart openvpn-server@server-tcp"
    systemctl restart openvpn-server@server-udp || echo "Peringatan: Gagal merestart openvpn-server@server-udp"
    echo "========== install_ovpn SELESAI =========="
}

# Jalankan fungsi utama
install_ovpn
