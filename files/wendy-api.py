#!/usr/bin/env python3
import html
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "127.0.0.1"
PORT = 9000
TOKEN_FILE = "/etc/wendy-api/token"
PANEL_TOKEN_FILE = "/etc/wendy-api/panel_token"
DOMAIN_FILE = "/etc/xray/domain"
ACCOUNT_FILES = {
    "ssh": "/etc/ssh/.ssh.db",
    "vmess": "/etc/vmess/.vmess.db",
    "vless": "/etc/vless/.vless.db",
    "trojan": "/etc/trojan/.trojan.db",
    "shadowsocks": "/etc/shadowsocks/.shadowsocks.db",
}
SERVICE_NAMES = [
    "nginx",
    "haproxy",
    "xray",
    "ssh",
    "dropbear",
    "vnstat",
    "cron",
    "fail2ban",
    "netfilter-persistent",
    "openvpn-server@server-tcp",
    "openvpn-server@server-udp",
    "ws",
]
ALLOWED_ACTIONS = {"start", "stop", "restart", "enable", "disable"}
ALLOWED_COMMAND_RE = re.compile(
    r"^(?:"
    r"printf\s+.*?\|\s*(?:addssh|addws|addvless|addtr|addss|trial|trialws|trialvless|trialtr|trialss|renewssh|renewws|renewvless|renewtr|renewss|delssh|delws|delvless|deltr|delss)"
    r"|xp|clean_lock\.sh|bot-backup|bot-cek-[a-z-]+|notif_(?:backup|delet|limit)"
    r")$"
)
VALID_SERVICE = {"ssh", "vmess", "vless", "trojan", "shadowsocks"}
VALID_USERNAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
CREATE_SCRIPTS = {
    "ssh": "addssh",
    "vmess": "addws",
    "vless": "addvless",
    "trojan": "addtr",
    "shadowsocks": "addss",
}
TRIAL_SCRIPTS = {
    "ssh": "trial",
    "vmess": "trialws",
    "vless": "trialvless",
    "trojan": "trialtr",
    "shadowsocks": "trialss",
}
RENEW_SCRIPTS = {
    "ssh": "renewssh",
    "vmess": "renewws",
    "vless": "renewvless",
    "trojan": "renewtr",
    "shadowsocks": "renewss",
}
DELETE_SCRIPTS = {
    "ssh": "delssh",
    "vmess": "delws",
    "vless": "delvless",
    "trojan": "deltr",
    "shadowsocks": "delss",
}
ACCOUNT_FILE_PREFIX = {
    "ssh": "ssh",
    "vmess": "vmess",
    "vless": "vless",
    "trojan": "trojan",
    "shadowsocks": "shadowsocks",
}


def read_text(path, default=""):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except Exception:
        return default


def load_token():
    return read_text(TOKEN_FILE)


def load_panel_token():
    return read_text(PANEL_TOKEN_FILE)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def run_shell(command, timeout=120):
    return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)


def api_error(message, status=400):
    return {"ok": False, "error": message}, status


def validate_service_username(service, username):
    if service not in VALID_SERVICE:
        return api_error("invalid_service")
    if not VALID_USERNAME_RE.match(username or ""):
        return api_error("invalid_username")
    return None, None


def shell_quote_lines(values, script):
    quoted = " ".join(shlex.quote(str(value)) for value in values)
    return f"printf '%s\\n' {quoted} | {script}"


def account_output(service, username):
    prefix = ACCOUNT_FILE_PREFIX.get(service, service)
    path = f"/var/www/html/{prefix}-{username}.txt"
    return read_text(path, "")


