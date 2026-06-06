import asyncio
import datetime
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from aiohttp import web
import sys
from config import BOT_TOKEN, ADMIN_IDS, WEBHOOK_URL, WEBHOOK_PATH
from database import init_db, get_user
from utils.scheduler import start_scheduler
from utils.helpers import check_channel_subscription
from utils.logger import get_logger
import handlers.start
import handlers.subscription
import handlers.accounts
import handlers.templates
import handlers.campaigns
import handlers.account_actions
import handlers.admin

logger = get_logger(__name__)

# ---------- Middleware ----------
class SubscriptionMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        if message.text and message.text.startswith(('/start', '/admin', '/reset_campaign', '/extend', '/broadcast', '/promo', '/setchannel', '/unsetchannel')):
            return
        user_id = message.from_user.id
        if user_id in ADMIN_IDS:
            return
        user = await get_user(user_id)
        if not user:
            await message.answer("❌ Пользователь не найден. Напишите /start")
            raise CancelHandler()
        if user.is_banned:
            await message.answer("❌ Аккаунт заблокирован.")
            raise CancelHandler()
        if not user.subscription_end or user.subscription_end < datetime.datetime.utcnow():
            await message.answer("❌ Платная подписка истекла.")
            raise CancelHandler()
        if not await check_channel_subscription(user_id):
            await message.answer("❌ Подпишитесь на канал @quantixtg.")
            raise CancelHandler()

    async def on_process_callback_query(self, call: types.CallbackQuery, data: dict):
        if call.data.startswith('admin_'):
            return
        user_id = call.from_user.id
        if user_id in ADMIN_IDS:
            return
        user = await get_user(user_id)
        if not user:
            await call.answer("❌ Пользователь не найден", show_alert=True)
            raise CancelHandler()
        if user.is_banned:
            await call.answer("❌ Вы заблокированы", show_alert=True)
            raise CancelHandler()
        if not user.subscription_end or user.subscription_end < datetime.datetime.utcnow():
            await call.answer("❌ Подписка истекла", show_alert=True)
            raise CancelHandler()
        if not await check_channel_subscription(user_id):
            await call.answer("❌ Подпишитесь на канал", show_alert=True)
            raise CancelHandler()

# ---------- Вебхук (для Railway) ----------
async def on_startup(dp: Dispatcher):
    await init_db()
    if WEBHOOK_URL:
        await dp.bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook set to {WEBHOOK_URL}")
    else:
        logger.info("No webhook URL, using polling")

async def on_shutdown(dp: Dispatcher):
    if WEBHOOK_URL:
        await dp.bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()

# ---------- Главная функция ----------
async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    dp.middleware.setup(SubscriptionMiddleware())

    # Регистрация хендлеров
    handlers.start.register_handlers(dp)
    handlers.subscription.register_handlers(dp)
    handlers.accounts.register_handlers(dp)
    handlers.templates.register_handlers(dp)
    handlers.campaigns.register_handlers(dp)
    handlers.account_actions.register_handlers(dp)
    handlers.admin.register_handlers(dp)

    # Фоновые задачи
    asyncio.create_task(start_scheduler())

    if WEBHOOK_URL:
        # Запуск через webhook (Railway)
        app = web.Application()
        app.router.add_post(WEBHOOK_PATH, dp.webhook_handler())
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=int(sys.argv[1]) if len(sys.argv) > 1 else 8080)
        await site.start()
        await on_startup(dp)
        logger.info("Bot started with webhook")
        # Держим сервер
        await asyncio.Event().wait()
    else:
        # Локальный запуск через polling
        await init_db()
        await dp.start_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")