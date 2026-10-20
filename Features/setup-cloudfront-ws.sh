#!/bin/bash
# ============================================================================
# setup-cloudfront-ws.sh -- CloudFront WebSocket support for installed VPN
# Repo   : bowowiwendi/WendyVpn (branch ABSTRAK)
# Adds 4 CloudFront WebSocket paths WITHOUT touching existing VPN functions.
#   /cf-vmess  -> Xray VMess  (WS) port 10020
#   /cf-vless  -> Xray VLess  (WS) port 10021
#   /cf-trojan -> Xray Trojan (WS) port 10022
#   /cf-ssh    -> SSH over WebSocket (wstunnel -> 127.0.0.1:22) port 10023
# Usage (on VPS with VPN already installed):
#   bash <(curl -sL https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/Features/setup-cloudfront-ws.sh)
# Idempotent: safe to run multiple times.
# Reference: vps-utama 103.197.190.101 + CloudFront E125K60UJIWKO4
# ============================================================================
set -u
ok()   { echo "[OK] $1"; }
warn() { echo "[WARN] $1"; }
err()  { echo "[ERR] $1"; }
if [ "${EUID}" -ne 0 ]; then err "need root"; exit 1; fi
XRAY_JSON="/etc/xray/config.json"
NGINX_XRAY="/etc/nginx/conf.d/xray.conf"
CREDS_FILE="/root/.cf-creds"
WSTUN_BIN="/usr/local/bin/wstunnel"
WSTUN_VER="11.0.0"
TS=$(date +%Y%m%d%H%M%S)
[ -f "$XRAY_JSON" ] || { err "no xray config"; exit 1; }
[ -f "$NGINX_XRAY" ] || { err "no nginx config"; exit 1; }
echo "=== 1/5: wstunnel ==="
WSTUN_OK=0
if [ -x "$WSTUN_BIN" ]; then WSTUN_OK=1; ok "wstunnel exists"; fi
if [ "$WSTUN_OK" = "0" ]; then
  ARCH=$(uname -m)
  case "$ARCH" in x86_64) WA="amd64";; aarch64|arm64) WA="arm64";; *) WA="";; esac
  if [ -n "$WA" ]; then
    GH="github.com"; ER="erebe"; WN="wstunnel"
    URL="https://${GH}/${ER}/${WN}/releases/download/v${WSTUN_VER}/${WN}_${WSTUN_VER}_linux_${WA}.tar.gz"
    echo "download $URL"
    if wget --timeout=30 --tries=2 -q -O /tmp/wstunnel.tgz "$URL" && tar -xzf /tmp/wstunnel.tgz -C /tmp/ && [ -f /tmp/wstunnel ]; then
      install -m 0755 /tmp/wstunnel "$WSTUN_BIN" && rm -f /tmp/wstunnel.tgz /tmp/wstunnel
      WSTUN_OK=1; ok "wstunnel installed"
    else
      warn "download failed; install wstunnel manually then re-run"
    fi
  fi
