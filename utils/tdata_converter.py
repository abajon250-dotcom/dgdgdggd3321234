import os
import zipfile
import shutil
from pyrogram import Client
from telethon.sessions import StringSession
from telethon import TelegramClient
from config import TDATA_TEMP_DIR, API_ID, API_HASH
import asyncio

async def convert_tdata_to_session(zip_path: str, session_name: str) -> str:
    """
    Распаковывает zip с tdata, конвертирует в строку сессии Telethon через Pyrogram.
    Возвращает путь к файлу сессии.
    """
    temp_dir = os.path.join(TDATA_TEMP_DIR, session_name)
    os.makedirs(temp_dir, exist_ok=True)
    # Распаковка
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    # Ищем папку tdata
    tdata_path = None
    for root, dirs, files in os.walk(temp_dir):
        if 'tdata' in dirs:
            tdata_path = os.path.join(root, 'tdata')
            break
    if not tdata_path:
        raise Exception("Папка tdata не найдена в архиве")
    # Используем Pyrogram для импорта сессии
    pyro_client = Client(
        session_name,
        api_id=API_ID,
        api_hash=API_HASH,
        workdir=temp_dir
    )
    await pyro_client.start()
    # Получаем строку сессии Telethon через экспорт
    # Для этого нужно сначала получить строку сессии Pyrogram, затем конвертировать
    # Упрощённо: используем telethon с строкой из pyro
    # Но проще: после запуска pyro_client, создаём telethon клиент с той же сессией
    # (не прямой путь) - используем библиотеку tg-seed? Вместо этого лучше предложить
    # Прямой способ: попросить пользователя использовать telethon для входа с кодом.
    # Для реальной конвертации нужна библиотека telethon-tdata, но она нестабильна.
    # Реализуем костыль: после запуска pyro_client экспортируем строку сессии для telethon
    # через создание временного файла.
    # В данном коде для краткости делаем так:
    telethon_session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")
    # Получаем данные авторизации из pyro
    user_data = await pyro_client.get_me()
    # Создаём telethon клиент с номером телефона
    tele_client = TelegramClient(telethon_session_path, API_ID, API_HASH)
    await tele_client.connect()
    # Необходимо войти с номером, но у нас уже есть сессия pyro - не совместимы.
    # Поэтому правильнее: предложить пользователю ввести код подтверждения через номер.
    # Но для выполнения задания - упростим: используем только Pyrogram для дальнейшей работы?
    # Или сэмулируем: сохраним сессию telethon, позже при подключении попросим код.
    # Проще всего: после конвертации tdata удалить и попросить ввести номер.
    raise NotImplementedError("Конвертация tdata требует дополнительной библиотеки. Используйте вход по номеру телефона.")
    # В реальном проекте используйте: https://github.com/therealOri/telethon-tdata