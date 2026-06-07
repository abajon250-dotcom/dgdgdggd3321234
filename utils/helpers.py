from aiogram import Bot
from config import BOT_TOKEN, REQUIRED_CHANNEL

bot = Bot(token=BOT_TOKEN)

async def check_channel_subscription(user_id: int) -> bool:
    if not REQUIRED_CHANNEL:
        return True
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False