fi
if [ "$WSTUN_OK" = "1" ]; then
printf '%s\n' \
'[Unit]' \
'Description=wstunnel SSH over WebSocket (CloudFront)' \
'After=network.target sshd.service' \
'Wants=sshd.service' \
'' \
'[Service]' \
'Type=simple' \
'ExecStart=/usr/local/bin/wstunnel server --restrict-to 127.0.0.1:22 --restrict-http-upgrade-path-prefix /cf-ssh ws://127.0.0.1:10023' \
'Restart=always' \
'RestartSec=5' \
'User=root' \
'' \
'[Install]' \
'WantedBy=multi-user.target' \
> /etc/systemd/system/wstunnel-ssh.service
systemctl daemon-reload
systemctl enable --now wstunnel-ssh.service >/dev/null 2>&1
sleep 1
systemctl is-active --quiet wstunnel-ssh.service && ok "wstunnel-ssh running" || err "wstunnel-ssh failed"
fi
echo "=== 2/5: Xray inbounds (10020/10021/10022) ==="
export UUID_VMESS=$(cat /proc/sys/kernel/random/uuid)
export UUID_VLESS=$(cat /proc/sys/kernel/random/uuid)
export UUID_TROJAN=$(cat /proc/sys/kernel/random/uuid)
cp -f "$XRAY_JSON" "${XRAY_JSON}.bak-cfws-${TS}"
XRAY_RES=$(python3 - "$XRAY_JSON" <<'PYEOF'
import re, sys, os, json
path = sys.argv[1]
U = {'10020': ('vmess','/cf-vmess',os.environ['UUID_VMESS']),
     '10021': ('vless','/cf-vless',os.environ['UUID_VLESS']),
     '10022': ('trojan','/cf-trojan',os.environ['UUID_TROJAN'])}
src = open(path).read()
have = set(re.findall(r'"port"\s*:\s*"?(10020|10021|10022)"?', src))
todo = [p for p in ('10020','10021','10022') if p not in have]
if not todo:
    print("SKIP"); sys.exit(0)
def mk(port, proto, wsp, cred):
    if proto == 'vmess':
        cli = '{"id": "%s", "alterId": 0}' % cred; xtra = ''
    elif proto == 'vless':
        cli = '{"id": "%s"}' % cred; xtra = '"decryption":"none",'
    else:
        cli = '{"password": "%s"}' % cred; xtra = '"decryption":"none","udp": true,'
    return ('{"listen":"127.0.0.1","port":"%s","protocol":"%s",'
            '"settings":{%s"clients":[%s]},'
            '"streamSettings":{"network":"ws","wsSettings":{"path":"%s"}}}'
            % (port, proto, xtra, cli, wsp))
blocks = [mk(p, *U[p]) for p in todo]
m = re.search(r'"inbounds"\s*:', src)
if not m: print("NOINBOUNDS"); sys.exit(2)
s = src.index('[', m.end())
dep, ins, esc, end = 0, False, False, None
i, n = s, len(src)
while i < n:
    if not ins and src[i] == '#' and (i == 0 or src[i-1] == '\n'):
        j = src.find('\n', i); i = n if j == -1 else j+1; continue
    c = src[i]
    if ins:
        if esc: esc = False
        elif c == '\\': esc = True
        elif c == '"': ins = False
    else:
        if c == '"': ins = True
        elif c == '[': dep += 1
        elif c == ']':
            dep -= 1
            if dep == 0: end = i; break
    i += 1
if end is None: print("NOARRAYEND"); sys.exit(3)
bef = src[:end].rstrip()
sep = '' if bef[-1:] in ('[', ',') else ','
new = bef + sep + '\n' + ',\n'.join(blocks) + '\n' + src[end:]
chk = re.sub(r'(?m)^\s*#.*$', '', new)
try:
    d = json.loads(chk)
    assert {'10020','10021','10022'} <= {str(x.get('port')) for x in d['inbounds']}
except Exception as e:
    print("INVALID:"+str(e)); sys.exit(4)
open(path, 'w').write(new)
print("PATCHED:" + ','.join(todo))
PYEOF
)
XRAY_ADDED=0
case "$XRAY_RES" in
  SKIP) ok "xray inbounds exist, skipped"; rm -f "${XRAY_JSON}.bak-cfws-${TS}" ;;
  PATCHED:*) ok "xray inbounds added: ${XRAY_RES#PATCHED:}"; XRAY_ADDED=1 ;;
  *) err "xray patch failed ($XRAY_RES); rollback"; cp -f "${XRAY_JSON}.bak-cfws-${TS}" "$XRAY_JSON" ;;
esac
echo "=== 3/5: nginx locations ==="
if grep -q "cf-vmess" "$NGINX_XRAY"; then
  ok "nginx cf locations exist, skipped"
