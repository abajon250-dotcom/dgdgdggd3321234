import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH
from database import init_db
from utils.scheduler import start_scheduler
from utils.logger import get_logger
from handlers import (
    start, subscription, accounts, templates, campaigns, account_actions, admin
)

logger = get_logger(__name__)

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    # Регистрация хендлеров
    start.register_handlers(dp)
    subscription.register_handlers(dp)
    accounts.register_handlers(dp)
    templates.register_handlers(dp)
    campaigns.register_handlers(dp)
    account_actions.register_handlers(dp)
    admin.register_handlers(dp)

    # Удаляем старый вебхук
    await bot.delete_webhook()
    asyncio.create_task(start_scheduler())

    if WEBHOOK_URL:
        # Railway webhook
        await bot.set_webhook(WEBHOOK_URL)
        app = web.Application()
        app.router.add_post(WEBHOOK_PATH, dp.webhook_handler())
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv("PORT", 8080))
        site = web.TCPSite(runner, host="0.0.0.0", port=port)
        await site.start()
        logger.info(f"Webhook started on {WEBHOOK_URL}")
        await asyncio.Event().wait()
    else:
        logger.info("Polling mode")
        await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())