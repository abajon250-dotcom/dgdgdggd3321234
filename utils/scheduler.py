import asyncio
import datetime
from aiogram import Bot
from config import BOT_TOKEN, CHECK_SUBSCRIPTION_INTERVAL, CHECK_ACCOUNTS_INTERVAL, API_ID, API_HASH
from database import get_all_accounts, update_account_active_status, get_user
from utils.telethon_client import get_client_by_account, check_account_valid
from utils.logger import get_logger

logger = get_logger(__name__)
bot = Bot(token=BOT_TOKEN)

async def check_subscriptions_task():
    while True:
        await asyncio.sleep(CHECK_SUBSCRIPTION_INTERVAL)
        try:
            # Проверим всех пользователей с истекающей подпиской (опционально)
            pass
        except Exception as e:
            logger.error(f"Subscription check error: {e}")

async def check_accounts_validity_task():
    while True:
        await asyncio.sleep(CHECK_ACCOUNTS_INTERVAL)
        try:
            accounts = await get_all_accounts()
            for acc in accounts:
                if not acc.is_active:
                    continue
                try:
                    client = await get_client_by_account(acc)
                    valid = await check_account_valid(client)
                    if not valid:
                        await update_account_active_status(acc.id, False)
                        user = await get_user(acc.user_id)
                        if user:
                            await bot.send_message(user.tg_user_id,
                                f"⚠️ Сессия для аккаунта {acc.phone} слетела. Требуется переподключение.")
                        logger.warning(f"Account {acc.phone} became invalid")
                except Exception as e:
                    logger.error(f"Check account {acc.id} error: {e}")
        except Exception as e:
            logger.error(f"Accounts validity check error: {e}")

async def start_scheduler():
    asyncio.create_task(check_subscriptions_task())
    asyncio.create_task(check_accounts_validity_task())