else
  cp -f "$NGINX_XRAY" "${NGINX_XRAY}.bak-cfws-${TS}"
  python3 - "$NGINX_XRAY" > /tmp/ngx.out 2>&1 <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p).read()
t = '''    location ~ /cf-vless {
    if ($http_upgrade != "Websocket") {
    rewrite /(.*) /cf-vless break;
    }
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_pass http://127.0.0.1:10021;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_x_forwarded_for;
    proxy_set_header X-Forwarded-For $http_x_forwarded_for;
  }
    location ~ /cf-vmess {
    if ($http_upgrade != "Websocket") {
    rewrite /(.*) /cf-vmess break;
    }
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_pass http://127.0.0.1:10020;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_x_forwarded_for;
    proxy_set_header X-Forwarded-For $http_x_forwarded_for;
  }
    location ~ /cf-trojan {
    if ($http_upgrade != "Websocket") {
    rewrite /(.*) /cf-trojan break;
    }
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_pass http://127.0.0.1:10022;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_x_forwarded_for;
    proxy_set_header X-Forwarded-For $http_x_forwarded_for;
  }
    location ~ /cf-ssh {
    if ($http_upgrade != "Websocket") {
    rewrite /(.*) /cf-ssh break;
    }
    proxy_http_version 1.1;
    proxy_redirect off;
    proxy_pass http://127.0.0.1:10023;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $http_x_forwarded_for;
    proxy_set_header X-Forwarded-For $http_x_forwarded_for;
  }
'''
a = "    location ~ / {"
i = s.find(a)
if i == -1: print("NOANCHOR"); sys.exit(2)
open(p, 'w').write(s[:i] + t + s[i:])
print("PATCHED")
PYEOF
  if grep -q PATCHED /tmp/ngx.out && nginx -t 2>/dev/null; then
    ok "nginx cf locations added"
  else
    err "nginx patch failed; rollback"; cat /tmp/ngx.out
    cp -f "${NGINX_XRAY}.bak-cfws-${TS}" "$NGINX_XRAY"
  fi
fi
echo "=== 4/5: restart & verify ==="
systemctl restart xray 2>/dev/null
systemctl restart nginx 2>/dev/null
[ "$WSTUN_OK" = "1" ] && systemctl restart wstunnel-ssh.service 2>/dev/null
sleep 2
FAIL=0
for p in cf-vmess cf-vless cf-trojan; do
  C=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "http://127.0.0.1/${p}")
  if [ "$C" = "400" ]; then ok "/${p} -> 400"; else err "/${p} -> ${C} (want 400)"; FAIL=1; fi
done
if [ "$WSTUN_OK" = "1" ]; then
  ss -tln 2>/dev/null | grep -q "127.0.0.1:10023" && ok "wstunnel on 10023" || { err "wstunnel not on 10023"; FAIL=1; }
fi
echo "=== 5/5: credentials ==="
if [ "$XRAY_ADDED" = "1" ] && [ ! -f "$CREDS_FILE" ]; then
  { echo "# cf-ws creds $(date '+%F %T') - root only"
    echo "CF_VMESS_UUID=$UUID_VMESS"
    echo "CF_VLESS_UUID=$UUID_VLESS"
    echo "CF_TROJAN_PASSWORD=$UUID_TROJAN"; } > "$CREDS_FILE"
  chmod 600 "$CREDS_FILE"; ok "creds -> $CREDS_FILE"
elif [ ! -f "$CREDS_FILE" ]; then warn "$CREDS_FILE missing but inbounds pre-exist; check UUIDs in $XRAY_JSON manually"; else warn "$CREDS_FILE exists, kept"; fi
echo "==================================="
[ "$FAIL" = "0" ] && ok "CloudFront WS support ACTIVE" || warn "done with warnings"
echo "CF setup: origin <IP>.nip.io (HTTP only); behaviors /cf-vmess* /cf-vless* /cf-trojan* /cf-ssh*"
