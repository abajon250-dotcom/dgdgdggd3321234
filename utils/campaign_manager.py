import asyncio
import datetime
import json
from aiogram import Bot
from config import BOT_TOKEN
from database import get_campaign_by_id, update_campaign_status, update_campaign_sent_count, update_campaign_errors_log, get_user
from utils.telethon_client import get_client_by_account, send_message_by_id, send_message_to_username
from utils.logger import get_logger

logger = get_logger(__name__)
bot = Bot(token=BOT_TOKEN)

active_tasks = {}
pause_events = {}
last_notify = {}

async def run_campaign(campaign_id: int, tg_user_id: int):
    campaign = await get_campaign_by_id(campaign_id, tg_user_id)
    if not campaign or campaign.status != 'running':
        return
    account = campaign.account
    if not account.is_active:
        await update_campaign_status(campaign_id, 'cancelled')
        await bot.send_message(tg_user_id, f"❌ Рассылка #{campaign_id} отменена: аккаунт неактивен.")
        return

    client = await get_client_by_account(account)
    recipients = json.loads(campaign.recipients_json)
    text = campaign.custom_text
    if not text and campaign.template:
        text = campaign.template.text
    delay = campaign.delay
    sent = campaign.sent_count
    errors = json.loads(campaign.errors_log) if campaign.errors_log else []

    pause_event = asyncio.Event()
    pause_event.set()
    pause_events[campaign_id] = pause_event
    last_notify[campaign_id] = sent

    for idx, recipient in enumerate(recipients[sent:], start=sent):
        if campaign.status == 'cancelled':
            break
        await pause_event.wait()

        rec_type = recipient.get('type')
        identifier = recipient.get('identifier')
        try:
            if rec_type == 'username':
                await send_message_to_username(client, identifier, text)
            elif rec_type == 'user_id':
                await send_message_by_id(client, int(identifier), text)
            else:
                await send_message_by_id(client, int(identifier), text)  # fallback
            sent += 1
            await update_campaign_sent_count(campaign_id, sent, datetime.datetime.utcnow())

            # Отправляем уведомление о прогрессе каждые 10 отправленных сообщений
            if sent - last_notify[campaign_id] >= 10:
                last_notify[campaign_id] = sent
                await bot.send_message(tg_user_id, f"📊 Прогресс рассылки #{campaign.id}: отправлено {sent} из {campaign.total_recipients}")

        except Exception as e:
            logger.error(f"Ошибка при отправке {identifier}: {e}")
            errors.append({"recipient": identifier, "error": str(e), "time": str(datetime.datetime.utcnow())})
            await update_campaign_errors_log(campaign_id, errors)

        await asyncio.sleep(delay)


    if campaign.status != 'cancelled':
        await update_campaign_status(campaign_id, 'finished')
        await send_gif(await bot.get_chat(tg_user_id), "campaign_finished",
                       f"✅ Рассылка #{campaign_id} завершена. Отправлено {sent} из {campaign.total_recipients}")
    active_tasks.pop(campaign_id, None)
    pause_events.pop(campaign_id, None)
    last_notify.pop(campaign_id, None)

async def start_campaign(campaign_id: int, tg_user_id: int):
    campaign = await get_campaign_by_id(campaign_id, tg_user_id)
    if not campaign or campaign.status != 'pending':
        return False
    for cid, task in active_tasks.items():
        camp = await get_campaign_by_id(cid, tg_user_id)
        if camp and camp.account_id == campaign.account_id:
            return False
    await update_campaign_status(campaign_id, 'running')
    await update_campaign_sent_count(campaign_id, 0, datetime.datetime.utcnow())
    task = asyncio.create_task(run_campaign(campaign_id, tg_user_id))
    active_tasks[campaign_id] = task
    return True

async def pause_campaign(campaign_id: int, tg_user_id: int):
    if campaign_id in pause_events:
        pause_events[campaign_id].clear()
        await update_campaign_status(campaign_id, 'paused')
        return True
    return False

async def resume_campaign(campaign_id: int, tg_user_id: int):
    if campaign_id in pause_events:
        pause_events[campaign_id].set()
        await update_campaign_status(campaign_id, 'running')
        return True
    return False

async def cancel_campaign(campaign_id: int, tg_user_id: int):
    if campaign_id in active_tasks:
        await update_campaign_status(campaign_id, 'cancelled')
        active_tasks[campaign_id].cancel()
        active_tasks.pop(campaign_id, None)
        pause_events.pop(campaign_id, None)
        last_notify.pop(campaign_id, None)
    else:
        await update_campaign_status(campaign_id, 'cancelled')
    return True