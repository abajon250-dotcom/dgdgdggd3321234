from aiogram import Bot
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
REQUIRED_CHANNEL = "@quantixtg"   # замените на свой канал

async def check_channel_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        # Если бот не админ канала, вернуть False, чтобы требовать подписку
        print(f"Ошибка проверки канала: {e}")
        return False