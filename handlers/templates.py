from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import get_user_templates, add_template, get_template_by_id, update_template, delete_template, get_user
from keyboards.inline import templates_list_keyboard, template_actions_keyboard, back_to_main_keyboard

class TemplateState(StatesGroup):
    waiting_name = State()
    waiting_text = State()
    waiting_delay = State()
    waiting_edit_name = State()
    waiting_edit_text = State()
    waiting_edit_delay = State()

async def my_templates(callback: types.CallbackQuery):
    templates = await get_user_templates(callback.from_user.id)
    # ВСЕГДА показываем клавиатуру с кнопкой создания
    await callback.message.edit_text("📋 Ваши шаблоны:", reply_markup=templates_list_keyboard(templates))

async def create_template(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите название шаблона:")
    await TemplateState.waiting_name.set()
    await callback.answer()

async def process_template_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("📝 Введите текст сообщения для шаблона:")
    await TemplateState.waiting_text.set()

async def process_template_text(message: types.Message, state: FSMContext):
    await state.update_data(text=message.text)
    await message.answer("⏱ Введите задержку между сообщениями (в секундах, 0 - без задержки):")
    await TemplateState.waiting_delay.set()

async def process_template_delay(message: types.Message, state: FSMContext):
    try:
        delay = int(message.text)
    except ValueError:
        await message.answer("❌ Ошибка: введите число секунд.")
        return
    data = await state.get_data()
    user = await get_user(message.from_user.id)
    await add_template(user.id, data['name'], data['text'], delay)
    await message.answer("✅ Шаблон создан!", reply_markup=back_to_main_keyboard())
    await state.finish()

async def view_template(callback: types.CallbackQuery):
    template_id = int(callback.data.split("_")[1])
    template = await get_template_by_id(template_id, callback.from_user.id)
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return
    text = f"📝 *{template.name}*\n\n{template.text}\n\n⏱ Задержка: {template.delay} сек"
    await callback.message.edit_text(text, parse_mode="Markdown",
                                     reply_markup=template_actions_keyboard(template.id))

async def edit_template(callback: types.CallbackQuery, state: FSMContext):
    template_id = int(callback.data.split("_")[2])
    template = await get_template_by_id(template_id, callback.from_user.id)
    if not template:
        await callback.answer("❌ Шаблон не найден")
        return
    await state.update_data(template_id=template_id)
    await callback.message.answer("✏️ Введите новое название (или '-' чтобы оставить прежним):")
    await TemplateState.waiting_edit_name.set()

async def process_edit_name(message: types.Message, state: FSMContext):
    name = message.text if message.text != "-" else None
    await state.update_data(edit_name=name)
    await message.answer("✏️ Введите новый текст (или '-' для пропуска):")
    await TemplateState.waiting_edit_text.set()

async def process_edit_text(message: types.Message, state: FSMContext):
    text = message.text if message.text != "-" else None
    await state.update_data(edit_text=text)
    await message.answer("✏️ Введите новую задержку (или '-' для пропуска):")
    await TemplateState.waiting_edit_delay.set()

async def process_edit_delay(message: types.Message, state: FSMContext):
    delay_str = message.text
    delay = int(delay_str) if delay_str != "-" else None
    data = await state.get_data()
    template_id = data['template_id']
    template = await get_template_by_id(template_id, message.from_user.id)
    if template:
        new_name = data.get('edit_name') or template.name
        new_text = data.get('edit_text') or template.text
        new_delay = delay if delay is not None else template.delay
        await update_template(template_id, new_name, new_text, new_delay)
        await message.answer("✅ Шаблон обновлён!", reply_markup=back_to_main_keyboard())
    else:
        await message.answer("❌ Ошибка: шаблон не найден")
    await state.finish()

async def delete_template_handler(callback: types.CallbackQuery):
    template_id = int(callback.data.split("_")[2])
    await delete_template(template_id)
    await callback.message.edit_text("🗑 Шаблон удалён.", reply_markup=back_to_main_keyboard())
    await callback.answer()

def register_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(my_templates, text="my_templates")
    dp.register_callback_query_handler(create_template, text="create_template")
    dp.register_message_handler(process_template_name, state=TemplateState.waiting_name)
    dp.register_message_handler(process_template_text, state=TemplateState.waiting_text)
    dp.register_message_handler(process_template_delay, state=TemplateState.waiting_delay)
    dp.register_callback_query_handler(view_template, Text(startswith="template_"))
    dp.register_callback_query_handler(edit_template, Text(startswith="edit_template_"))
    dp.register_message_handler(process_edit_name, state=TemplateState.waiting_edit_name)
    dp.register_message_handler(process_edit_text, state=TemplateState.waiting_edit_text)
    dp.register_message_handler(process_edit_delay, state=TemplateState.waiting_edit_delay)
    dp.register_callback_query_handler(delete_template_handler, Text(startswith="delete_template_"))