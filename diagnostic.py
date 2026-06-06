import asyncio
from aiogram import Bot

bot = Bot(token='8779070491:AAGOte7zdnjHwFMD42FFJLOEFadrxq7249A')  # твой токен


async def main():
    try:
        # Проверяем информацию о канале
        chat = await bot.get_chat('@quantixtg')
        print(f"Канал найден: {chat.title}")

        # Проверяем статус бота в канале
        me = await bot.get_me()
        bot_member = await bot.get_chat_member('@quantixtg', me.id)
        print(f"Статус бота в канале: {bot_member.status}")

        if bot_member.status not in ['administrator', 'creator']:
            print("❌ Бот не является администратором! Добавьте бота в канал как администратора.")
            return

        # Проверяем ваш статус
        your_member = await bot.get_chat_member('@quantixtg', 6484109563)
        print(f"Ваш статус: {your_member.status}")

        if your_member.status in ['member', 'administrator', 'creator']:
            print("✅ Вы подписаны на канал. Проверка пройдёт.")
        else:
            print("❌ Вы не подписаны на канал или бот не может определить статус.")

    except Exception as e:
        print(f"Ошибка: {e}")


asyncio.run(main())