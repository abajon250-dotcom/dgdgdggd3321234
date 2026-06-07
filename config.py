import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

SESSIONS_DIR = "sessions"
WEBHOOK_HOST = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}" if BOT_TOKEN else ""
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")
FLOOD_SLEEP_THRESHOLD = 60
AUTO_RECONNECT = True

# Добавляем недостающие константы
CHECK_SUBSCRIPTION_INTERVAL = int(os.getenv("CHECK_SUBSCRIPTION_INTERVAL", 300))
CHECK_ACCOUNTS_INTERVAL = int(os.getenv("CHECK_ACCOUNTS_INTERVAL", 60))
MAX_CONCURRENT_CAMPAIGNS_PER_ACCOUNT = int(os.getenv("MAX_CONCURRENT_CAMPAIGNS_PER_ACCOUNT", 1))