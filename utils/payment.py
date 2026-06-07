import requests
from config import CRYPTOBOT_TOKEN
import logging

logger = logging.getLogger(__name__)

async def create_cryptobot_invoice(amount: float, description: str):
    url = "https://pay.crypt.bot/api/createInvoice"
    headers = {"Crypto-Pay-API-Token": CRYPTOBOT_TOKEN}
    data = {"asset": "USDT", "amount": str(amount), "description": description}
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            return {"id": result["result"]["invoice_id"], "link": result["result"]["pay_url"]}
    except Exception as e:
        logger.error(f"CryptoBot error: {e}")
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
            return data["result"]["items"][0]["status"]
    except:
        pass
    return None