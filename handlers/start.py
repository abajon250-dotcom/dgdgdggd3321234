from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart
from database import get_user, create_user
from keyboards.inline import main_menu_keyboard
from utils.helpers import check_channel_subscription
from utils.gif_sender import send_gif
from config import ADMIN_IDS

async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    user = await get_user(user_id)
    if not user:
        user = await create_user(user_id)

    # Проверка подписки на канал (для не-админов)
    if user_id not in ADMIN_IDS:
        if not await check_channel_subscription(user_id):
            await send_gif(message, "channel_required", "❌ Вы не подписаны на канал @quantixtg")
            await message.answer(
                "👉 Подпишитесь, чтобы использовать бота:\n"
                "🔗 https://t.me/quantixtg\n\n"
                "После подписки нажмите /start снова."
            )
            return

    # Приветственная гифка
    await send_gif(message, "welcome", "Добро пожаловать в панель управления!")
    await message.answer(
        "Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

async def main_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu_keyboard())
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(cmd_start, CommandStart())
    dp.register_callback_query_handler(main_menu_callback, text="main_menu")