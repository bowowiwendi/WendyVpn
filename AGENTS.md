# AGENTS.md — WendyVpn

## Repo structure

- `setup-main.sh` — **single installer entrypoint**. Run via `wget ... && chmod +x && ./setup-main.sh`
- `Features/menu/menu/` — canonical shell scripts (~122). **This is the source of truth** for menu items, backup, restore, bot helpers. All edits here must stay in sync with copies inside `bot/kyt.zip`
- `cfg_conf_js/` — templates for nginx, haproxy, xray, dropbear, rclone, tun configs
- `files/` — service files, updater, OpenVPN configs, UDP customizer
- `bot/` — Telegram bots (kyt.zip, cybervpn.zip, Botdo.zip, botkyt/)
- `ovpn/` — OpenVPN configuration files

## Branch & CI

- **Default branch is `ABSTRAK`**, not `main`
- CI workflows in `.github/workflows/` only trigger on `main` pushes. They are not used for `ABSTRAK`
- `deploy-vps.yml` runs `setup-main.sh` on ubuntu-24.04 with automated input `"2\n"`
- `test-install-ovpn.yml` tests `install_ovpn.sh` (note: this file does not exist yet in the repo root)

## Architecture & OS support

- Supported arch: `x86_64`, `aarch64`, `arm64`
- Supported OS: Ubuntu 20+, Debian 10+
- **No upper version bound** — must remain compatible with modern releases

## Key package quirks (setup-main.sh)

| Package | Fallback |
|---|---|
| `p7zip-full` | → `7zip` |
| `libcurl4-nss-dev` | → `libcurl4-openssl-dev` (NSS variant dropped in Ubuntu 24.04) |
| `apt-transport-https` | skip if APT ≥ 2.1 (built-in) |
| `bsd-mailx` | removed (deprecated) |
| `shc`, `easy-rsa`, `speedtest-cli`, `netcat-openbsd` | optional with fallbacks |

## After installation

- Menu entrypoint: `menu` (symlinked to `/usr/bin/`)
- Main control panel: `features`
- All menu items must `return` or call `menu`, not `exit` — otherwise user is dropped from the menu system
- Scripts are deployed to `/usr/bin/` on the VPS

## Telegram bots

| Bot | Location | Tech | Service name |
|---|---|---|---|
| kyt | `bot/kyt.zip` → `/usr/bin/kyt/` | Python 3 + Telethon | `kyt.service`? (check) |
| cybervpn | `bot/cybervpn.zip` | Python + Telethon | `cybervpn.service` |
| Botdo | external GitHub (`bowowiwendi/backup`) | Python + python-telegram-bot | `Botdo.service` |
| botkyt | `bot/botkyt/` (extracted) | Python + python-telegram-bot | manual |

### kyt.zip constraints

- Built from `bot/kyt/kyt/` directory — always rebuild zip after editing any file inside it:
  ```bash
  rm -f bot/kyt.zip && cd bot/kyt && zip -r ../kyt.zip kyt/
  ```
- Shell scripts in `kyt/shell/bot/` **must match** `Features/menu/menu/` — they are the same scripts deployed to both locations
- `requirements.txt`: use `telethon>=1.28.0`, **do not add** `keyboard` (headless-incompatible, needs `/dev/uinput`)
- Python entrypoint: `python3 -m kyt` from `WorkingDirectory=/usr/bin`
- Obfuscated `dist/` (PyArmor) is **never imported** — leave untouched

### bot.zip

- Contains the same shell helper scripts (backup, restore, cek-*)
- Rebuild after updating `Features/menu/menu/` scripts:
  ```bash
  rsync -a Features/menu/menu/{bot-backup,bot-cek-*,bot-member-ssh,bot-restore,bot-vps-info,notif_*} /tmp/bot_rebuild/bot/
  ```
  Then zip with `zip -r bot/bot.zip bot/`

## rclone / backup

- `cfg_conf_js/rclone.conf` contains an **expired** Google Drive token. Users must run `rclone config` themselves — the config template has instructions but no valid token
- Backup script: `Features/menu/menu/bot-backup` — uses absolute paths (`/root/backup/`), validates rclone remote exists before upload
- Restore script: `Features/menu/menu/restore` — supports Google Drive links (`FILE_ID` extraction), validates `unzip -t`, restarts services after restore

## Visual style

- Menu separator lines: `**◇━━━━━━━━━━◇**` (10 ━ characters, double-width in Telegram)
- All decorative lines in bot responses should use this exact pattern
- Shell menus use simple cyan/white box-drawing without emoji

## Development commands

```bash
# Rebuild kyt.zip
cd bot/kyt && rm -f ../kyt.zip && zip -r ../kyt.zip kyt/

# Rebuild bot.zip
mkdir -p /tmp/bot && cp Features/menu/menu/{bot-backup,bot-cek-login-ssh,bot-cek-ss,bot-cek-tr,bot-cek-vless,bot-cek-ws.sh,bot-member-ssh,bot-vps-info,restore,notif_backup,notif_delet} /tmp/bot/ && cd /tmp && zip -r /root/WendyVpn/bot/bot.zip bot/

# Commit & push (ABSTRAK branch)
git add -A && git commit -m "descriptive message"
git push origin ABSTRAK
```

## Out-of-scope / leave untouched

- PyArmor obfuscated code in `bot/kyt/kyt/{dist,modules/dist}/` — not imported at runtime, no need to touch
- Compiled binary `bot/kyt.sh` — no source available
- External scripts (`bot/install.sh` downloads from `bowowiwendi/backup`, `fix_cert`, `fix.sh`)
