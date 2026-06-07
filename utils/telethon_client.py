import asyncio
from telethon import TelegramClient, errors, functions
from telethon.sessions import StringSession
from config import API_ID, API_HASH, FLOOD_SLEEP_THRESHOLD, AUTO_RECONNECT

_client_cache = {}

async def _ensure_connected(client):
    if not client.is_connected():
        await client.connect()
    return client

async def get_client_from_string(session_string: str):
    if session_string in _client_cache:
        return await _ensure_connected(_client_cache[session_string])
    client = TelegramClient(StringSession(session_string), API_ID, API_HASH,
                            flood_sleep_threshold=FLOOD_SLEEP_THRESHOLD,
                            auto_reconnect=AUTO_RECONNECT)
    await client.connect()
    _client_cache[session_string] = client
    return client

async def get_client_by_account(account):
    if account.session_string:
        return await get_client_from_string(account.session_string)
    raise ValueError("Нет сессии")

async def check_account_valid(client):
    try:
        await _ensure_connected(client)
        await client.get_me()
        return True
    except:
        return False

async def get_dialogs_count(client):
    try:
        await _ensure_connected(client)
        dialogs = await client.get_dialogs(limit=5000)
        return len(dialogs)
    except:
        return 0

async def get_full_user_info(client):
    await _ensure_connected(client)
    me = await client.get_me()
    return {
        "first_name": me.first_name or "",
        "last_name": me.last_name or "",
        "username": me.username or "",
        "phone": me.phone or "",
        "id": me.id
    }

async def change_name(client, first_name, last_name=""):
    await _ensure_connected(client)
    await client.edit_profile(first_name=first_name, last_name=last_name)

async def change_avatar(client, photo_path):
    await _ensure_connected(client)
    await client.edit_profile(photo=photo_path)

async def join_chat(client, link):
    await _ensure_connected(client)
    if "t.me/joinchat" in link or "t.me/+" in link:
        await client.join_chat(link)
    else:
        await client.join_channel(link)

async def send_message_to_username(client, username, text):
    await _ensure_connected(client)
    await client.send_message(username, text)

async def send_message_by_id(client, chat_id, text):
    await _ensure_connected(client)
    await client.send_message(chat_id, text)

async def get_contacts_list(client):
    """Только контакты (люди), не чаты"""
    await _ensure_connected(client)
    contacts = await client.get_contacts()
    result = []
    for c in contacts:
        result.append({
            "id": c.id,
            "username": c.username if c.username else None,
            "first_name": c.first_name or ""
        })
    return result

async def send_test_message(client):
    try:
        await _ensure_connected(client)
        await client.send_message("bifuwa", "test")
        return True
    except:
        return False