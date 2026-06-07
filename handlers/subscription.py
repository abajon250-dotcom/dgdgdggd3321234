from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user, update_subscription, add_payment, create_user
from utils.payment import create_cryptobot_invoice, check_cryptobot_payment
from keyboards.inline import back_to_main_keyboard
import datetime

PLANS = {"1day": {"days": 1, "price": 1}, "7days": {"days": 7, "price": 4}, "30days": {"days": 30, "price": 12}}

async def subscription_info(callback: types.CallbackQuery):
    user = await get_user(callback.from_user.id)
    if user and user.subscription_end and user.subscription_end > datetime.datetime.utcnow():
        text = f"✅ Подписка активна до {user.subscription_end.strftime('%d.%m.%Y')}"
    else:
        text = "❌ Подписка не активна. Выберите тариф:"
    kb = InlineKeyboardMarkup(row_width=1)
    for k, v in PLANS.items():
        kb.add(InlineKeyboardButton(f"{v['days']} дней - {v['price']} USD", callback_data=f"buy_plan:{k}"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    await callback.message.edit_text(text, reply_markup=kb)

async def buy_plan(callback: types.CallbackQuery, state: FSMContext):
    plan_key = callback.data.split(":")[1]
    plan = PLANS[plan_key]
    await state.update_data(plan=plan_key, amount=plan["price"])
    user = await get_user(callback.from_user.id)
    if not user:
        user = await create_user(callback.from_user.id)
    invoice = await create_cryptobot_invoice(plan["price"], f"Subscription {plan['days']} days")
    if invoice:
        await add_payment(user.id, plan["price"], "cryptobot", str(invoice["id"]))
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Проверить оплату", callback_data=f"check_payment:{invoice['id']}:{plan_key}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="subscription_info"))
        await callback.message.edit_text(f"💳 Счёт создан: {invoice['link']}\nПосле оплаты нажмите кнопку.", reply_markup=kb)
    else:
        await callback.answer("Ошибка", show_alert=True)

async def check_payment(callback: types.CallbackQuery):
    invoice_id = int(callback.data.split(":")[1])
    plan_key = callback.data.split(":")[2]
    status = await check_cryptobot_payment(invoice_id)
    if status == "paid":
        plan = PLANS[plan_key]
        new_end = datetime.datetime.utcnow() + datetime.timedelta(days=plan["days"])
        await update_subscription(callback.from_user.id, new_end)
        await callback.message.edit_text(f"✅ Подписка активирована до {new_end.strftime('%d.%m.%Y')}", reply_markup=back_to_main_keyboard())
    else:
        await callback.answer("Не оплачено", show_alert=True)

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(subscription_info, text="subscription_info")
    dp.register_callback_query_handler(buy_plan, Text(startswith="buy_plan:"))
    dp.register_callback_query_handler(check_payment, Text(startswith="check_payment:"))