import json
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text, Command
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_campaigns, get_campaign_by_id, get_user_accounts, get_user_templates, add_campaign, get_user, get_account_by_id
from utils.campaign_manager import start_campaign, pause_campaign, resume_campaign, cancel_campaign
from utils.telethon_client import get_client_by_account, get_contacts_list
from keyboards.inline import campaigns_list_keyboard, campaign_control_keyboard, back_to_main_keyboard
from utils.gif_sender import send_gif

class CreateCampaignState(StatesGroup):
    waiting_name = State()
    waiting_account = State()
    waiting_recipients_type = State()
    waiting_recipients = State()
    waiting_text_source = State()
    waiting_template_or_text = State()
    waiting_delay = State()

async def my_campaigns(callback: types.CallbackQuery):
    campaigns = await get_user_campaigns(callback.from_user.id)
    await callback.message.edit_text("📋 Ваши рассылки:", reply_markup=campaigns_list_keyboard(campaigns))

async def view_campaign(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[1])
    campaign = await get_campaign_by_id(campaign_id, callback.from_user.id)
    if not campaign:
        await callback.answer("❌ Рассылка не найдена")
        return
    text = f"""
📢 *Рассылка #{campaign.id}*
📝 Название: {campaign.name or 'Без названия'}
📱 Аккаунт: {campaign.account.phone}
📊 Статус: {campaign.status}
✅ Отправлено: {campaign.sent_count}/{campaign.total_recipients}
⏱ Задержка: {campaign.delay} сек
⏰ Последняя отправка: {campaign.last_sent_at.strftime('%d.%m.%Y %H:%M:%S') if campaign.last_sent_at else 'Не начата'}
    """
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=campaign_control_keyboard(campaign.id, campaign.status))

async def status_campaign_callback(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[2])  # status_campaign_123
    campaign = await get_campaign_by_id(campaign_id, callback.from_user.id)
    if not campaign:
        await callback.answer("❌ Рассылка не найдена")
        return
    text = f"""
📢 *Рассылка #{campaign.id}*
📝 Название: {campaign.name or 'Без названия'}
📱 Аккаунт: {campaign.account.phone}
📊 Статус: {campaign.status}
✅ Отправлено: {campaign.sent_count}/{campaign.total_recipients}
⏱ Задержка: {campaign.delay} сек
⏰ Последняя отправка: {campaign.last_sent_at.strftime('%d.%m.%Y %H:%M:%S') if campaign.last_sent_at else 'Не начата'}
    """
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=campaign_control_keyboard(campaign.id, campaign.status))
    await callback.answer()

async def create_campaign_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите название рассылки (или '-' для пропуска):")
    await CreateCampaignState.waiting_name.set()

async def process_campaign_name(message: types.Message, state: FSMContext):
    name = message.text if message.text != "-" else None
    await state.update_data(name=name)
    accounts = await get_user_accounts(message.from_user.id)
    if not accounts:
        await message.answer("❌ Нет аккаунтов. Сначала добавьте аккаунт.", reply_markup=back_to_main_keyboard())
        await state.finish()
        return
    kb = InlineKeyboardMarkup(row_width=1)
    for acc in accounts:
        kb.add(InlineKeyboardButton(acc.phone, callback_data=f"camp_acc_{acc.id}"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="my_campaigns"))
    await message.answer("📱 Выберите аккаунт-отправитель:", reply_markup=kb)
    await CreateCampaignState.waiting_account.set()

async def select_account(callback: types.CallbackQuery, state: FSMContext):
    acc_id = int(callback.data.split("_")[2])  # camp_acc_123
    await state.update_data(account_id=acc_id)
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📞 Из контактов", callback_data="rec_contacts"),
        InlineKeyboardButton("✍️ Ввести вручную", callback_data="rec_manual"),
        InlineKeyboardButton("◀️ Назад", callback_data="my_campaigns")
    )
    await callback.message.edit_text("👥 Выберите источник получателей:", reply_markup=kb)
    await CreateCampaignState.waiting_recipients_type.set()

