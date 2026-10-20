# Biner Bawaan — Identitas, Sumber, dan Cara Build

Dokumen ini mencatat asal-usul dan cara membangun ulang biner bawaan
di direktori ini: `ws`, `ftvpn`, `udp-mini`, dan pasangan SlowDNS
`slowdns`/`slowdns-client`. Installer memilih biner
berdasarkan arsitektur mesin (`BINARCH` di `setup-main.sh` dan
`files/update.sh`):

- Mesin `x86_64` → `files/ws`, `files/ftvpn`, `files/udp-mini`,
  `files/slowdns`, `files/slowdns-client`
- Mesin `aarch64`/`arm64` → `files/arm64/ws`, `files/arm64/ftvpn`,
  `files/arm64/udp-mini`, `files/arm64/slowdns`,
  `files/arm64/slowdns-client`

## ftvpn — HAProxy

- **Identitas biner lama:** HAProxy 1.8.31-1~bpo10+1 (build Debian
  buster-backports), terikat OpenSSL 1.1 (`libssl.so.1.1`) dan Lua 5.3.
  Tidak bisa berjalan di Ubuntu 22.04+/Debian 12+ (OpenSSL 3). Diunduh
  `ins_epro` ke `/usr/sbin/ftvpn`; tidak ada script di repo yang pernah
  menjalankannya — ia disiapkan sebagai HAProxy cadangan/standalone.
- **Pengganti (sejak 2026-10-20):** HAProxy **2.8.31** dibangun dari
  source resmi haproxy.org melawan **OpenSSL 3.0.16**, Lua 5.3.6,
  PCRE2 10.45, zlib 1.3.1, libxcrypt 4.4.38 (semua statis).
  - x86-64: biner **statis penuh (musl)** — tidak tergantung libc/OpenSSL
    sistem sama sekali, jalan di semua OS yang didukung installer.
  - arm64: dinamis glibc dengan syarat simbol maksimal **GLIBC_2.25**
    (dibangun memakai sysroot Debian 10/glibc 2.28) — jalan di
    Debian 10+/Ubuntu 20.04+.
  - Verifikasi: `cfg_conf_js/haproxy.cfg` dan `haproxy3.cfg` valid di
    2.8.31; uji proxy HTTP dan terminasi TLS lolos (native x86-64 dan
    arm64 via qemu-aarch64 + sysroot buster).

## udp-mini — BadVPN udpgw

- **Identitas biner lama:** BadVPN udpgw **1.999.128** (open source,
  github.com/ambrop72/badvpn). Hanya butuh libc/librt, jadi biner
  x86-64 lama tetap dipakai apa adanya.
- **arm64:** dibangun dari source resmi BadVPN **1.999.130** (tag
  terdekat yang tersedia; source 1.999.128 tidak diterbitkan). CLI
  udpgw tidak berubah — `--help` identik selain nomor versi. Syarat
  simbol maksimal GLIBC_2.17; terverifikasi jalan (qemu-aarch64).
  Dijalankan service sebagai
  `udp-mini --listen-addr 127.0.0.1:7100 --max-clients 500` dst.

## ws — ws-epro (WebSocket proxy ePro)

- **Identitas biner lama:** `ws-epro v1.2.1`, Go 1.16.3, statis,
  **closed source** (tidak ada source publik dari pembuatnya). Biner
  x86-64 lama tetap dipakai apa adanya. Audit `strings` atas biner lama
  tidak menemukan URL/telemetri apa pun.
