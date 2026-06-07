import os
from dotenv import load_dotenv

load_dotenv()

# ---------- Telegram Bot ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ---------- Платёжные системы ----------
CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")  # для CryptoBot
# Xrocket (опционально)
XROCKET_API_KEY = os.getenv("XROCKET_API_KEY")
XROCKET_API_URL = os.getenv("XROCKET_API_URL", "https://api.xrocket.com/v1")

# ---------- База данных ----------
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
# Если DATABASE_URL не задана, используем SQLite (только для локального теста)
if not DATABASE_URL:
    DATABASE_URL = "sqlite+aiosqlite:///bot_database.db"

# ---------- Администраторы ----------
# ТВОЙ ID: 6484109563
ADMIN_IDS = [6484109563]   # ← вот здесь должен быть твой ID

# Если хочешь добавить других админов, укажи через запятую: [6484109563, 123456789, 987654321]

# ---------- Telegram API (для Telethon) ----------
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")

# ---------- Пути к папкам ----------
SESSIONS_DIR = "sessions"
TDATA_TEMP_DIR = "temp_tdata"

# ---------- Настройки Telethon ----------
FLOOD_SLEEP_THRESHOLD = 60
AUTO_RECONNECT = True

# ---------- Интервалы проверок (в секундах) ----------
CHECK_SUBSCRIPTION_INTERVAL = 300   # 5 минут
CHECK_ACCOUNTS_INTERVAL = 60        # 1 минута
MAX_CONCURRENT_CAMPAIGNS_PER_ACCOUNT = 1

# ---------- Webhook (для Railway) ----------
WEBHOOK_HOST = os.getenv("RAILWAY_PUBLIC_DOMAIN", "")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}" if BOT_TOKEN else ""
WEBHOOK_URL = f"https://{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

# ---------- Проверка подписки на канал (опционально) ----------
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL", "")  # например "@quantixtg"