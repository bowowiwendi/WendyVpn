import os

# Bot Configuration
BOT_TOKEN = ""
SUPER_ADMIN = ""
DOMAIN = ""
DNS = ""
PUB = ""

# Bayar.gg Configuration
BAYAR_API_KEY = ""
BAYAR_API_URL = "https://www.bayar.gg/api"
BAYAR_MAX_AMOUNT = 500000

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

# Server Configuration
SERVERS = {}  # Will be loaded from database

# Default Pricing (Rp)
DEFAULT_PRICE = 10000

# Load from var.txt if exists
VAR_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "var.txt")

def load_config():
    """Load configuration from var.txt"""
    global BOT_TOKEN, SUPER_ADMIN, DOMAIN, DNS, PUB, BAYAR_API_KEY
    
    if os.path.exists(VAR_FILE):
        with open(VAR_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if key == "BOT_TOKEN":
                        BOT_TOKEN = value
                    elif key == "ADMIN":
                        SUPER_ADMIN = value
                    elif key == "DOMAIN":
                        DOMAIN = value
                    elif key == "DNS":
                        DNS = value
                    elif key == "PUB":
                        PUB = value
                    elif key == "BAYAR_API_KEY":
                        BAYAR_API_KEY = value

load_config()
