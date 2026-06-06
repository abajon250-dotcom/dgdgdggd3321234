import asyncio
import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_user
from utils.scheduler import start_scheduler
from utils.helpers import check_channel_subscription
from utils.logger import get_logger
from utils.gif_sender import send_gif  # добавим позже
import handlers.start
import handlers.subscription
import handlers.accounts
import handlers.templates
import handlers.campaigns
import handlers.account_actions
import handlers.admin

logger = get_logger(__name__)

class SubscriptionMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        # Команды, которые не требуют проверки
        if message.text and message.text.startswith(('/start', '/admin', '/reset_campaign', '/extend', '/broadcast', '/promo', '/setchannel', '/unsetchannel')):
            return
        user_id = message.from_user.id
        if user_id in ADMIN_IDS:
            return
        user = await get_user(user_id)
        if not user:
            await send_gif(message, "error")  # гифка при ошибке
            await message.answer("❌ Пользователь не найден. Напишите /start")
            raise CancelHandler()
        if user.is_banned:
            await send_gif(message, "ban")
            await message.answer("❌ Ваш аккаунт заблокирован.")
            raise CancelHandler()
        # Проверка платной подписки
        if not user.subscription_end or user.subscription_end < datetime.datetime.utcnow():
            await send_gif(message, "subscription_expired")
            await message.answer("❌ Платная подписка истекла. Продлите её в разделе «Подписка».")
            raise CancelHandler()
        # Проверка подписки на канал
        if not await check_channel_subscription(user_id):
            await send_gif(message, "channel_required")
            await message.answer(f"❌ Вы не подписаны на канал @quantixtg. Подпишитесь, чтобы пользоваться ботом.")
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
            await call.answer("❌ Вы не подписаны на канал @quantixtg", show_alert=True)
            raise CancelHandler()

async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    dp.middleware.setup(SubscriptionMiddleware())
    handlers.start.register_handlers(dp)
    handlers.subscription.register_handlers(dp)
    handlers.accounts.register_handlers(dp)
    handlers.templates.register_handlers(dp)
    handlers.campaigns.register_handlers(dp)
    handlers.account_actions.register_handlers(dp)
    handlers.admin.register_handlers(dp)
    asyncio.create_task(start_scheduler())
    logger.info("Бот запущен")
    try:
        await dp.start_polling()
    finally:
        await bot.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    asyncio.run(main())