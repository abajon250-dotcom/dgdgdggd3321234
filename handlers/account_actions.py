import os
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from telethon import errors
from database import get_account_by_id
from utils.telethon_client import get_client_by_account, send_message_to_username, join_chat, change_name, change_avatar
from keyboards.inline import account_actions_keyboard, back_to_main_keyboard
from config import SESSIONS_DIR

class WriteGroupState(StatesGroup):
    waiting_group_username = State()
    waiting_message = State()

class JoinChatState(StatesGroup):
    waiting_link = State()

class WriteUserState(StatesGroup):
    waiting_user_identifier = State()
    waiting_message = State()

class ChangeNameState(StatesGroup):
    waiting_first_name = State()
    waiting_last_name = State()

class ChangeAvatarState(StatesGroup):
    waiting_photo = State()

# ---------- Написать в группу ----------
async def write_group_start(callback: types.CallbackQuery, state: FSMContext):
    account_id = int(callback.data.split("_")[2])
    await state.update_data(account_id=account_id)
    await callback.message.answer("Введите username группы (например @mygroup) или invite-ссылку:")
    await WriteGroupState.waiting_group_username.set()
    await callback.answer()

async def write_group_username(message: types.Message, state: FSMContext):
    await state.update_data(group_identifier=message.text.strip())
    await message.answer("Введите текст сообщения для отправки в группу:")
    await WriteGroupState.waiting_message.set()

async def write_group_message(message: types.Message, state: FSMContext):
    data = await state.get_data()
    account_id = data['account_id']
    group_identifier = data['group_identifier']
    text = message.text
    account = await get_account_by_id(account_id, message.from_user.id)
    if not account:
        await message.answer("Аккаунт не найден")
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
        await message.answer("✅ Сообщение отправлено в группу!", reply_markup=back_to_main_keyboard())
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except errors.rpcerrorlist.ChatWriteForbiddenError:
        await message.answer("❌ Нельзя писать в этот чат (нет прав).")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

# ---------- Вступить в группу/канал ----------
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
        await message.answer("Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        await join_chat(client, link)
        await message.answer("✅ Вы вступили в группу/канал!", reply_markup=back_to_main_keyboard())
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except errors.rpcerrorlist.ChannelInvalidError:
        await message.answer("❌ Неверная ссылка или канал не существует.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

# ---------- Написать пользователю ----------
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
        await message.answer("Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        if identifier.isdigit():
            await client.send_message(int(identifier), text)
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

# ---------- Сменить имя ----------
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
        await message.answer("Аккаунт не найден")
        await state.finish()
        return
    client = await get_client_by_account(account)
    try:
        await change_name(client, first_name, last_name)
        await message.answer("✅ Имя успешно изменено!", reply_markup=back_to_main_keyboard())
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

# ---------- Сменить аватар ----------
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
        await message.answer("Аккаунт не найден")
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
    except errors.FloodWaitError as e:
        await message.answer(f"⚠️ Флуд-лимит. Подождите {e.seconds} секунд.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    await state.finish()

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(write_group_start, Text(startswith="write_group_"))
    dp.register_message_handler(write_group_username, state=WriteGroupState.waiting_group_username)
    dp.register_message_handler(write_group_message, state=WriteGroupState.waiting_message)

    dp.register_callback_query_handler(join_chat_start, Text(startswith="join_chat_"))
    dp.register_message_handler(join_chat_link, state=JoinChatState.waiting_link)

    dp.register_callback_query_handler(write_user_start, Text(startswith="write_user_"))
    dp.register_message_handler(write_user_identifier, state=WriteUserState.waiting_user_identifier)
    dp.register_message_handler(write_user_message, state=WriteUserState.waiting_message)

    dp.register_callback_query_handler(change_name_start, Text(startswith="change_name_"))
    dp.register_message_handler(change_name_first_name, state=ChangeNameState.waiting_first_name)
    dp.register_message_handler(change_name_last_name, state=ChangeNameState.waiting_last_name)

    dp.register_callback_query_handler(change_avatar_start, Text(startswith="change_avatar_"))
    dp.register_message_handler(change_avatar_photo, state=ChangeAvatarState.waiting_photo, content_types=['photo', 'document'])