#!/usr/bin/env python3
import json
import os
import re
import shlex
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

_NGINX_CONF_PATHS = [
    "/etc/nginx/sites-enabled/xray.conf",
    "/etc/nginx/conf.d/xray.conf",
    "/etc/nginx/nginx.conf",
]
for _cfg in _NGINX_CONF_PATHS:
    if os.path.isfile(_cfg):
        try:
            with open(_cfg) as _f:
                _orig = _f.read()
            _fixed = re.sub(
                r'^\s*server_name\s+.*\bapi\..*\bpanel\..*;\s*\n?',
                '',
                _orig,
                flags=re.MULTILINE | re.IGNORECASE,
            )
            if _fixed != _orig:
                with open(_cfg, "w") as _f:
                    _f.write(_fixed)
                code = subprocess.run(
                    ["nginx", "-t"],
                    capture_output=True,
                    timeout=5,
                ).returncode
                if code == 0 and subprocess.run(
                    ["systemctl", "is-active", "--quiet", "nginx"]
                ).returncode == 0:
                    subprocess.run(
                        ["systemctl", "reload", "nginx"],
                        capture_output=True,
                        timeout=10,
                    )
        except Exception:
            pass

HOST = "0.0.0.0"
PORT = 9000
TOKEN_FILE = "/etc/wendy-api/token"
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


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def run_shell(command, timeout=120, env_extra=None):
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    return subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, env=env)


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
    env = {"NO_NOTIF": "1"} if body.get("no_notif") else {}

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
    return account_response(run_shell(command, env_extra=env), service, username)


def handle_account_renew(body):
    service = body.get("service", "")
    username = body.get("username", "")
    err, status = validate_service_username(service, username)
    if err:
        return err, status
    days = str(body.get("days", "1"))
    quota = str(body.get("quota", "100"))
    limit_ip = str(body.get("limit_ip", "2"))
    env = {"NO_NOTIF": "1"} if body.get("no_notif") else {}
    script = RENEW_SCRIPTS[service]
    if service in ("vmess", "vless", "trojan"):
        values = [username, days, quota, limit_ip]
    else:
        values = [username, days]
    return account_response(run_shell(shell_quote_lines(values, script), env_extra=env), service, username)


def handle_account_delete(body):
    service = body.get("service", "")
    username = body.get("username", "")
    err, status = validate_service_username(service, username)
    if err:
        return err, status
    env = {"NO_NOTIF": "1"} if body.get("no_notif") else {}
    script = DELETE_SCRIPTS[service]
    return account_response(run_shell(shell_quote_lines([username], script), env_extra=env), service, username)


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
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "system":
            if not self._require_token():
                return
            length = int(self.headers.get("Content-Length", "0") or "0")
            try:
                body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            except Exception:
                self._send_json({"ok": False, "error": "invalid_json"}, status=400)
                return
            if parts[2] == "bot-config":
                bot_token = (body.get("bot_token") or "").strip()
                chat_id = (body.get("chat_id") or "").strip()
                if not bot_token or not chat_id:
                    self._send_json({"ok": False, "error": "bot_token and chat_id required"}, status=400)
                    return
                os.makedirs("/etc/bot", exist_ok=True)
                with open("/etc/bot/.bot.db", "w") as f:
                    f.write(f"#bot# {bot_token} {chat_id}\n")
                self._send_json({"ok": True, "stdout": "Bot config updated"})
                return
            self._send_json({"ok": False, "error": "not_found"}, status=404)
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