async def process_recipients_type(callback: types.CallbackQuery, state: FSMContext):
    rec_type = callback.data.split("_")[1]  # contacts или manual
    await state.update_data(recipients_type=rec_type)
    if rec_type == "manual":
        await callback.message.answer("✏️ Введите список получателей (по одному на строку в формате username или ID):")
        await CreateCampaignState.waiting_recipients.set()
    else:  # rec_contacts
        data = await state.get_data()
        account_id = data['account_id']
        account = await get_account_by_id(account_id, callback.from_user.id)
        if not account:
            await callback.answer("❌ Аккаунт не найден")
            return
        try:
            client = await get_client_by_account(account)
            contacts = await get_contacts_list(client)  # только контакты
            if not contacts:
                await callback.message.answer("⚠️ Не найдено контактов. Введите вручную.")
                await CreateCampaignState.waiting_recipients.set()
                return
            recipients = []
            for c in contacts:
                if c['username']:
                    recipients.append({"type": "username", "identifier": c['username']})
                else:
                    recipients.append({"type": "user_id", "identifier": str(c['id'])})
            await state.update_data(recipients=recipients)
            kb = InlineKeyboardMarkup(row_width=2)
            kb.add(
                InlineKeyboardButton("📄 Использовать шаблон", callback_data="text_template"),
                InlineKeyboardButton("✍️ Ввести текст вручную", callback_data="text_manual")
            )
            await callback.message.edit_text(f"✅ Найдено {len(recipients)} контактов. Выберите текст:", reply_markup=kb)
            await CreateCampaignState.waiting_text_source.set()
        except Exception as e:
            await callback.message.answer(f"❌ Ошибка: {e}")
            await state.finish()
    await callback.answer()

async def process_recipients_manual(message: types.Message, state: FSMContext):
    lines = message.text.strip().split('\n')
    recipients = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('@'):
            recipients.append({"type": "username", "identifier": line[1:]})
        elif line.isdigit():
            recipients.append({"type": "user_id", "identifier": line})
        else:
            recipients.append({"type": "username", "identifier": line})
    await state.update_data(recipients=recipients)
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📄 Использовать шаблон", callback_data="text_template"),
        InlineKeyboardButton("✍️ Ввести текст вручную", callback_data="text_manual")
    )
    await message.answer(f"✅ Добавлено {len(recipients)} получателей. Выберите текст:", reply_markup=kb)
    await CreateCampaignState.waiting_text_source.set()

