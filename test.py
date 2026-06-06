import asyncio
from aiogram import Bot

bot = Bot(token='8779070491:AAGOte7zdnjHwFMD42FFJLOEFadrxq7249A')

async def check():
    member = await bot.get_chat_member('@quantixtg', 6484109563)
    print(member.status)

asyncio.run(check())