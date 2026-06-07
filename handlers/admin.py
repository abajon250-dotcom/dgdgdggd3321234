import asyncio
import datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_all_users, get_user_accounts, get_all_payments, get_user,
    update_subscription, get_all_campaigns, update_campaign_status,
    ban_user, unban_user, create_promo, get_promo, get_all_promos, use_promo,
    create_user
)
from keyboards.inline import admin_panel_keyboard, back_to_main_keyboard, admin_ban_keyboard
from config import ADMIN_IDS

# FSM
class GiveSubscriptionState(StatesGroup):
    waiting_user_id = State()
    waiting_days = State()

class CreatePromoState(StatesGroup):
    waiting_code = State()
    waiting_days = State()
    waiting_max_uses = State()
    waiting_expiry = State()

class BroadcastState(StatesGroup):
    waiting_message = State()

# ---------- Админ-панель ----------
async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ Нет доступа.")
        return
    await message.answer("👑 Админ-панель", reply_markup=admin_panel_keyboard())

# Основной обработчик callback'ов админки
async def admin_callback(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    action = callback.data.split("_")[1]

    if action == "users":
        users = await get_all_users()
        text = "📋 *Список пользователей:*\n\n"
        for u in users:
            accounts = await get_user_accounts(u.tg_user_id)
            sub = u.subscription_end.strftime('%d.%m.%Y %H:%M') if u.subscription_end else 'Нет'
            banned = "🔒" if u.is_banned else "✅"
            text += f"{banned} ID: `{u.tg_user_id}` | Подписка до: {sub} | Акков: {len(accounts)}\n"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())
    elif action == "payments":
        payments = await get_all_payments(50)
        text = "💰 *Последние платежи:*\n\n"
        for p in payments:
            text += f"🧾 ID: {p.id} | Юзер: {p.user_id} | {p.amount} {p.currency} | {p.payment_system} | {p.status}\n"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())
    elif action == "stats":
        users = await get_all_users()
        total_accounts = sum(len(await get_user_accounts(u.tg_user_id)) for u in users)
        text = f"📊 *Статистика:*\n👥 Пользователей: {len(users)}\n📱 Аккаунтов: {total_accounts}"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())
    elif action == "campaigns":
        campaigns = await get_all_campaigns(50)
        text = "📢 *Все рассылки:*\n\n"
        for c in campaigns:
            text += f"📨 ID: {c.id} | Юзер: {c.user_id} | Аккаунт: {c.account.phone} | Статус: {c.status}\n"
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_to_main_keyboard())
    elif action == "promos":
        await promo_codes_menu(callback)
    elif action == "ban_menu":
        await callback.message.edit_text("🔒 Управление блокировкой:", reply_markup=admin_ban_keyboard())
    elif action == "broadcast":
        await callback.message.answer("📢 Введите текст для массовой рассылки:")
        await BroadcastState.waiting_message.set()
    else:
        await callback.answer("Неизвестная команда", show_alert=True)
    await callback.answer()

