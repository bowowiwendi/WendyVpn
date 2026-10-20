# Biner Bawaan — Identitas, Sumber, dan Cara Build

Dokumen ini mencatat asal-usul dan cara membangun ulang tiga biner bawaan
di direktori ini: `ws`, `ftvpn`, dan `udp-mini`. Installer memilih biner
berdasarkan arsitektur mesin (`BINARCH` di `setup-main.sh` dan
`files/update.sh`):

- Mesin `x86_64` → `files/ws`, `files/ftvpn`, `files/udp-mini`
- Mesin `aarch64`/`arm64` → `files/arm64/ws`, `files/arm64/ftvpn`,
  `files/arm64/udp-mini`

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
