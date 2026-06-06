from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📱 Мои аккаунты", callback_data="my_accounts"),
        InlineKeyboardButton("📝 Шаблоны", callback_data="my_templates"),
        InlineKeyboardButton("🚀 Рассылки", callback_data="my_campaigns"),
        InlineKeyboardButton("💳 Подписка", callback_data="subscription_info"),
        InlineKeyboardButton("➕ Добавить аккаунт", callback_data="add_account_choice")
    )
    return kb

def back_to_main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ В главное меню", callback_data="main_menu"))
    return kb

def subscription_plans_keyboard():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("1 день - 0.5 USD", callback_data="buy_plan:1day"),
        InlineKeyboardButton("7 дней - 3 USD", callback_data="buy_plan:7days"),
        InlineKeyboardButton("30 дней - 12 USD", callback_data="buy_plan:30days"),
        InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
    )
    return kb

def accounts_list_keyboard(accounts):
    kb = InlineKeyboardMarkup(row_width=1)
    for acc in accounts:
        status = "✅" if acc.is_active else "❌"
        spam = "🚫" if acc.spam_block else ""
        kb.add(InlineKeyboardButton(f"{status} {acc.phone} {spam}", callback_data=f"account_{acc.id}"))
    kb.add(InlineKeyboardButton("➕ Добавить аккаунт", callback_data="add_account_choice"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def account_actions_keyboard(account_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔄 Проверить валидность", callback_data=f"check_valid_{account_id}"),
        InlineKeyboardButton("🗑 Удалить аккаунт", callback_data=f"delete_account_{account_id}"),
        InlineKeyboardButton("✏️ Сменить имя", callback_data=f"change_name_{account_id}"),
        InlineKeyboardButton("🖼 Сменить аватар", callback_data=f"change_avatar_{account_id}"),
        InlineKeyboardButton("💬 Написать в группу", callback_data=f"write_group_{account_id}"),
        InlineKeyboardButton("➕ Вступить в группу/канал", callback_data=f"join_chat_{account_id}"),
        InlineKeyboardButton("👤 Написать пользователю", callback_data=f"write_user_{account_id}"),
        InlineKeyboardButton("◀️ Назад", callback_data="my_accounts")
    )
    return kb

def templates_list_keyboard(templates):
    kb = InlineKeyboardMarkup(row_width=1)
    for tpl in templates:
        kb.add(InlineKeyboardButton(f"📄 {tpl.name}", callback_data=f"template_{tpl.id}"))
    kb.add(InlineKeyboardButton("➕ СОЗДАТЬ ШАБЛОН", callback_data="create_template"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def template_actions_keyboard(template_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit_template_{template_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_template_{template_id}"),
        InlineKeyboardButton("◀️ Назад", callback_data="my_templates")
    )
    return kb

def campaigns_list_keyboard(campaigns):
    kb = InlineKeyboardMarkup(row_width=1)
    for camp in campaigns:
        status_emoji = {"pending":"⏳", "running":"▶️", "paused":"⏸", "cancelled":"❌", "finished":"✅"}.get(camp.status, "❓")
        kb.add(InlineKeyboardButton(f"{status_emoji} {camp.name or camp.id} ({camp.status})", callback_data=f"campaign_{camp.id}"))
    kb.add(InlineKeyboardButton("➕ СОЗДАТЬ РАССЫЛКУ", callback_data="create_campaign"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def campaign_control_keyboard(campaign_id, status):
    kb = InlineKeyboardMarkup(row_width=2)
    if status == "running":
        kb.add(
            InlineKeyboardButton("⏸ Пауза", callback_data=f"pause_campaign_{campaign_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}"),
            InlineKeyboardButton("🔄 Статус", callback_data=f"status_campaign_{campaign_id}")
        )
    elif status == "paused":
        kb.add(
            InlineKeyboardButton("▶️ Возобновить", callback_data=f"resume_campaign_{campaign_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}"),
            InlineKeyboardButton("🔄 Статус", callback_data=f"status_campaign_{campaign_id}")
        )
    elif status == "pending":
        kb.add(
            InlineKeyboardButton("🚀 Запустить", callback_data=f"start_campaign_{campaign_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}")
        )
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="my_campaigns"))
    return kb

def admin_panel_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton("💰 Платежи", callback_data="admin_payments"),
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📢 Рассылки", callback_data="admin_campaigns"),
        InlineKeyboardButton("🎁 Промокоды", callback_data="admin_promos"),
        InlineKeyboardButton("🔒 Блокировка", callback_data="admin_ban_menu"),
        InlineKeyboardButton("📅 Выдать подписку", callback_data="admin_give_sub"),
        InlineKeyboardButton("📢 Массовая рассылка", callback_data="admin_broadcast"),  # <-- новая кнопка
        InlineKeyboardButton("◀️ Назад", callback_data="main_menu")
    )
    return kb

def admin_ban_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔒 Заблокировать", callback_data="admin_ban_user"),
        InlineKeyboardButton("🔓 Разблокировать", callback_data="admin_unban_user"),
        InlineKeyboardButton("◀️ Назад", callback_data="admin_panel")
    )
    return kb