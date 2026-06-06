import asyncio
import datetime
import os
import glob
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from database import (
    get_user, get_user_accounts, add_account, get_account_by_id,
    create_user, update_account_active_status, AsyncSessionLocal
)
from utils.telethon_client import (
    get_client_by_account,
    get_client_from_string,
    check_account_valid,
    change_name,
    change_avatar,
    send_message_to_username,
    join_chat,
    send_message_by_id,
    get_contacts_list,
    get_chats_list,
    get_dialogs_count,
    get_full_user_info,
    send_test_message
)
from keyboards.inline import accounts_list_keyboard, account_actions_keyboard, back_to_main_keyboard
from config import SESSIONS_DIR, API_ID, API_HASH

# Хранилище временных клиентов для процесса входа
temp_clients = {}

# ---------- FSM состояния ----------
class AddAccountPhone(StatesGroup):
    waiting_phone = State()
    waiting_code = State()
    waiting_password = State()

class ChangeNameState(StatesGroup):
    waiting_first_name = State()
    waiting_last_name = State()

class ChangeAvatarState(StatesGroup):
    waiting_photo = State()

class WriteGroupState(StatesGroup):
    waiting_group_username = State()
    waiting_message = State()

class JoinChatState(StatesGroup):
    waiting_link = State()

class WriteUserState(StatesGroup):
    waiting_user_identifier = State()
    waiting_message = State()

# ---------- Список и детали аккаунтов ----------
async def my_accounts(callback: types.CallbackQuery):
    accounts = await get_user_accounts(callback.from_user.id)
    if not accounts:
        await callback.message.edit_text("📭 У вас нет подключённых аккаунтов. Добавьте аккаунт:", reply_markup=back_to_main_keyboard())
        return
    await callback.message.edit_text("📱 Ваши аккаунты:", reply_markup=accounts_list_keyboard(accounts))

async def account_detail(callback: types.CallbackQuery):
    account_id = int(callback.data.split("_")[1])
    account = await get_account_by_id(account_id, callback.from_user.id)
    if not account:
        await callback.answer("❌ Аккаунт не найден")
        return
    text = f"""
📱 *Аккаунт:* {account.phone}
🌍 *Страна:* {account.country or 'Неизвестно'}
👤 *Имя:* {account.first_name} {account.last_name}
🆔 *Юзернейм:* @{account.username if account.username else 'Нет'}
📞 *Диалогов:* {account.contacts_count}
🚫 *Спам-блок:* {'Да' if account.spam_block else 'Нет'}
🔌 *Статус:* {'✅ Активен' if account.is_active else '❌ Неактивен'}
"""
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=account_actions_keyboard(account.id))

# ---------- Проверка валидности ----------
async def check_account_validity(callback: types.CallbackQuery):
    account_id = int(callback.data.split("_")[2])
    account = await get_account_by_id(account_id, callback.from_user.id)
    if not account:
        await callback.answer("❌ Аккаунт не найден", show_alert=True)
        return
    await callback.message.answer(f"🔄 Проверяю аккаунт {account.phone}...")
    try:
        client = await get_client_by_account(account)
        if await check_account_valid(client):
            await update_account_active_status(account_id, True)
            await callback.message.answer(f"✅ Аккаунт {account.phone} *валиден* (сессия активна).", parse_mode="Markdown")
        else:
            await update_account_active_status(account_id, False)
            await callback.message.answer(f"❌ Аккаунт {account.phone} *невалиден*. Сессия слетела, требуется переподключение.", parse_mode="Markdown")
    except Exception as e:
        await callback.message.answer(f"⚠️ Ошибка при проверке: {str(e)[:100]}")
    await callback.answer()

# ---------- Удаление аккаунта ----------
async def delete_account_confirm(callback: types.CallbackQuery):
    account_id = int(callback.data.split("_")[2])
    account = await get_account_by_id(account_id, callback.from_user.id)
    if not account:
        await callback.answer("❌ Аккаунт не найден", show_alert=True)
        return
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{account_id}"),
        InlineKeyboardButton("❌ Нет, отмена", callback_data=f"account_{account_id}")
    )
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить аккаунт {account.phone}?\n"
        "Это действие нельзя отменить. Сессия будет удалена.",
        reply_markup=kb
    )
    await callback.answer()

