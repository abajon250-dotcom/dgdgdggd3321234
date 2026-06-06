import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")
XROCKET_API_URL = os.getenv("XROCKET_API_URL", "https://api.xrocket.com/v1")

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else [6484109563]

SESSIONS_DIR = "sessions"
TDATA_TEMP_DIR = "temp_tdata"
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

FLOOD_SLEEP_THRESHOLD = 60
AUTO_RECONNECT = True

CHECK_SUBSCRIPTION_INTERVAL = 300
CHECK_ACCOUNTS_INTERVAL = 60
MAX_CONCURRENT_CAMPAIGNS_PER_ACCOUNT = 1

POOL_SIZE = 10
POOL_RECYCLE = 3600

