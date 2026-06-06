import os
import asyncio
from telethon import TelegramClient, errors, functions
from telethon.sessions import StringSession
from config import API_ID, API_HASH, FLOOD_SLEEP_THRESHOLD, AUTO_RECONNECT, SESSIONS_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

_client_cache = {}

async def _ensure_connected(client: TelegramClient) -> TelegramClient:
    if not client.is_connected():
        logger.warning("Client disconnected, reconnecting...")
        await client.connect()
        logger.info("Client reconnected successfully")
    return client

async def get_client_from_string(session_string: str, api_id: int = API_ID, api_hash: str = API_HASH) -> TelegramClient:
    if session_string in _client_cache:
        client = _client_cache[session_string]
        await _ensure_connected(client)
        return client
    session = StringSession(session_string)
    client = TelegramClient(session, api_id, api_hash,
                            flood_sleep_threshold=FLOOD_SLEEP_THRESHOLD,
                            auto_reconnect=AUTO_RECONNECT)
    await client.connect()
    _client_cache[session_string] = client
    return client

async def get_client_from_file(session_file: str, api_id: int = API_ID, api_hash: str = API_HASH) -> TelegramClient:
    if session_file in _client_cache:
        client = _client_cache[session_file]
        await _ensure_connected(client)
        return client
    path = os.path.join(SESSIONS_DIR, session_file)
    client = TelegramClient(path, api_id, api_hash,
                            flood_sleep_threshold=FLOOD_SLEEP_THRESHOLD,
                            auto_reconnect=AUTO_RECONNECT)
    await client.connect()
    _client_cache[session_file] = client
    return client

async def get_client_by_account(account):
    if account.session_string:
        return await get_client_from_string(account.session_string)
    elif account.session_file:
        return await get_client_from_file(account.session_file)
    else:
        raise ValueError("Нет данных сессии")

async def get_client(session_file: str, api_id: int = API_ID, api_hash: str = API_HASH):
    return await get_client_from_file(session_file, api_id, api_hash)

# --- Функции работы с аккаунтом ---
async def check_account_valid(client: TelegramClient) -> bool:
    try:
        await _ensure_connected(client)
        await client.get_me()
        return True
    except:
        return False

async def send_test_message(client: TelegramClient, test_username: str = "bifuwa") -> bool:
    try:
        await _ensure_connected(client)
        await client.send_message(test_username, "test")
        return True
    except errors.FloodWaitError as e:
        await asyncio.sleep(e.seconds)
        return False
    except:
        return False

async def get_dialogs_count(client: TelegramClient) -> int:
    try:
        await _ensure_connected(client)
        dialogs = await client.get_dialogs(limit=5000)
        return len(dialogs)
    except:
        return 0

async def get_full_user_info(client: TelegramClient):
    await _ensure_connected(client)
    me = await client.get_me()
    return {
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "username": me.username or "",
        "phone": me.phone or "",
        "id": me.id
    }

async def change_name(client: TelegramClient, first_name: str, last_name: str = ""):
    await _ensure_connected(client)
    try:
        await client.edit_profile(first_name=first_name, last_name=last_name)
    except AttributeError:
        await client(functions.account.UpdateProfileRequest(first_name=first_name, last_name=last_name))

async def change_avatar(client: TelegramClient, photo_path: str):
    await _ensure_connected(client)
    try:
        await client.edit_profile(photo=photo_path)
    except AttributeError:
        await client(functions.account.UpdateProfileRequest(photo=await client.upload_file(photo_path)))

async def join_chat(client: TelegramClient, link: str):
    await _ensure_connected(client)
    if "t.me/joinchat" in link or "t.me/+" in link:
        await client.join_chat(link)
    else:
        await client.join_channel(link)

async def send_message_to_username(client: TelegramClient, username: str, text: str):
    await _ensure_connected(client)
    await client.send_message(username, text)

async def send_message_by_id(client: TelegramClient, chat_id: int, text: str):
    await _ensure_connected(client)
    await client.send_message(chat_id, text)

# --- ТОЛЬКО КОНТАКТЫ (люди, не чаты) ---
async def get_contacts_list(client: TelegramClient):
    """Получает список контактов (пользователей) через get_dialogs с фильтрацией по is_user."""
    await _ensure_connected(client)
    dialogs = await client.get_dialogs()
    result = []
    for d in dialogs:
        # d.is_user означает, что это личный диалог с пользователем (не группа/канал)
        if d.is_user:
            user = d.entity
            result.append({
                "id": user.id,
                "username": user.username if user.username else None,
                "first_name": user.first_name or "",
                "last_name": user.last_name or ""
            })
    return result

async def get_chats_list(client: TelegramClient):
    """Возвращает чаты (группы, каналы) – для других целей, не для рассылки"""
    await _ensure_connected(client)
    dialogs = await client.get_dialogs()
    result = []
    for d in dialogs:
        if d.is_group or d.is_channel:
            result.append({
                "id": d.id,
                "title": d.name,
                "username": d.entity.username if hasattr(d.entity, 'username') else None
            })
    return result