async def delete_account_execute(callback: types.CallbackQuery):
    account_id = int(callback.data.split("_")[2])
    account = await get_account_by_id(account_id, callback.from_user.id)
    if not account:
        await callback.answer("❌ Аккаунт не найден", show_alert=True)
        return
    if account.session_file:
        session_path = os.path.join(SESSIONS_DIR, account.session_file)
        if os.path.exists(session_path):
            os.remove(session_path)
    async with AsyncSessionLocal() as session:
        await session.delete(account)
        await session.commit()
    await callback.message.edit_text(f"✅ Аккаунт {account.phone} успешно удалён.", reply_markup=back_to_main_keyboard())
    await callback.answer()

# ---------- Добавление аккаунта через номер телефона ----------
async def add_account_choice(callback: types.CallbackQuery):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📞 По номеру телефона", callback_data="add_by_phone"),
        InlineKeyboardButton("📁 Из TDATA (zip)", callback_data="add_by_tdata"),
        InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
    )
    await callback.message.edit_text("Выберите способ добавления аккаунта:", reply_markup=kb)

async def add_by_phone(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите номер телефона в международном формате (например +380123456789):")
    await AddAccountPhone.waiting_phone.set()
    await callback.answer()

async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    await state.update_data(phone=phone)
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        await state.update_data(phone_code_hash=sent.phone_code_hash)
        temp_clients[message.from_user.id] = client
        await message.answer("Введите код подтверждения, полученный в Telegram:")
        await AddAccountPhone.waiting_code.set()
    except errors.PhoneNumberInvalidError:
        await message.answer("Неверный номер телефона")
        await state.finish()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.finish()

async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    data = await state.get_data()
    phone = data["phone"]
    phone_code_hash = data.get("phone_code_hash")
    client = temp_clients.get(message.from_user.id)
    if not client:
        await message.answer("Сессия потеряна. Начните заново.")
        await state.finish()
        return
    try:
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        session_string = client.session.save()
        await client.disconnect()
        del temp_clients[message.from_user.id]

        client2 = await get_client_from_string(session_string)
        user_info = await get_full_user_info(client2)
        dialogs_count = await get_dialogs_count(client2)
        spam_block = not await send_test_message(client2)

        user_db = await get_user(message.from_user.id)
        if not user_db:
            user_db = await create_user(message.from_user.id)

        await add_account(
            user_id=user_db.id,
            phone=phone,
            country=None,
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            username=user_info['username'],
            reg_date=None,
            contacts_count=dialogs_count,
            spam_block=spam_block,
            session_string=session_string
        )

        accounts = await get_user_accounts(message.from_user.id)
        new_account = accounts[-1]
        text = f"""
📱 Аккаунт: {new_account.phone}
🌍 Страна: {new_account.country or 'Неизвестно'}
👤 Имя: {new_account.first_name} {new_account.last_name}
🆔 Юзернейм: @{new_account.username if new_account.username else 'Нет'}
📞 Кол-во контактов/чатов: {new_account.contacts_count}
🚫 Спам-блок: {'Да' if new_account.spam_block else 'Нет'}
🔌 Статус: {'Активен' if new_account.is_active else 'Неактивен'}
        """
        await message.answer(text, reply_markup=account_actions_keyboard(new_account.id))
        await state.finish()
    except errors.SessionPasswordNeededError:
        await message.answer("Включена двухфакторная аутентификация. Введите пароль:")
        await AddAccountPhone.waiting_password.set()
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.finish()
    finally:
        if client and client.is_connected():
            await client.disconnect()

async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    phone = data["phone"]
    client = temp_clients.get(message.from_user.id)
    if not client:
        await message.answer("Сессия потеряна. Начните заново.")
        await state.finish()
        return
    try:
        await client.sign_in(password=password)
        session_string = client.session.save()
        await client.disconnect()
        del temp_clients[message.from_user.id]

        client2 = await get_client_from_string(session_string)
        user_info = await get_full_user_info(client2)
        dialogs_count = await get_dialogs_count(client2)
        spam_block = not await send_test_message(client2)

        user_db = await get_user(message.from_user.id)
        if not user_db:
            user_db = await create_user(message.from_user.id)

        await add_account(
            user_id=user_db.id,
            phone=phone,
            country=None,
            first_name=user_info['first_name'],
            last_name=user_info['last_name'],
            username=user_info['username'],
            reg_date=None,
            contacts_count=dialogs_count,
            spam_block=spam_block,
            session_string=session_string
        )

        accounts = await get_user_accounts(message.from_user.id)
        new_account = accounts[-1]
        text = f"""
📱 Аккаунт: {new_account.phone}
🌍 Страна: {new_account.country or 'Неизвестно'}
👤 Имя: {new_account.first_name} {new_account.last_name}
🆔 Юзернейм: @{new_account.username if new_account.username else 'Нет'}
📞 Кол-во контактов/чатов: {new_account.contacts_count}
🚫 Спам-блок: {'Да' if new_account.spam_block else 'Нет'}
🔌 Статус: {'Активен' if new_account.is_active else 'Неактивен'}
        """
        await message.answer(text, reply_markup=account_actions_keyboard(new_account.id))
        await state.finish()
    except errors.PasswordHashInvalidError:
        await message.answer("❌ Неверный пароль. Попробуйте снова:")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
        await state.finish()
    finally:
        if client and client.is_connected():
            await client.disconnect()

# ---------- Добавление через TDATA (заглушка) ----------
async def add_by_tdata(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Функция временно недоступна. Используйте вход по номеру телефона.")
    await state.finish()

async def handle_tdata_zip(message: types.Message, state: FSMContext):
    await message.answer("Функция временно недоступна. Используйте вход по номеру телефона.")
    await state.finish()

# ---------- Действия с аккаунтом ----------
async def change_name_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Введите новое имя (first_name):")
    await ChangeNameState.waiting_first_name.set()
    await callback.answer()

async def change_name_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите фамилию (last_name) или '-' для пропуска:")
    await ChangeNameState.waiting_last_name.set()

async def change_name_last_name(message: types.Message, state: FSMContext):
    last_name = message.text if message.text != "-" else ""
    data = await state.get_data()
    account_id = data['account_id']
    first_name = data['first_name']
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("❌ Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        await change_name(client, first_name, last_name)
        await message.answer("✅ Имя успешно изменено!", reply_markup=back_to_main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

async def change_avatar_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Отправьте новое фото (как файл или обычное фото):")
    await ChangeAvatarState.waiting_photo.set()
    await callback.answer()

async def change_avatar_photo(message: types.Message, state: FSMContext):
    if not message.photo and not message.document:
        await message.answer("Пожалуйста, отправьте фото.")
        return
    data = await state.get_data()
    account_id = data['account_id']
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("❌ Аккаунт не найден")
        await state.finish()
        return
    if message.photo:
        photo = message.photo[-1]
        file_path = f"{SESSIONS_DIR}/temp_avatar_{account_id}.jpg"
        await photo.download(destination=file_path)
    else:
        file_path = await message.document.download(destination_dir=SESSIONS_DIR)
    client = await get_client_by_account(account)
    try:
        await change_avatar(client, file_path)
        os.remove(file_path)
        await message.answer("✅ Аватар изменён!", reply_markup=back_to_main_keyboard())
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

async def write_group_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Введите username группы (например @mygroup) или invite-ссылку:")
    await WriteGroupState.waiting_group_username.set()
    await callback.answer()

async def write_group_username(message: types.Message, state: FSMContext):
    await state.update_data(group_identifier=message.text.strip())
    await message.answer("Введите текст сообщения:")
    await WriteGroupState.waiting_message.set()

async def write_group_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    account_id = data['account_id']
    group_identifier = data['group_identifier']
    text = message.text
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("❌ Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        if group_identifier.startswith("https://t.me/") or group_identifier.startswith("t.me/"):
            await join_chat(client, group_identifier)
            username = group_identifier.split("/")[-1]
            await send_message_to_username(client, username, text)
        else:
            username = group_identifier.lstrip('@')
            await send_message_to_username(client, username, text)
        await message.answer("✅ Сообщение отправлено!", reply_markup=back_to_main_keyboard())
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except errors.rpcerrorlist.ChatWriteForbiddenError:
        await message.answer("❌ Нельзя писать в этот чат (нет прав).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

async def join_chat_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Введите ссылку (https://t.me/...) или username:")
    await JoinChatState.waiting_link.set()
    await callback.answer()

async def join_chat_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    account_id = data['account_id']
    link = message.text.strip()
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("❌ Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        await join_chat(client, link)
        await message.answer("✅ Вы вступили в группу/канал!", reply_markup=back_to_main_keyboard())
    except errors.rpcerrorlist.ChannelInvalidError:
        await message.answer("❌ Неверная ссылка или канал не существует.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

async def write_user_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Введите username (например @user) или ID пользователя:")
    await WriteUserState.waiting_user_identifier.set()
    await callback.answer()

async def write_user_identifier(message: types.Message, state: FSMContext):
    await state.update_data(user_identifier=message.text.strip())
    await message.answer("Введите текст сообщения:")
    await WriteUserState.waiting_message.set()

async def write_user_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    account_id = data['account_id']
    identifier = data['user_identifier']
    text = message.text
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("❌ Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        if identifier.isdigit():
            await send_message_by_id(client, int(identifier), text)
        else:
            username = identifier.lstrip('@')
            await send_message_to_username(client, username, text)
        await message.answer("✅ Сообщение отправлено!", reply_markup=back_to_main_keyboard())
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except errors.rpcerrorlist.PeerIdInvalidError:
        await message.answer("❌ Пользователь не найден или не может получать сообщения.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(my_accounts, text="my_accounts")
    dp.register_callback_query_handler(account_detail, Text(startswith="account_"))
    dp.register_callback_query_handler(check_account_validity, Text(startswith="check_valid_"))
    dp.register_callback_query_handler(delete_account_confirm, Text(startswith="delete_account_"))
    dp.register_callback_query_handler(delete_account_execute, Text(startswith="confirm_delete_"))

    dp.register_callback_query_handler(add_account_choice, text="add_account_choice")
    dp.register_callback_query_handler(add_by_phone, text="add_by_phone")
    dp.register_message_handler(process_phone, state=AddAccountPhone.waiting_phone)
    dp.register_message_handler(process_code, state=AddAccountPhone.waiting_code)
    dp.register_message_handler(process_password, state=AddAccountPhone.waiting_password)
    dp.register_callback_query_handler(add_by_tdata, text="add_by_tdata")
    dp.register_message_handler(handle_tdata_zip, state="waiting_tdata_zip", content_types=['document'])

    dp.register_callback_query_handler(change_name_start, Text(startswith="change_name_"))
    dp.register_message_handler(change_name_first_name, state=ChangeNameState.waiting_first_name)
    dp.register_message_handler(change_name_last_name, state=ChangeNameState.waiting_last_name)

    dp.register_callback_query_handler(change_avatar_start, Text(startswith="change_avatar_"))
    dp.register_message_handler(change_avatar_photo, state=ChangeAvatarState.waiting_photo, content_types=['photo', 'document'])

    dp.register_callback_query_handler(write_group_start, Text(startswith="write_group_"))
    dp.register_message_handler(write_group_username, state=WriteGroupState.waiting_group_username)
    dp.register_message_handler(write_group_message, state=WriteGroupState.waiting_message)

    dp.register_callback_query_handler(join_chat_start, Text(startswith="join_chat_"))
    dp.register_message_handler(join_chat_link, state=JoinChatState.waiting_link)

    dp.register_callback_query_handler(write_user_start, Text(startswith="write_user_"))
    dp.register_message_handler(write_user_identifier, state=WriteUserState.waiting_user_identifier)
    dp.register_message_handler(write_user_message, state=WriteUserState.waiting_message)