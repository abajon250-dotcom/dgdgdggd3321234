import asyncio
import datetime
import json
from aiogram import Bot
from config import BOT_TOKEN
from database import get_campaign_by_id, update_campaign_status, update_campaign_sent_count, update_campaign_errors_log
from utils.telethon_client import get_client_by_account, send_message_to_username, send_message_by_id

bot = Bot(token=BOT_TOKEN)
active_tasks = {}
pause_events = {}

async def run_campaign(campaign_id, user_id):
    campaign = await get_campaign_by_id(campaign_id, user_id)
    if not campaign or campaign.status != 'running':
        return
    account = campaign.account
    if not account.is_active:
        await update_campaign_status(campaign_id, 'cancelled')
        await bot.send_message(user_id, f"❌ Рассылка #{campaign_id} отменена: аккаунт неактивен.")
        return
    client = await get_client_by_account(account)
    recipients = json.loads(campaign.recipients_json)
    text = campaign.custom_text
    if not text and campaign.template:
        text = campaign.template.text
    delay = campaign.delay if campaign.delay >= 3 else 3
    sent = campaign.sent_count
    errors = json.loads(campaign.errors_log) if campaign.errors_log else []
    pause_event = asyncio.Event()
    pause_event.set()
    pause_events[campaign_id] = pause_event

    for idx, rec in enumerate(recipients[sent:], start=sent):
        if campaign.status != 'running':
            break
        await pause_event.wait()
        try:
            if rec['type'] == 'username':
                await send_message_to_username(client, rec['identifier'], text)
            else:
                await send_message_by_id(client, int(rec['identifier']), text)
            sent += 1
            await update_campaign_sent_count(campaign_id, sent, datetime.datetime.utcnow())
            if sent % 10 == 0:
                await bot.send_message(user_id, f"📊 Прогресс: {sent}/{campaign.total_recipients}")
        except Exception as e:
            errors.append({"recipient": rec['identifier'], "error": str(e)})
            await update_campaign_errors_log(campaign_id, errors)
        await asyncio.sleep(delay)

    if campaign.status == 'running':
        await update_campaign_status(campaign_id, 'finished')
        await bot.send_message(user_id, f"✅ Рассылка #{campaign_id} завершена. Отправлено {sent} из {campaign.total_recipients}")
    active_tasks.pop(campaign_id, None)
    pause_events.pop(campaign_id, None)

async def start_campaign(campaign_id, user_id):
    campaign = await get_campaign_by_id(campaign_id, user_id)
    if not campaign or campaign.status != 'pending':
        return False
    for cid in active_tasks:
        camp = await get_campaign_by_id(cid, user_id)
        if camp and camp.account_id == campaign.account_id:
            return False
    await update_campaign_status(campaign_id, 'running')
    task = asyncio.create_task(run_campaign(campaign_id, user_id))
    active_tasks[campaign_id] = task
    return True

async def pause_campaign(campaign_id, user_id):
    if campaign_id in pause_events:
        pause_events[campaign_id].clear()
        await update_campaign_status(campaign_id, 'paused')
        return True
    return False

async def resume_campaign(campaign_id, user_id):
    if campaign_id in pause_events:
        pause_events[campaign_id].set()
        await update_campaign_status(campaign_id, 'running')
        return True
    return False

async def cancel_campaign(campaign_id, user_id):
    if campaign_id in active_tasks:
        await update_campaign_status(campaign_id, 'cancelled')
        active_tasks[campaign_id].cancel()
        active_tasks.pop(campaign_id, None)
        pause_events.pop(campaign_id, None)
    else:
        await update_campaign_status(campaign_id, 'cancelled')
    return True