from aiogram import types, Bot

GIF_URLS = {
    "welcome": "https://tenor.com/jLm9RXm7iIB.gif",
    "campaign_started": "https://i.pinimg.com/originals/8d/86/8e/8d868e038d96c7b8b3f233b2ffe59790.gif",
    "campaign_finished": "https://i.gifer.com/BDcd.gif",
    "subscription_expired": "https://media.giphy.com/media/xT9IgzoKnwFNmISR8I/giphy.gif",
    "channel_required": "https://media.giphy.com/media/3o7abB06u9bNzA8LC8/giphy.gif",
    "error": "https://media.giphy.com/media/l0HlNQ3JqjR8U0VRS/giphy.gif"
}

async def send_gif(target, gif_key: str, caption: str = None):
    """Отправляет гифку, target = message или callback"""
    url = GIF_URLS.get(gif_key)
    if not url:
        return
    if hasattr(target, 'message'):
        target = target.message
    try:
        if caption:
            await target.answer_animation(url, caption=caption)
        else:
            await target.answer_animation(url)
    except Exception as e:
        print(f"Ошибка отправки гифки: {e}")

async def send_gif_by_chat_id(bot: Bot, chat_id: int, gif_key: str, caption: str = None):
    """Отправляет гифку по chat_id (для использования в фоновых задачах)"""
    url = GIF_URLS.get(gif_key)
    if not url:
        return
    try:
        if caption:
            await bot.send_animation(chat_id, url, caption=caption)
        else:
            await bot.send_animation(chat_id, url)
    except Exception as e:
        print(f"Ошибка отправки гифки: {e}")