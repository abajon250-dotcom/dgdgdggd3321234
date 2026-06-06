import datetime
import time
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, update_subscription, add_payment, update_payment_status, create_user
from utils.payment import create_cryptobot_invoice, check_cryptobot_payment
from keyboards.inline import subscription_plans_keyboard, back_to_main_keyboard

PLANS = {
    "1day": {"days": 1, "price": 0.5},
    "7days": {"days": 7, "price": 3},
    "30days": {"days": 30, "price": 12}
}

async def subscription_info(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user and user.subscription_end and user.subscription_end > datetime.datetime.utcnow():
        days_left = (user.subscription_end - datetime.datetime.utcnow()).days
        text = f"✅ Подписка активна до {user.subscription_end.strftime('%d.%m.%Y %H:%M')}\nОсталось дней: {days_left}\n\nВыберите тариф для продления:"
    else:
        text = "❌ Подписка не активна. Выберите тариф:"
    await callback.message.edit_text(text, reply_markup=subscription_plans_keyboard())

async def select_plan(callback: types.CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    plan = PLANS[plan_key]
    await state.update_data(plan=plan_key, amount=plan["price"])
    # Создаём инвойс в CryptoBot
    invoice = await create_cryptobot_invoice(plan["price"], "USD", f"Subscription {plan['days']} days")
    if invoice:
        await add_payment(callback.from_user.id, plan["price"], "cryptobot", str(invoice["id"]))
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_cryptobot:{invoice['id']}:{plan_key}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="subscription_info"))
        await callback.message.edit_text(
            f"💳 Счёт создан!\nСумма: {plan['price']} USD\nСсылка для оплаты: {invoice['link']}\n\nПосле оплаты нажмите «Проверить оплату».",
            reply_markup=kb
        )
    else:
        await callback.answer("Ошибка создания счёта. Попробуйте позже.", show_alert=True)

async def check_cryptobot_payment_handler(callback: types.CallbackQuery):
    invoice_id = callback.data.split(":")[1]
    plan_key = callback.data.split(":")[2]
    status = await check_cryptobot_payment(int(invoice_id))
    if status == "paid":
        plan = PLANS[plan_key]
        new_end = datetime.datetime.utcnow() + datetime.timedelta(days=plan["days"])
        await update_subscription(callback.from_user.id, new_end)
        await update_payment_status(invoice_id, "paid")
        await callback.message.edit_text(f"✅ Подписка активирована до {new_end.strftime('%d.%m.%Y %H:%M')}", reply_markup=back_to_main_keyboard())
    else:
        await callback.answer("Оплата не найдена или ещё не обработана. Попробуйте позже.", show_alert=True)

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(subscription_info, text="subscription_info")
    dp.register_callback_query_handler(select_plan, Text(startswith="buy_plan:"))
    dp.register_callback_query_handler(check_cryptobot_payment_handler, Text(startswith="check_cryptobot:"))