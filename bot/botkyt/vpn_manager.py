"""VPN Manager - Interface to shell scripts on remote servers via SSH"""
import paramiko
import asyncio
import secrets
import string
from datetime import datetime, timedelta


def generate_username(prefix: str = "wvpn") -> str:
    """Generate random username"""
    chars = string.ascii_lowercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(5))
    return f"{prefix}{suffix}"


def generate_uuid() -> str:
    """Generate UUID for xray protocols"""
    import uuid
    return str(uuid.uuid4())


def calculate_expiry(days: int) -> str:
    """Calculate expiry date from today"""
    expiry = datetime.now() + timedelta(days=days)
    return expiry.strftime("%Y-%m-%d")


class VPNManager:
    """Manages VPN account creation/deletion on remote servers via SSH"""
    
    def __init__(self, host: str, port: int = 22, username: str = "root", password: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
    
    def _get_ssh_client(self) -> paramiko.SSHClient:
        """Create SSH client connection"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=30
        )
        return client
    
    def _exec_command(self, command: str) -> tuple:
        """Execute command on remote server"""
        client = self._get_ssh_client()
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=60)
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            return output, error
        finally:
            client.close()
    
    async def exec_async(self, command: str) -> tuple:
        """Execute command asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._exec_command, command)
    
    # ==================== SSH ACCOUNT ====================
    
    async def create_ssh(self, username: str, password: str, days: int, ip_limit: int = 2) -> dict:
        """Create SSH account"""
        expiry = calculate_expiry(days)
        
        command = f"""
        useradd -e {expiry} -s /bin/false -M {username} 2>/dev/null
        echo '{username}:{password}' | chpasswd
        echo '{username} {expiry} {ip_limit}' >> /etc/ssh/.ssh.db
        echo '{ip_limit}' > /etc/kyt/files/ssh/ip/{username}
        echo "SSH account created: {username}"
        """
        
        output, error = await self.exec_async(command)
        
        return {
            "success": "created" in output.lower() or error == "",
            "username": username,
            "password": password,
            "expired": expiry,
            "ip_limit": ip_limit,
            "output": output
        }
    
    async def delete_ssh(self, username: str) -> dict:
        """Delete SSH account"""
        command = f"""
        userdel {username} 2>/dev/null
        sed -i '/^{username} /d' /etc/ssh/.ssh.db
        rm -f /etc/kyt/files/ssh/ip/{username}
        echo "SSH account deleted: {username}"
        """
        output, error = await self.exec_async(command)
        return {"success": True, "output": output}
    
    # ==================== VMESS ACCOUNT ====================
    
    async def create_vmess(self, username: str, uuid: str, days: int, ip_limit: int = 2) -> dict:
        """Create VMess account"""
        expiry = calculate_expiry(days)
        
        command = f"""
        echo '#{username} {expiry} {ip_limit}' >> /etc/xray/.lock.db
        sed -i '/#vmess$/a\\,{{"id": "{uuid}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        echo '{username} {uuid} {expiry}' >> /etc/vmess/.vmess.db
        echo '{ip_limit}' > /etc/kyt/files/vmess/ip/{username}
        systemctl restart xray
        echo "VMess account created: {username}"
        """
        
        output, error = await self.exec_async(command)
        
        return {
            "success": "created" in output.lower(),
            "username": username,
            "uuid": uuid,
            "expired": expiry,
            "ip_limit": ip_limit,
            "output": output
        }
    
    async def delete_vmess(self, username: str) -> dict:
        """Delete VMess account"""
        command = f"""
        sed -i '/^{username} /d' /etc/vmess/.vmess.db
        sed -i '/#! {username}/,+1d' /etc/xray/config.json
        sed -i '/#{username}/d' /etc/xray/.lock.db
        rm -f /etc/kyt/files/vmess/ip/{username}
        systemctl restart xray
        echo "VMess account deleted: {username}"
        """
        output, error = await self.exec_async(command)
        return {"success": True, "output": output}
    
    # ==================== VLESS ACCOUNT ====================
    
    async def create_vless(self, username: str, uuid: str, days: int, ip_limit: int = 2) -> dict:
        """Create VLess account"""
        expiry = calculate_expiry(days)
        
        command = f"""
        echo '#{username} {expiry} {ip_limit}' >> /etc/xray/.lock.db
        sed -i '/#vless$/a\\,{{"id": "{uuid}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        echo '{username} {uuid} {expiry}' >> /etc/vless/.vless.db
        echo '{ip_limit}' > /etc/kyt/files/vless/ip/{username}
        systemctl restart xray
        echo "VLess account created: {username}"
        """
        
        output, error = await self.exec_async(command)
        
        return {
            "success": "created" in output.lower(),
            "username": username,
            "uuid": uuid,
            "expired": expiry,
            "ip_limit": ip_limit,
            "output": output
        }
    
    async def delete_vless(self, username: str) -> dict:
        """Delete VLess account"""
        command = f"""
        sed -i '/^{username} /d' /etc/vless/.vless.db
        sed -i '/#! {username}/,+1d' /etc/xray/config.json
        sed -i '/#{username}/d' /etc/xray/.lock.db
        rm -f /etc/kyt/files/vless/ip/{username}
        systemctl restart xray
        echo "VLess account deleted: {username}"
        """
        output, error = await self.exec_async(command)
        return {"success": True, "output": output}
    
    # ==================== TROJAN ACCOUNT ====================
    
    async def create_trojan(self, username: str, uuid: str, days: int, ip_limit: int = 2) -> dict:
        """Create Trojan account"""
        expiry = calculate_expiry(days)
        
        command = f"""
        echo '#{username} {expiry} {ip_limit}' >> /etc/xray/.lock.db
        sed -i '/#trojanws$/a\\,{{"password": "{uuid}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        sed -i '/#trojangrpc$/a\\,{{"password": "{uuid}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        echo '{username} {uuid} {expiry}' >> /etc/trojan/.trojan.db
        echo '{ip_limit}' > /etc/kyt/files/trojan/ip/{username}
        systemctl restart xray
        echo "Trojan account created: {username}"
        """
        
        output, error = await self.exec_async(command)
        
        return {
            "success": "created" in output.lower(),
            "username": username,
            "uuid": uuid,
            "expired": expiry,
            "ip_limit": ip_limit,
            "output": output
        }
    
    async def delete_trojan(self, username: str) -> dict:
        """Delete Trojan account"""
        command = f"""
        sed -i '/^{username} /d' /etc/trojan/.trojan.db
        sed -i '/#! {username}/,+1d' /etc/xray/config.json
        sed -i '/#{username}/d' /etc/xray/.lock.db
        rm -f /etc/kyt/files/trojan/ip/{username}
        systemctl restart xray
        echo "Trojan account deleted: {username}"
        """
        output, error = await self.exec_async(command)
        return {"success": True, "output": output}
    
    # ==================== SHADOWSOCKS ACCOUNT ====================
    
    async def create_shadowsocks(self, username: str, password: str, days: int, ip_limit: int = 2) -> dict:
        """Create Shadowsocks account"""
        expiry = calculate_expiry(days)
        
        command = f"""
        echo '#{username} {expiry} {ip_limit}' >> /etc/xray/.lock.db
        sed -i '/#ssws$/a\\,{{"method": "aes-128-gcm","password": "{password}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        sed -i '/#ssgrpc$/a\\,{{"method": "aes-128-gcm","password": "{password}"\\n#! {username} {expiry}"}}' /etc/xray/config.json
        echo '{username} {password} {expiry}' >> /etc/shadowsocks/.shadowsocks.db
        systemctl restart xray
        echo "Shadowsocks account created: {username}"
        """
        
        output, error = await self.exec_async(command)
        
        return {
            "success": "created" in output.lower(),
            "username": username,
            "password": password,
            "expired": expiry,
            "ip_limit": ip_limit,
            "output": output
        }
    
    async def delete_shadowsocks(self, username: str) -> dict:
        """Delete Shadowsocks account"""
        command = f"""
        sed -i '/^{username} /d' /etc/shadowsocks/.shadowsocks.db
        sed -i '/#! {username}/,+1d' /etc/xray/config.json
        sed -i '/#{username}/d' /etc/xray/.lock.db
        systemctl restart xray
        echo "Shadowsocks account deleted: {username}"
        """
        output, error = await self.exec_async(command)
        return {"success": True, "output": output}
    
    # ==================== UTILITY ====================
    
    async def get_server_info(self) -> dict:
        """Get server information"""
        command = """
        echo "DOMAIN=$(cat /etc/xray/domain 2>/dev/null)"
        echo "IP=$(curl -s ipv4.icanhazip.com)"
        echo "UPTIME=$(uptime -p)"
        echo "RAM_TOTAL=$(free -m | awk 'NR==2{print $2}')"
        echo "RAM_USED=$(free -m | awk 'NR==2{print $3}')"
        echo "DISK_TOTAL=$(df -h / | awk 'NR==2{print $2}')"
        echo "DISK_USED=$(df -h / | awk 'NR==2{print $3}')"
        echo "SSH_USERS=$(cat /etc/ssh/.ssh.db 2>/dev/null | grep -c '^')"
        echo "VMESS_USERS=$(cat /etc/vmess/.vmess.db 2>/dev/null | grep -c '^')"
        echo "VLESS_USERS=$(cat /etc/vless/.vless.db 2>/dev/null | grep -c '^')"
        echo "TROJAN_USERS=$(cat /etc/trojan/.trojan.db 2>/dev/null | grep -c '^')"
        echo "SS_USERS=$(cat /etc/shadowsocks/.shadowsocks.db 2>/dev/null | grep -c '^')"
        """
        
        output, error = await self.exec_async(command)
        
        info = {}
        for line in output.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key.strip()] = value.strip()
        
        return info
    
    async def check_connection(self) -> bool:
        """Check if server is reachable"""
        try:
            output, error = await self.exec_async("echo 'OK'")
            return "OK" in output
        except Exception:
            return False
