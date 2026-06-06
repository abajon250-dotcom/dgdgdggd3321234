import requests
from config import CRYPTOBOT_TOKEN, XROCKET_API_KEY, XROCKET_API_URL
from utils.logger import get_logger

logger = get_logger(__name__)

# ---------- CryptoBot (реальный API) ----------
async def create_cryptobot_invoice(amount: float, currency: str = "USD", description: str = "Subscription"):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    # CryptoBot поддерживает USDT, BTC, ETH, LTC, BNB, TRX, TON
    asset = "USDT"
    payload = {
        "asset": asset,
        "amount": str(amount),
        "description": description,
        "paid_btn_name": "callback",
        "paid_btn_url": "https://t.me/your_bot"  # замените на ссылку вашего бота
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            return {
                "id": data["result"]["invoice_id"],
                "link": data["result"]["pay_url"]
            }
        else:
            logger.error(f"CryptoBot error: {data}")
            return None
    except Exception as e:
        logger.error(f"CryptoBot create invoice failed: {e}")
        return None

async def check_cryptobot_payment(invoice_id: int):
    url = "https://pay.crypt.bot/api/getInvoices"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    params = {"invoice_ids": invoice_id}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok") and data["result"]["items"]:
            invoice = data["result"]["items"][0]
            return invoice["status"]  # active, paid, expired
        return None
    except Exception as e:
        logger.error(f"CryptoBot check payment failed: {e}")
        return None

# ---------- Xrocket (заглушка – добавьте свою реализацию) ----------
async def create_xrocket_invoice(amount: float, currency: str = "USD", user_id: int = None):
    # Здесь должна быть реальная интеграция с Xrocket по их документации
    logger.warning("Xrocket invoice creation is not implemented")
    return None

async def check_xrocket_payment(invoice_id: str):
    logger.warning("Xrocket payment check is not implemented")
    return None