# Отдельный обработчик для кнопки "Выдать подписку" (чтобы не попадал в admin_callback)
async def give_subscription_button(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.answer("✏️ Введите Telegram ID пользователя:")
    await GiveSubscriptionState.waiting_user_id.set()
    await callback.answer()

# Обработчики ввода для выдачи подписки
async def give_subscription_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(target_user_id=user_id)
        await message.answer("✏️ Введите количество дней:")
        await GiveSubscriptionState.waiting_days.set()
    except:
        await message.answer("❌ Неверный ID. Введите число.")
        await state.finish()

async def give_subscription_days(message: types.Message, state: FSMContext):
    try:
        days = int(message.text)
        data = await state.get_data()
        target_user_id = data['target_user_id']
        user = await get_user(target_user_id)
        if not user:
            await message.answer(f"❌ Пользователь {target_user_id} не найден.")
            await state.finish()
            return
        new_end = datetime.datetime.utcnow() + datetime.timedelta(days=days)
        await update_subscription(target_user_id, new_end)
        await message.answer(f"✅ Подписка выдана на {days} дней. Действует до {new_end.strftime('%d.%m.%Y')}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        await state.finish()

# Блокировка
async def ban_user_start(callback: types.CallbackQuery):
    await callback.message.answer("Введите ID для блокировки:")
    await callback.answer()
    await callback.message.bot.get_dispatcher().current_state(chat=callback.message.chat.id).set_state("wait_ban_user_id")

async def unban_user_start(callback: types.CallbackQuery):
    await callback.message.answer("Введите ID для разблокировки:")
    await callback.answer()
    await callback.message.bot.get_dispatcher().current_state(chat=callback.message.chat.id).set_state("wait_unban_user_id")

async def process_ban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await ban_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} заблокирован.")
    except:
        await message.answer("❌ Ошибка")
    await state.finish()

async def process_unban_user(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await unban_user(user_id)
        await message.answer(f"✅ Пользователь {user_id} разблокирован.")
    except:
        await message.answer("❌ Ошибка")
    await state.finish()

# Массовая рассылка
async def broadcast_message(message: types.Message, state: FSMContext):
    text = message.text
    users = await get_all_users()
    count = 0
    for u in users:
        try:
            await message.bot.send_message(u.tg_user_id, text)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await message.answer(f"✅ Отправлено {count} пользователям.")
    await state.finish()

# Промокоды
async def promo_codes_menu(callback: types.CallbackQuery):
    promos = await get_all_promos()
    text = "🎁 *Промокоды:*\n\n"
    for p in promos:
        text += f"• `{p.code}` | +{p.days} дн. | {p.used_count}/{p.max_uses}\n"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Создать", callback_data="admin_create_promo"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="admin_panel"))
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)

async def create_promo_start(callback: types.CallbackQuery):
    await callback.message.answer("Введите код промокода:")
    await CreatePromoState.waiting_code.set()
    await callback.answer()

async def create_promo_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    if await get_promo(code):
        await message.answer("❌ Уже существует.")
        return
    await state.update_data(code=code)
    await message.answer("Введите количество дней:")
    await CreatePromoState.waiting_days.set()

async def create_promo_days(message: types.Message, state: FSMContext):
    await state.update_data(days=int(message.text))
    await message.answer("Введите лимит активаций (1-100):")
    await CreatePromoState.waiting_max_uses.set()

async def create_promo_max_uses(message: types.Message, state: FSMContext):
    await state.update_data(max_uses=int(message.text))
    await message.answer("Введите срок ДД.ММ.ГГГГ или '-' для бессрочного:")
    await CreatePromoState.waiting_expiry.set()

async def create_promo_expiry(message: types.Message, state: FSMContext):
    expires_at = None
    if message.text != "-":
        try:
            expires_at = datetime.datetime.strptime(message.text, "%d.%m.%Y")
        except:
            await message.answer("❌ Неверный формат.")
            return
    data = await state.get_data()
    await create_promo(data['code'], data['days'], data['max_uses'], expires_at, message.from_user.id)
    await message.answer(f"✅ Промокод {data['code']} создан!")
    await state.finish()

async def activate_promo(message: types.Message):
    args = message.get_args()
    if not args:
        await message.answer("Использование: /promo <код>")
        return
    code = args.strip().upper()
    promo = await get_promo(code)
    if not promo:
        await message.answer("❌ Не найден")
        return
    if promo.max_uses <= promo.used_count:
        await message.answer("❌ Исчерпан")
        return
    if promo.expires_at and promo.expires_at < datetime.datetime.utcnow():
        await message.answer("❌ Истёк")
        return
    days = await use_promo(code)
    if not days:
        await message.answer("❌ Ошибка")
        return
    user = await get_user(message.from_user.id)
    if not user:
        user = await create_user(message.from_user.id)
    new_end = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    if user.subscription_end and user.subscription_end > datetime.datetime.utcnow():
        new_end = user.subscription_end + datetime.timedelta(days=days)
    await update_subscription(message.from_user.id, new_end)
    await message.answer(f"✅ Продлено на {days} дней. Новая дата: {new_end.strftime('%d.%m.%Y')}")

async def reset_campaign(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    args = message.get_args()
    if not args:
        await message.answer("Использование: /reset_campaign <id>")
        return
    try:
        cid = int(args)
        await update_campaign_status(cid, "pending")
        await message.answer(f"✅ Рассылка {cid} сброшена.")
    except:
        await message.answer("❌ Ошибка")

# Регистрация
def register_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, Command("admin"))
    dp.register_callback_query_handler(admin_callback, Text(startswith="admin_"), state=None)
    dp.register_callback_query_handler(give_subscription_button, text="admin_give_sub")
    dp.register_message_handler(give_subscription_user_id, state=GiveSubscriptionState.waiting_user_id)
    dp.register_message_handler(give_subscription_days, state=GiveSubscriptionState.waiting_days)
    dp.register_callback_query_handler(ban_user_start, text="admin_ban_user")
    dp.register_callback_query_handler(unban_user_start, text="admin_unban_user")
    dp.register_message_handler(process_ban_user, state="wait_ban_user_id")
    dp.register_message_handler(process_unban_user, state="wait_unban_user_id")
    dp.register_message_handler(broadcast_message, state=BroadcastState.waiting_message)
    dp.register_callback_query_handler(promo_codes_menu, text="admin_promos")
    dp.register_callback_query_handler(create_promo_start, text="admin_create_promo")
    dp.register_message_handler(create_promo_code, state=CreatePromoState.waiting_code)
    dp.register_message_handler(create_promo_days, state=CreatePromoState.waiting_days)
    dp.register_message_handler(create_promo_max_uses, state=CreatePromoState.waiting_max_uses)
    dp.register_message_handler(create_promo_expiry, state=CreatePromoState.waiting_expiry)
    dp.register_message_handler(activate_promo, Command("promo"))
    dp.register_message_handler(reset_campaign, Command("reset_campaign"))
