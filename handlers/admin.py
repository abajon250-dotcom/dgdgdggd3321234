import asyncio, datetime
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command, Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import (
    get_all_users, get_user_accounts, get_all_payments, get_user,
    update_subscription, get_all_campaigns, update_campaign_status,
    ban_user, unban_user, create_promo, get_promo, get_all_promos,
    create_user, use_promo
)
from keyboards.inline import admin_panel_keyboard, back_to_main_keyboard, admin_ban_keyboard
from config import ADMIN_IDS

class GiveSub(StatesGroup):
    uid = State()
    days = State()

class CreatePromo(StatesGroup):
    code = State()
    days = State()
    max_uses = State()
    expiry = State()

class Broadcast(StatesGroup):
    msg = State()

async def admin_panel(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.answer("Нет доступа")
    await message.answer("👑 Админ-панель", reply_markup=admin_panel_keyboard())

async def admin_callback(call: types.CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        return await call.answer("Нет доступа", show_alert=True)
    action = call.data.split("_")[1]
    if action == "give_sub":
        await call.message.answer("Введите Telegram ID:")
        await GiveSub.uid.set()
    elif action == "users":
        users = await get_all_users()
        text = "📋 Пользователи:\n"
        for u in users:
            accounts = await get_user_accounts(u.tg_user_id)
            sub = u.subscription_end.strftime('%d.%m.%Y') if u.subscription_end else 'Нет'
            text += f"🆔 {u.tg_user_id} | Подписка до: {sub} | Акков: {len(accounts)}\n"
        await call.message.edit_text(text, reply_markup=back_to_main_keyboard())
    elif action == "payments":
        pays = await get_all_payments(50)
        text = "💰 Платежи:\n"
        for p in pays:
            text += f"🧾 {p.amount} {p.currency} | {p.payment_system} | {p.status}\n"
        await call.message.edit_text(text, reply_markup=back_to_main_keyboard())
    elif action == "stats":
        users = await get_all_users()
        total_acc = 0
        for u in users:
            total_acc += len(await get_user_accounts(u.tg_user_id))
        await call.message.edit_text(f"📊 Пользователей: {len(users)}\n📱 Аккаунтов: {total_acc}", reply_markup=back_to_main_keyboard())
    elif action == "campaigns":
        camps = await get_all_campaigns(50)
        text = "📢 Рассылки:\n"
        for c in camps:
            text += f"ID: {c.id} | Статус: {c.status}\n"
        await call.message.edit_text(text, reply_markup=back_to_main_keyboard())
    elif action == "promos":
        await promo_menu(call)
    elif action == "ban_menu":
        await call.message.edit_text("🔒 Блокировка", reply_markup=admin_ban_keyboard())
    elif action == "broadcast":
        await call.message.answer("Введите текст для рассылки:")
        await Broadcast.msg.set()
    await call.answer()

# Give subscription FSM
async def give_sub_uid(message: types.Message, state: FSMContext):
    await state.update_data(uid=int(message.text))
    await message.answer("Введите количество дней:")
    await GiveSub.days.set()

async def give_sub_days(message: types.Message, state: FSMContext):
    data = await state.get_data()
    uid = data['uid']
    days = int(message.text)
    new_end = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    await update_subscription(uid, new_end)
    await message.answer(f"✅ Подписка выдана пользователю {uid} на {days} дней.")
    await state.finish()

# Ban/Unban
async def ban_user_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите ID для блокировки:")
    await state.set_state("ban_id")

async def unban_user_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите ID для разблокировки:")
    await state.set_state("unban_id")

async def process_ban(message: types.Message, state: FSMContext):
    await ban_user(int(message.text))
    await message.answer("✅ Заблокирован.")
    await state.finish()

async def process_unban(message: types.Message, state: FSMContext):
    await unban_user(int(message.text))
    await message.answer("✅ Разблокирован.")
    await state.finish()

# Broadcast
async def broadcast_msg(message: types.Message, state: FSMContext):
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

# Promo codes
async def promo_menu(call: types.CallbackQuery):
    promos = await get_all_promos()
    text = "🎁 Промокоды:\n"
    for p in promos:
        text += f"• {p.code} | +{p.days} дн. | {p.used_count}/{p.max_uses}\n"
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("➕ Создать", callback_data="admin_create_promo"))
    await call.message.edit_text(text, reply_markup=kb)

async def create_promo_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("Введите код промокода:")
    await CreatePromo.code.set()

async def create_promo_code(m: types.Message, state: FSMContext):
    await state.update_data(code=m.text.upper())
    await m.answer("Введите количество дней:")
    await CreatePromo.days.set()

async def create_promo_days(m: types.Message, state: FSMContext):
    await state.update_data(days=int(m.text))
    await m.answer("Введите лимит активаций:")
    await CreatePromo.max_uses.set()

async def create_promo_max_uses(m: types.Message, state: FSMContext):
    await state.update_data(max_uses=int(m.text))
    await m.answer("Введите дату ДД.ММ.ГГГГ или '-' :")
    await CreatePromo.expiry.set()

async def create_promo_expiry(m: types.Message, state: FSMContext):
    data = await state.get_data()
    expires = None
    if m.text != '-':
        expires = datetime.datetime.strptime(m.text, "%d.%m.%Y")
    await create_promo(data['code'], data['days'], data['max_uses'], expires, m.from_user.id)
    await m.answer(f"✅ Промокод {data['code']} создан.")
    await state.finish()

async def activate_promo(message: types.Message):
    args = message.get_args()
    if not args:
        return await message.answer("/promo КОД")
    code = args.upper()
    promo = await get_promo(code)
    if not promo:
        return await message.answer("❌ Не найден")
    days = await use_promo(code)
    if not days:
        return await message.answer("❌ Неактивен или исчерпан")
    user = await get_user(message.from_user.id)
    if not user:
        user = await create_user(message.from_user.id)
    new_end = datetime.datetime.utcnow() + datetime.timedelta(days=days)
    if user.subscription_end and user.subscription_end > datetime.datetime.utcnow():
        new_end = user.subscription_end + datetime.timedelta(days=days)
    await update_subscription(message.from_user.id, new_end)
    await message.answer(f"✅ Подписка продлена на {days} дней.")

def register_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_panel, Command("admin"))
    dp.register_callback_query_handler(admin_callback, Text(startswith="admin_"), state=None)
    dp.register_message_handler(give_sub_uid, state=GiveSub.uid)
    dp.register_message_handler(give_sub_days, state=GiveSub.days)
    dp.register_callback_query_handler(ban_user_start, text="admin_ban_user")
    dp.register_callback_query_handler(unban_user_start, text="admin_unban_user")
    dp.register_message_handler(process_ban, state="ban_id")
    dp.register_message_handler(process_unban, state="unban_id")
    dp.register_message_handler(broadcast_msg, state=Broadcast.msg)
    dp.register_callback_query_handler(promo_menu, text="admin_promos")
    dp.register_callback_query_handler(create_promo_start, text="admin_create_promo")
    dp.register_message_handler(create_promo_code, state=CreatePromo.code)
    dp.register_message_handler(create_promo_days, state=CreatePromo.days)
    dp.register_message_handler(create_promo_max_uses, state=CreatePromo.max_uses)
    dp.register_message_handler(create_promo_expiry, state=CreatePromo.expiry)
    dp.register_message_handler(activate_promo, Command("promo"))