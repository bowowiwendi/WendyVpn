# AGENTS.md — WendyVpn

## Repo structure

- `setup-main.sh` — **single installer entrypoint**. Run via `wget ... && chmod +x && ./setup-main.sh`
- `Features/menu.zip` — canonical shell scripts (~122, zipped). **This is the source of truth** for menu items, backup, restore, bot helpers. All edits here must stay in sync with copies inside `bot/kyt.zip`
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
| kyt | `bot/kyt.zip` → `/usr/bin/kyt/` | Python 3 + Telethon | kyt.service |

### Editing kyt.zip

- `bot/kyt.zip` is the **final artifact** — source tree was removed. To edit:
  ```bash
  mkdir -p /tmp/kyt_edit && cd /tmp/kyt_edit && unzip -o /root/WendyVpn/bot/kyt.zip && nano kyt/modules/file.py && rm -f /root/WendyVpn/bot/kyt.zip && zip -r /root/WendyVpn/bot/kyt.zip kyt/ && rm -rf /tmp/kyt_edit
  ```
- Shell scripts in `kyt/shell/bot/` must match `Features/menu.zip`
- `requirements.txt`: use `telethon>=1.28.0`, **do not add** `keyboard`
- Python entrypoint: `python3 -m kyt` from `WorkingDirectory=/usr/bin`
- Obfuscated `dist/` (PyArmor) is **never imported** — leave untouched

### bot.zip

- Contains the same shell helper scripts (backup, restore, cek-*)
- Rebuild after updating `Features/menu.zip` scripts:
  ```bash
  cd Features && unzip -o menu.zip 'menu/bot-*' 'menu/notif_*' 'menu/restore' -d /tmp/bot_rebuild/ && cd /tmp/bot_rebuild/menu && zip -r /root/WendyVpn/bot/bot.zip . && rm -rf /tmp/bot_rebuild
  ```

## rclone / backup

- `cfg_conf_js/rclone.conf` contains an **expired** Google Drive token. Users must run `rclone config` themselves — the config template has instructions but no valid token
- Backup script: `Features/menu.zip` → `bot-backup` — uses absolute paths (`/root/backup/`), validates rclone remote exists before upload
- Restore script: `Features/menu.zip` → `restore` — supports Google Drive links (`FILE_ID` extraction), validates `unzip -t`, restarts services after restore

## Visual style

- Menu separator lines: `**◇━━━━━━━━━━◇**` (10 ━ characters, double-width in Telegram)
- All decorative lines in bot responses should use this exact pattern
- Shell menus use simple cyan/white box-drawing without emoji

## Development commands

```bash
# Edit kyt.zip then rebuild
mkdir -p /tmp/kyt_edit && cd /tmp/kyt_edit && unzip -o /root/WendyVpn/bot/kyt.zip && nano kyt/modules/file.py && rm -f /root/WendyVpn/bot/kyt.zip && zip -r /root/WendyVpn/bot/kyt.zip kyt/ && rm -rf /tmp/kyt_edit
```

## Out-of-scope / leave untouched

- PyArmor obfuscated code in `bot/kyt/kyt/{dist,modules/dist}/` — not imported at runtime, no need to touch
- Compiled binary `bot/kyt.sh` — no source available
- External scripts (`bot/install.sh` downloads from `bowowiwendi/backup`, `fix_cert`, `fix.sh`)