def account_response(result, service=None, username=None):
    payload = {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    if service and username:
        payload["account_text"] = account_output(service, username)
    return payload, 200 if result.returncode == 0 else 500


def is_panel_authenticated(headers):
    token = load_panel_token()
    if not token:
        return True
    cookie = headers.get("Cookie", "")
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith("wendy_panel=") and part.split("=", 1)[1] == token:
            return True
    return False


def handle_account_create(body):
    service = body.get("service", "")
    username = body.get("username", "")
    err, status = validate_service_username(service, username)
    if err:
        return err, status
    password = str(body.get("password", ""))
    limit_ip = str(body.get("limit_ip", "2"))
    quota = str(body.get("quota", "100"))
    days = str(body.get("days", "1"))
    bug = str(body.get("bug", ""))
    trial = bool(body.get("trial", False))

    if trial:
        script = TRIAL_SCRIPTS[service]
        if service == "ssh":
            command = shell_quote_lines([username, password, limit_ip, days], script)
        else:
            command = shell_quote_lines([days], script)
    else:
        script = CREATE_SCRIPTS[service]
        if service == "ssh":
            values = [username, password, limit_ip, days, bug]
        elif service in ("vmess", "vless", "trojan"):
            values = [username, limit_ip, quota, days, bug]
        else:
            values = [username, limit_ip, days, quota, bug]
        command = shell_quote_lines(values, script)
    return account_response(run_shell(command), service, username)


def handle_account_renew(body):
    service = body.get("service", "")
    username = body.get("username", "")
    err, status = validate_service_username(service, username)
    if err:
        return err, status
    days = str(body.get("days", "1"))
    quota = str(body.get("quota", "100"))
    limit_ip = str(body.get("limit_ip", "2"))
    script = RENEW_SCRIPTS[service]
    if service in ("vmess", "vless", "trojan"):
        values = [username, days, quota, limit_ip]
    else:
        values = [username, days]
    return account_response(run_shell(shell_quote_lines(values, script)), service, username)


def handle_account_delete(body):
    service = body.get("service", "")
    username = body.get("username", "")
    err, status = validate_service_username(service, username)
    if err:
        return err, status
    script = DELETE_SCRIPTS[service]
    return account_response(run_shell(shell_quote_lines([username], script)), service, username)


def handle_restart_service(body):
    service = str(body.get("service", "")).strip()
    if not service:
        return api_error("missing_service")
    result = run(["systemctl", "restart", service])
    return ({"ok": result.returncode == 0, "service": service, "stdout": result.stdout, "stderr": result.stderr}, 200 if result.returncode == 0 else 500)


def handle_enable_service(body):
    service = str(body.get("service", "")).strip()
    if not service:
        return api_error("missing_service")
    result = run(["systemctl", "enable", "--now", service])
    return ({"ok": result.returncode == 0, "service": service, "stdout": result.stdout, "stderr": result.stderr}, 200 if result.returncode == 0 else 500)


def handle_command_xp():
    result = run_shell("xp", timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_command_clean_lock():
    result = run_shell("clean_lock.sh", timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_command_backup():
    result = run_shell("bot-backup", timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_notif_state(name):
    result = run_shell(name, timeout=60)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_reboot():
    result = run_shell("reboot", timeout=30)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_speedtest():
    result = run_shell("speedtest-cli --share", timeout=300)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_fixcert():
    result = run_shell("fixcert", timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_addhost(body):
    domain = str(body.get("domain", "")).strip()
    if not domain:
        return api_error("missing_domain")
    result = run_shell(f"printf '%s\n' {shlex.quote(domain)} | addhost", timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_restore(body):
    link = str(body.get("link", "")).strip()
    if not link:
        return api_error("missing_link")
    result = run_shell(f"printf '%s\n' {shlex.quote(link)} | bot-restore", timeout=300)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_toggle_auto_delete(body):
    state = str(body.get("state", "")).strip()
    if state not in {"on", "off"}:
        return api_error("invalid_state")
    script = "printf '%s\n' '3' | auto-delet.sh" if state == "on" else "printf '%s\n' '1' | auto-delet.sh"
    result = run_shell(script, timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_toggle_auto_backup(body):
    state = str(body.get("state", "")).strip()
    if state not in {"on", "off"}:
        return api_error("invalid_state")
    script = "printf '%s\n' '8' | auto-backup.sh" if state == "on" else "printf '%s\n' '3' | auto-backup.sh"
    result = run_shell(script, timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def handle_toggle_limit(body):
    state = str(body.get("state", "")).strip()
    if state not in {"on", "off"}:
        return api_error("invalid_state")
    script = "printf '%s\n' '1' | onoff" if state == "on" else "printf '%s\n' '2' | onoff"
    result = run_shell(script, timeout=180)
    return ({"ok": result.returncode == 0, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}, 200 if result.returncode == 0 else 500)


def is_enabled(name):
    result = run(["systemctl", "is-enabled", name])
    if result.returncode == 0:
        return "enabled"
    if result.stdout.strip():
        return result.stdout.strip()
    return "disabled"


def service_state(name):
    result = run(["systemctl", "is-active", name])
    active = result.stdout.strip() if result.stdout.strip() else ("active" if result.returncode == 0 else "inactive")
    return {"name": name, "active": active, "enabled": is_enabled(name)}


def cpu_usage_percent():
    def sample():
        with open("/proc/stat", "r", encoding="utf-8") as handle:
            parts = handle.readline().split()[1:8]
        values = list(map(int, parts))
        idle = values[3] + values[4]
        total = sum(values)
        return idle, total

    idle1, total1 = sample()
    time.sleep(0.15)
    idle2, total2 = sample()
    total_delta = total2 - total1
    idle_delta = idle2 - idle1
    if total_delta <= 0:
        return 0.0
    return round((1 - (idle_delta / float(total_delta))) * 100, 2)


def memory_stats():
    meminfo = {}
    with open("/proc/meminfo", "r", encoding="utf-8") as handle:
        for line in handle:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            meminfo[key] = int(value.strip().split()[0])
    total = meminfo.get("MemTotal", 0) * 1024
    available = meminfo.get("MemAvailable", 0) * 1024
    used = max(total - available, 0)
    percent = round((used / total) * 100, 2) if total else 0.0
    return {"total": total, "available": available, "used": used, "percent": percent}


def disk_stats():
    usage = shutil.disk_usage("/")
    percent = round((usage.used / usage.total) * 100, 2) if usage.total else 0.0
    return {"total": usage.total, "used": usage.used, "free": usage.free, "percent": percent}


def uptime_seconds():
    try:
        with open("/proc/uptime", "r", encoding="utf-8") as handle:
            return float(handle.read().split()[0])
    except Exception:
        return 0.0


def load_average():
    try:
        one, five, fifteen = os.getloadavg()
        return {"1m": round(one, 2), "5m": round(five, 2), "15m": round(fifteen, 2)}
    except Exception:
        return {"1m": 0.0, "5m": 0.0, "15m": 0.0}


def network_traffic():
    rx = 0
    tx = 0
    try:
        with open("/proc/net/dev", "r", encoding="utf-8") as handle:
            for line in handle:
                if ":" not in line:
                    continue
                iface, data = line.split(":", 1)
                iface = iface.strip()
                if iface == "lo":
                    continue
                values = data.split()
                if len(values) >= 16:
                    rx += int(values[0])
                    tx += int(values[8])
    except Exception:
        pass
    return {"rx_bytes": rx, "tx_bytes": tx}


def account_counts():
    result = {}
    for name, path in ACCOUNT_FILES.items():
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as handle:
                result[name] = sum(1 for line in handle if line.startswith("###"))
        except Exception:
            result[name] = 0
    return result


def system_stats():
    return {
        "domain": read_text(DOMAIN_FILE, "-"),
        "hostname": os.uname().nodename,
        "uptime_seconds": int(uptime_seconds()),
        "load_average": load_average(),
        "cpu_percent": cpu_usage_percent(),
        "memory": memory_stats(),
        "disk": disk_stats(),
        "network": network_traffic(),
        "services": [service_state(name) for name in SERVICE_NAMES],
        "accounts": account_counts(),
    }


def human_bytes(value):
    value = float(value)
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if value < 1024.0:
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} PB"


def human_uptime(seconds):
    seconds = int(seconds)
    days, rem = divmod(seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or parts:
        parts.append(f"{hours}h")
    if minutes or parts:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


def panel_html(stats):
    services_rows = []
    for svc in stats["services"]:
        services_rows.append(
            f"<tr><td>{html.escape(svc['name'])}</td><td>{html.escape(svc['active'])}</td><td>{html.escape(svc['enabled'])}</td></tr>"
        )

    account_cards = []
    for name, count in stats["accounts"].items():
        account_cards.append(f'<div class="mini"><span>{html.escape(name.upper())}</span><strong>{count}</strong></div>')

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WendyVPN Dashboard</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b1020;
      --card: #121a33;
      --muted: #93a4c3;
      --text: #e8eefc;
      --accent: #5eead4;
      --line: #243055;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Inter, system-ui, sans-serif; background: radial-gradient(circle at top, #182447 0%, var(--bg) 45%); color: var(--text); }}
    .wrap {{ max-width: 1180px; margin: 0 auto; padding: 24px; }}
    .hero {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 16px; align-items: center; margin-bottom: 20px; }}
    .hero h1 {{ margin: 0; font-size: 28px; }}
    .hero p {{ margin: 6px 0 0; color: var(--muted); }}
    .pill {{ border: 1px solid var(--line); background: rgba(255,255,255,.04); padding: 10px 14px; border-radius: 999px; color: var(--accent); font-weight: 600; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; margin-bottom: 18px; }}
    .card {{ background: rgba(18,26,51,.92); border: 1px solid var(--line); border-radius: 18px; padding: 18px; box-shadow: 0 12px 40px rgba(0,0,0,.18); }}
    .card .label {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .card .value {{ font-size: 28px; margin-top: 8px; font-weight: 700; }}
    .card .sub {{ margin-top: 6px; color: var(--muted); font-size: 13px; }}
    .two {{ display: grid; grid-template-columns: 1.4fr .9fr; gap: 14px; }}
    .section-title {{ margin: 0 0 12px; font-size: 18px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid var(--line); font-size: 14px; }}
    th {{ color: var(--muted); font-weight: 600; }}
    .mini-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; }}
    .mini {{ background: rgba(255,255,255,.03); border: 1px solid var(--line); border-radius: 14px; padding: 12px; }}
    .mini span {{ display: block; color: var(--muted); font-size: 11px; margin-bottom: 8px; }}
    .mini strong {{ font-size: 22px; }}
    .footer {{ margin-top: 16px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 900px) {{ .two {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>WendyVPN Dashboard</h1>
        <p>Read-only monitor and API entry point for the VPS.</p>
      </div>
      <div class="pill" id="uptime">Uptime: {human_uptime(stats['uptime_seconds'])}</div>
    </div>

    <div class="grid">
      <div class="card"><div class="label">CPU</div><div class="value" id="cpu">{stats['cpu_percent']}%</div><div class="sub">Usage realtime</div></div>
      <div class="card"><div class="label">RAM</div><div class="value" id="ram">{stats['memory']['percent']}%</div><div class="sub" id="ram-sub">{human_bytes(stats['memory']['used'])} / {human_bytes(stats['memory']['total'])}</div></div>
      <div class="card"><div class="label">Disk</div><div class="value" id="disk">{stats['disk']['percent']}%</div><div class="sub" id="disk-sub">{human_bytes(stats['disk']['used'])} / {human_bytes(stats['disk']['total'])}</div></div>
      <div class="card"><div class="label">Load</div><div class="value" id="load">{stats['load_average']['1m']}</div><div class="sub" id="load-sub">5m {stats['load_average']['5m']} | 15m {stats['load_average']['15m']}</div></div>
    </div>

    <div class="two">
      <div class="card">
        <h2 class="section-title">Services</h2>
        <table>
          <thead><tr><th>Service</th><th>Status</th><th>Enabled</th></tr></thead>
          <tbody id="services">{''.join(services_rows)}</tbody>
        </table>
      </div>
      <div class="card">
        <h2 class="section-title">Accounts</h2>
        <div class="mini-grid" id="accounts">{''.join(account_cards)}</div>
        <div class="footer">API endpoint: <code>/api/stats</code></div>
      </div>
    </div>
  </div>
  <script>
    async function refresh() {{
      const res = await fetch('/api/stats', {{cache: 'no-store'}});
      const data = await res.json();
      document.getElementById('cpu').textContent = data.cpu_percent.toFixed(2) + '%';
      document.getElementById('ram').textContent = data.memory.percent.toFixed(2) + '%';
      document.getElementById('ram-sub').textContent = formatBytes(data.memory.used) + ' / ' + formatBytes(data.memory.total);
      document.getElementById('disk').textContent = data.disk.percent.toFixed(2) + '%';
      document.getElementById('disk-sub').textContent = formatBytes(data.disk.used) + ' / ' + formatBytes(data.disk.total);
      document.getElementById('load').textContent = data.load_average['1m'].toFixed(2);
      document.getElementById('load-sub').textContent = '5m ' + data.load_average['5m'].toFixed(2) + ' | 15m ' + data.load_average['15m'].toFixed(2);
      document.getElementById('uptime').textContent = 'Uptime: ' + formatUptime(data.uptime_seconds);
      document.getElementById('services').innerHTML = data.services.map(svc => `<tr><td>${{svc.name}}</td><td>${{svc.active}}</td><td>${{svc.enabled}}</td></tr>`).join('');
      document.getElementById('accounts').innerHTML = Object.entries(data.accounts).map(([name, count]) => `<div class="mini"><span>${{name.toUpperCase()}}</span><strong>${{count}}</strong></div>`).join('');
    }}
    function formatBytes(value) {{
      const units = ['B', 'KB', 'MB', 'GB', 'TB'];
      let size = value;
      let index = 0;
      while (size >= 1024 && index < units.length - 1) {{ size /= 1024; index += 1; }}
      return size.toFixed(1) + ' ' + units[index];
    }}
    function formatUptime(seconds) {{
      seconds = Math.floor(seconds);
      const days = Math.floor(seconds / 86400);
      seconds %= 86400;
      const hours = Math.floor(seconds / 3600);
      seconds %= 3600;
      const minutes = Math.floor(seconds / 60);
      const parts = [];
      if (days) parts.push(days + 'd');
      if (hours || parts.length) parts.push(hours + 'h');
      if (minutes || parts.length) parts.push(minutes + 'm');
      parts.push(seconds + 's');
      return parts.join(' ');
    }}
    refresh();
    setInterval(refresh, 10000);
  </script>
</body>
</html>"""


def login_html(error_message=""):
    error_box = f'<div class="error">{html.escape(error_message)}</div>' if error_message else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WendyVPN Panel Login</title>
  <style>
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; font-family:system-ui,sans-serif; background:radial-gradient(circle at top, #182447 0%, #0b1020 50%); color:#e8eefc; }}
    .card {{ width:min(420px, 92vw); background:rgba(18,26,51,.95); border:1px solid #243055; border-radius:20px; padding:28px; box-shadow:0 12px 40px rgba(0,0,0,.22); }}
    h1 {{ margin:0 0 8px; font-size:26px; }}
    p {{ margin:0 0 18px; color:#93a4c3; }}
    input {{ width:100%; padding:14px 16px; border-radius:12px; border:1px solid #243055; background:#0b1020; color:#e8eefc; margin-bottom:12px; }}
    button {{ width:100%; padding:14px 16px; border:0; border-radius:12px; background:#5eead4; color:#08111f; font-weight:700; cursor:pointer; }}
    .error {{ margin-bottom:12px; color:#fca5a5; font-size:14px; }}
    .hint {{ margin-top:12px; font-size:13px; color:#93a4c3; }}
  </style>
</head>
<body>
  <form class="card" method="post" action="/panel-login">
    <h1>WendyVPN Panel</h1>
    <p>Masukkan panel token untuk membuka dashboard.</p>
    {error_box}
    <input type="password" name="token" placeholder="Panel token" autocomplete="current-password" required>
    <button type="submit">Login</button>
    <div class="hint">Token dibuat otomatis saat installer berjalan.</div>
  </form>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "WendyAPI/1.0"

    def _send_json(self, payload, status=200):
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text, status=200, content_type="text/html; charset=utf-8"):
        data = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _token_ok(self):
        token = load_token()
        if not token:
            return True
        header_token = self.headers.get("X-API-Token", "")
        auth = self.headers.get("Authorization", "")
        if header_token == token:
            return True
        if auth.startswith("Bearer ") and auth.split(" ", 1)[1] == token:
            return True
        return False

    def _require_token(self):
        if self._token_ok():
            return True
        self._send_json({"ok": False, "error": "unauthorized"}, status=401)
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") if parsed.path not in ("/",) else parsed.path
        if path in ("/", "/panel"):
            if not is_panel_authenticated(self.headers):
                self._send_text(login_html(), content_type="text/html; charset=utf-8")
                return
            self._send_text(panel_html(system_stats()))
            return
        if path == "/panel-login":
            self._send_text(login_html(), content_type="text/html; charset=utf-8")
            return
        if path == "/panel-logout":
            self.send_response(302)
            self.send_header("Set-Cookie", "wendy_panel=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            self.send_header("Location", "/panel-login")
            self.end_headers()
            return
        if path == "/api/health":
            self._send_json({"ok": True, "service": "wendy-api"})
            return
        if path == "/api/stats":
            self._send_json(system_stats())
            return
        if path == "/api/services":
            self._send_json({"services": [service_state(name) for name in SERVICE_NAMES]})
            return
        if path == "/api/token":
            if not self._require_token():
                return
            self._send_json({"token_present": bool(load_token())})
            return
        self._send_json({"ok": False, "error": "not_found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.path == "/panel-login":
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else ""
            form = parse_qs(raw)
            submitted = (form.get("token", [""])[0] or "").strip()
            panel_token = load_panel_token()
            if panel_token and submitted != panel_token:
                self._send_text(login_html("Token panel salah."), content_type="text/html; charset=utf-8")
                return
            self.send_response(302)
            self.send_header("Set-Cookie", f"wendy_panel={submitted or panel_token}; Path=/; HttpOnly; SameSite=Lax")
            self.send_header("Location", "/panel")
            self.end_headers()
            return
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "accounts":
            if not self._require_token():
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                self._send_json({"ok": False, "error": "invalid_json"}, status=400)
                return
            if parts[2] == "create":
                payload, status = handle_account_create(body)
            elif parts[2] == "renew":
                payload, status = handle_account_renew(body)
            elif parts[2] == "delete":
                payload, status = handle_account_delete(body)
            else:
                payload, status = {"ok": False, "error": "not_found"}, 404
            self._send_json(payload, status=status)
            return
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "maintenance":
            if not self._require_token():
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                self._send_json({"ok": False, "error": "invalid_json"}, status=400)
                return
            if parts[2] == "restart":
                payload, status = handle_restart_service(body)
            elif parts[2] == "enable":
                payload, status = handle_enable_service(body)
            elif parts[2] == "xp":
                payload, status = handle_command_xp()
            elif parts[2] == "clean-lock":
                payload, status = handle_command_clean_lock()
            elif parts[2] == "backup":
                payload, status = handle_command_backup()
            elif parts[2] == "notif-delet":
                payload, status = handle_notif_state("notif_delet")
            elif parts[2] == "notif-backup":
                payload, status = handle_notif_state("notif_backup")
            elif parts[2] == "notif-limit":
                payload, status = handle_notif_state("notif_limit")
            elif parts[2] == "reboot":
                payload, status = handle_reboot()
            elif parts[2] == "speedtest":
                payload, status = handle_speedtest()
            elif parts[2] == "fixcert":
                payload, status = handle_fixcert()
            elif parts[2] == "addhost":
                payload, status = handle_addhost(body)
            elif parts[2] == "restore":
                payload, status = handle_restore(body)
            elif parts[2] == "toggle-auto-delete":
                payload, status = handle_toggle_auto_delete(body)
            elif parts[2] == "toggle-auto-backup":
                payload, status = handle_toggle_auto_backup(body)
            elif parts[2] == "toggle-limit":
                payload, status = handle_toggle_limit(body)
            else:
                payload, status = {"ok": False, "error": "not_found"}, 404
            self._send_json(payload, status=status)
            return
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "command":
            if not self._require_token():
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                self._send_json({"ok": False, "error": "invalid_json"}, status=400)
                return
            command = (body.get("command") or "").strip()
            if not command or not ALLOWED_COMMAND_RE.match(command):
                self._send_json({"ok": False, "error": "command_not_allowed"}, status=400)
                return
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self._send_json(
                {
                    "ok": result.returncode == 0,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                status=200 if result.returncode == 0 else 500,
            )
            return
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "services":
            if not self._require_token():
                return
            service_name = parts[2]
            action = parts[3]
            if action not in ALLOWED_ACTIONS:
                self._send_json({"ok": False, "error": "unsupported_action"}, status=400)
                return
            result = run(["systemctl", action, service_name])
            if result.returncode == 0:
                self._send_json({"ok": True, "service": service_name, "action": action})
            else:
                self._send_json({"ok": False, "service": service_name, "action": action, "error": result.stderr.strip() or result.stdout.strip() or "systemctl_failed"}, status=500)
            return
        self._send_json({"ok": False, "error": "not_found"}, status=404)

    def log_message(self, fmt, *args):
        return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"WendyAPI listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