- **arm64:** **implementasi ulang bersih (clean-room)** dalam Go,
  source di `src/ws-epro/` (hanya stdlib). Perilaku disamakan dengan
  biner asli lewat pengujian black-box:
  - Flag tunggal `-f <config>` (default `config.yml`); format config
    YAML subset yang sama (`verbose`, `listen[].target_host/target_port/
    listen_port`) — kompatibel dengan `cfg_conf_js/tun.conf`.
  - Banner `ws-epro (v1.2.1)` + baris `list porting [...]` sama.
  - Setiap request HTTP dijawab literal
    `HTTP/1.1 101 Switching Protocols\r\n\r\n` (tanpa header tambahan)
    **sebelum** koneksi ke target dibuka, lalu relay TCP dua arah polos.
  - Format log stdout sama persis (warna ANSI, format
    `#NNN :port: client/opened/closed (X bytes send, Y bytes received)`,
    log per-chunk + hex dump pada `verbose: 2`, pesan error
    `check remote tcp fail: ...` saat target mati, dan
    `config file not exists` (exit 1) saat config tidak ada).
  - Terverifikasi berdampingan dengan biner asli (kasus relay normal,
    target mati, config hilang) pada x86-64, dan via qemu untuk arm64.

## Catatan build

- Toolchain x86-64: `musl-gcc`, target statis penuh.
- Toolchain arm64: `aarch64-linux-gnu-gcc` (glibc) dengan sysroot
  Debian 10 (glibc 2.28) agar biner hasil tidak menuntut glibc yang
  lebih baru dari OS target tertua (Debian 10/Ubuntu 20.04).
- Semua biner hasil build sudah di-strip.

## slowdns & slowdns-client — dnstt (SlowDNS)

- **Identitas:** "SlowDNS" di panel ini adalah **dnstt** (DNS tunnel)
  karya David Fifield (bamsoftware) — protokol yang sama dengan pakem
  SlowDNS yang beredar (khaledagn, fisabiliyusri/SLDNS).
  `files/slowdns` adalah **dnstt-server**; `files/slowdns-client`
  adalah **dnstt-client**.
- **Kenapa dibangun dari source:** repo `khaledagn/SlowDNS` sudah tidak
  ada di GitHub (404 saat dicek 2026-10-21), dan repo
  `fisabiliyusri/SLDNS` hanya membagikan biner jadi plus **sepasang
  kunci server yang sama untuk semua pemasang** (`server.key`/
  `server.pub` publik di repo) — tidak aman dipakai. Karena itu biner
  dibangun dari source resmi dnstt, dan installer **membuat keypair
  baru di setiap VPS** (kunci privat tidak pernah masuk repo).
- **Versi & build:** dnstt **v1.20260501.0** (commit `0c5c52a`) dari
  `https://www.bamsoftware.com/git/dnstt.git`, diaudit singkat (tanpa
  `os/exec`/telemetri; `net/http` hanya untuk mode DoH/DoT client),
  dibangun statis penuh (`CGO_ENABLED=0`, `-trimpath -ldflags '-s -w'`)
  untuk amd64 dan arm64 dengan Go 1.27.3:
  ```bash
  git clone https://www.bamsoftware.com/git/dnstt.git
  cd dnstt
  CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags '-s -w' -o files/slowdns ./dnstt-server/
  CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags '-s -w' -o files/slowdns-client ./dnstt-client/
  CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags '-s -w' -o files/arm64/slowdns ./dnstt-server/
  CGO_ENABLED=0 GOOS=linux GOARCH=arm64 go build -trimpath -ldflags '-s -w' -o files/arm64/slowdns-client ./dnstt-client/
  ```
- **Pemakaian (`ssh_slow()` di `setup-main.sh`):** biner dipasang
  sebagai `/etc/slowdns/sldns-server` dan `/etc/slowdns/sldns-client`;
  unit `server-sldns.service` (UDP 5300, backend SSH `127.0.0.1:22`)
  dan `client-sldns.service` (dengar lokal `127.0.0.1:2222`); publik
  masuk lewat iptables REDIRECT UDP 53 → 5300. Domain NS disimpan di
  `/root/nsdomain` (dibaca semua menu pembuat akun), public key di
  `/etc/slowdns/server.pub`.
- **Verifikasi:** uji tunnel lokal di VM build terhalang sandbox
  (UDP `sendto: operation not permitted`); pembuktian ujung-ke-ujung
  dilakukan di VPS uji (loopback via client-sldns + leg publik dari
  server lain) — lihat catatan rilis commit SlowDNS.