async def select_text_source(callback: types.CallbackQuery, state: FSMContext):
    source = callback.data.split("_")[1]  # template или manual
    if source == "template":
        templates = await get_user_templates(callback.from_user.id)
        if not templates:
            await callback.answer("❌ Нет шаблонов. Сначала создайте шаблон.", show_alert=True)
            return
        kb = InlineKeyboardMarkup(row_width=1)
        for tpl in templates:
            kb.add(InlineKeyboardButton(tpl.name, callback_data=f"temp_{tpl.id}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="create_campaign"))
        await callback.message.edit_text("📄 Выберите шаблон:", reply_markup=kb)
        await CreateCampaignState.waiting_template_or_text.set()
    else:
        await callback.message.answer("✏️ Введите текст сообщения:")
        await CreateCampaignState.waiting_template_or_text.set()

async def process_template_selection(callback: types.CallbackQuery, state: FSMContext):
    template_id = int(callback.data.split("_")[1])  # temp_123
    await state.update_data(template_id=template_id, custom_text=None)
    await callback.message.answer("⏱ Введите задержку (в секундах, минимум 3):")
    await CreateCampaignState.waiting_delay.set()

async def process_manual_text(message: types.Message, state: FSMContext):
    await state.update_data(template_id=None, custom_text=message.text)
    await message.answer("⏱ Введите задержку (в секундах, минимум 3):")
    await CreateCampaignState.waiting_delay.set()

async def process_campaign_delay(message: types.Message, state: FSMContext):
    try:
        delay = int(message.text)
        if delay < 3:
            await message.answer("⚠️ Минимум 3 секунды. Повторите:")
            return
    except ValueError:
        await message.answer("❌ Введите число")
        return
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    campaign = await add_campaign(
        user_id=user.id,
        account_id=data['account_id'],
        name=data.get('name'),
        template_id=data.get('template_id'),
        custom_text=data.get('custom_text'),
        delay=delay,
        recipients=data['recipients']
    )
    await message.answer(f"✅ Рассылка #{campaign.id} создана! Теперь вы можете запустить её из списка.", reply_markup=back_to_main_keyboard())
    await state.finish()

async def start_campaign_handler(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[2])  # start_campaign_123
    success = await start_campaign(campaign_id, callback.from_user.id)
    if success:
        await send_gif(callback, "campaign_started", "🚀 Рассылка запущена!")
        await view_campaign(callback)
    else:
        await send_gif(callback, "error", "❌ Не удалось запустить")
        await callback.answer("Не удалось запустить (аккаунт занят или нет подписки)", show_alert=True)

async def pause_campaign_handler(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[2])
    await pause_campaign(campaign_id, callback.from_user.id)
    await callback.answer("⏸ Рассылка на паузе")
    await view_campaign(callback)

async def resume_campaign_handler(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[2])
    await resume_campaign(campaign_id, callback.from_user.id)
    await callback.answer("▶️ Рассылка возобновлена")
    await view_campaign(callback)

async def cancel_campaign_handler(callback: types.CallbackQuery):
    campaign_id = int(callback.data.split("_")[2])
    await cancel_campaign(campaign_id, callback.from_user.id)
    await callback.answer("❌ Рассылка отменена")
    await view_campaign(callback)

async def campaign_status_command(message: types.Message):
    args = message.get_args()
    if not args:
        await message.answer("Использование: /status <id_рассылки>")
        return
    try:
        campaign_id = int(args)
        campaign = await get_campaign_by_id(campaign_id, message.from_user.id)
        if not campaign:
            await message.answer("❌ Рассылка не найдена")
            return
        text = f"""
📊 *Статус рассылки #{campaign.id}*
📝 Название: {campaign.name or 'Без названия'}
📱 Аккаунт: {campaign.account.phone}
📊 Статус: {campaign.status}
✅ Отправлено: {campaign.sent_count}/{campaign.total_recipients}
⏱ Задержка: {campaign.delay} сек
⏰ Последняя отправка: {campaign.last_sent_at.strftime('%d.%m.%Y %H:%M:%S') if campaign.last_sent_at else 'Не начата'}
        """
        await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(my_campaigns, text="my_campaigns")
    dp.register_callback_query_handler(view_campaign, Text(startswith="campaign_"))
    dp.register_callback_query_handler(status_campaign_callback, Text(startswith="status_campaign_"))
    dp.register_callback_query_handler(create_campaign_start, text="create_campaign")
    dp.register_message_handler(process_campaign_name, state=CreateCampaignState.waiting_name)
    dp.register_callback_query_handler(select_account, Text(startswith="camp_acc_"), state=CreateCampaignState.waiting_account)
    dp.register_callback_query_handler(process_recipients_type, Text(startswith="rec_"), state=CreateCampaignState.waiting_recipients_type)
    dp.register_message_handler(process_recipients_manual, state=CreateCampaignState.waiting_recipients)
    dp.register_callback_query_handler(select_text_source, Text(startswith="text_"), state=CreateCampaignState.waiting_text_source)
    dp.register_callback_query_handler(process_template_selection, Text(startswith="temp_"), state=CreateCampaignState.waiting_template_or_text)
    dp.register_message_handler(process_manual_text, state=CreateCampaignState.waiting_template_or_text)
    dp.register_message_handler(process_campaign_delay, state=CreateCampaignState.waiting_delay)
    dp.register_callback_query_handler(start_campaign_handler, Text(startswith="start_campaign_"))
    dp.register_callback_query_handler(pause_campaign_handler, Text(startswith="pause_campaign_"))
    dp.register_callback_query_handler(resume_campaign_handler, Text(startswith="resume_campaign_"))
    dp.register_callback_query_handler(cancel_campaign_handler, Text(startswith="cancel_campaign_"))
    dp.register_message_handler(campaign_status_command, Command("status"))