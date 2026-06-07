from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📱 Аккаунты", callback_data="my_accounts"),
        InlineKeyboardButton("📝 Шаблоны", callback_data="my_templates"),
        InlineKeyboardButton("🚀 Рассылки", callback_data="my_campaigns"),
        InlineKeyboardButton("💳 Подписка", callback_data="subscription_info"),
        InlineKeyboardButton("➕ Добавить", callback_data="add_account_choice")
    )
    return kb

def back_to_main_keyboard():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("◀️ Главное меню", callback_data="main_menu"))
    return kb

def accounts_list_keyboard(accounts):
    kb = InlineKeyboardMarkup(row_width=1)
    for a in accounts:
        kb.add(InlineKeyboardButton(f"{'✅' if a.is_active else '❌'} {a.phone}", callback_data=f"account_{a.id}"))
    kb.add(InlineKeyboardButton("➕ Добавить", callback_data="add_account_choice"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def account_actions_keyboard(account_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🔄 Проверить", callback_data=f"check_valid_{account_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_account_{account_id}"),
        InlineKeyboardButton("✏️ Имя", callback_data=f"change_name_{account_id}"),
        InlineKeyboardButton("🖼 Аватар", callback_data=f"change_avatar_{account_id}"),
        InlineKeyboardButton("💬 В группу", callback_data=f"write_group_{account_id}"),
        InlineKeyboardButton("➕ Вступить", callback_data=f"join_chat_{account_id}"),
        InlineKeyboardButton("👤 Написать", callback_data=f"write_user_{account_id}"),
        InlineKeyboardButton("◀️ Назад", callback_data="my_accounts")
    )
    return kb

def templates_list_keyboard(templates):
    kb = InlineKeyboardMarkup(row_width=1)
    for t in templates:
        kb.add(InlineKeyboardButton(f"📄 {t.name}", callback_data=f"template_{t.id}"))
    kb.add(InlineKeyboardButton("➕ Создать", callback_data="create_template"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def template_actions_keyboard(template_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✏️ Ред.", callback_data=f"edit_template_{template_id}"),
        InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_template_{template_id}"),
        InlineKeyboardButton("◀️ Назад", callback_data="my_templates")
    )
    return kb

def campaigns_list_keyboard(campaigns):
    kb = InlineKeyboardMarkup(row_width=1)
    for c in campaigns:
        emoji = {"pending":"⏳","running":"▶️","paused":"⏸","finished":"✅","cancelled":"❌"}.get(c.status,"❓")
        kb.add(InlineKeyboardButton(f"{emoji} {c.name or c.id}", callback_data=f"campaign_{c.id}"))
    kb.add(InlineKeyboardButton("➕ Создать", callback_data="create_campaign"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="main_menu"))
    return kb

def campaign_control_keyboard(campaign_id, status):
    kb = InlineKeyboardMarkup(row_width=2)
    if status == "running":
        kb.add(InlineKeyboardButton("⏸ Пауза", callback_data=f"pause_campaign_{campaign_id}"))
        kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}"))
    elif status == "paused":
        kb.add(InlineKeyboardButton("▶️ Возобновить", callback_data=f"resume_campaign_{campaign_id}"))
        kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}"))
    elif status == "pending":
        kb.add(InlineKeyboardButton("🚀 Запустить", callback_data=f"start_campaign_{campaign_id}"))
        kb.add(InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_campaign_{campaign_id}"))
    kb.add(InlineKeyboardButton("🔄 Статус", callback_data=f"status_campaign_{campaign_id}"))
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
        InlineKeyboardButton("📢 Массовая рассылка", callback_data="admin_broadcast"),
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