import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

# Используем единый менеджер
from bot.services import table_manager
from bot.handlers.states import TableStates

start_router = Router()

def get_main_keyboard():
    """Клавиатура основного меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Сохранить таблицу"), KeyboardButton(text="📋 Мои таблицы")],
            [KeyboardButton(text="🔄 Обновить таблицу"), KeyboardButton(text="❌ Удалить таблицу")],
            [KeyboardButton(text="📤 Экспорт таблицы"), KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True,
        persistent=True
    )

@start_router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start с инлайн-кнопками и постоянным меню"""
    keyboard = [
        [InlineKeyboardButton(text="📥 Сохранить таблицу", callback_data="save_table")],
        [InlineKeyboardButton(text="📋 Мои таблицы", callback_data="list_tables")],
        [InlineKeyboardButton(text="🔄 Обновить таблицу", callback_data="update_table")],
        [InlineKeyboardButton(text="❌ Удалить таблицу", callback_data="delete_table")],
        [InlineKeyboardButton(text="📤 Экспорт таблицы", callback_data="export_table")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(
        "📊 **Table Manager Bot**\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Отправляем постоянное меню отдельным сообщением
    await message.answer(
        "👇 Или используйте меню внизу экрана:",
        reply_markup=get_main_keyboard()
    )

@start_router.message(F.text == "ℹ️ Помощь")
@start_router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help и кнопки помощи"""
    help_text = """
📊 **Table Manager Bot - Помощь**

**Основные команды:**
/start - Главное меню
/help - Эта справка

**Поддерживаемые форматы:**
• CSV (.csv)
• JSON (.json) 
• Excel (.xlsx, .xls)

**Функционал:**
• Сохранение таблиц с датой в названии
• Просмотр списка таблиц
• Удаление таблиц
• Скачивание оригинальных файлов
"""
    await message.answer(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@start_router.message(F.text == "📥 Сохранить таблицу")
async def handle_save_table_button(message: Message, state: FSMContext):
    """Обработчик кнопки сохранения таблицы"""
    await message.answer(
        "📥 **Сохранение таблицы**\n\n"
        "Пожалуйста, загрузите файл таблицы (CSV, JSON, Excel).\n"
        "Файл будет сохранен с датой в названии.\n\n"
        "📁 **Поддерживаемые форматы:**\n"
        "• CSV (.csv)\n"
        "• JSON (.json)\n"
        "• Excel (.xlsx, .xls)",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
    await state.set_state(TableStates.waiting_table_file)

@start_router.message(F.text == "📋 Мои таблицы")
async def handle_list_tables_button(message: Message):
    """Обработчик кнопки просмотра таблиц"""
    await handle_list_tables_internal(message)

async def handle_list_tables_internal(message: Message):
    """Внутренняя функция для просмотра таблиц"""
    user_id = message.from_user.id
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        await message.answer(
            "📋 **Мои таблицы**\n\n"
            "У вас пока нет сохраненных таблиц.\n\n"
            "💡 Нажмите «📥 Сохранить таблицу», чтобы добавить первую таблицу.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )
        return
    
    message_text = "📋 **Мои таблицы**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message_text += f"{i}. **{table.original_name}**\n"
        message_text += f"   📅 {table.created_at} | 📊 {len(table.columns)} кол. | 📈 {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"👁️ {table.original_name[:15]}...", callback_data=f"view_{table.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"confirm_delete_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")])
    
    await message.answer(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

# ... остальные обработчики callback_query остаются без изменений ...
# (handle_save_table, handle_list_tables, handle_view_table, handle_download_table, 
#  handle_confirm_delete, handle_delete_table, handle_back_main, handle_update_table, handle_export_table)

@start_router.callback_query(F.data == "list_tables")
async def handle_list_tables(callback: CallbackQuery):
    """Обработчик просмотра таблиц"""
    await callback.answer()
    user_id = callback.from_user.id
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        await callback.message.edit_text(
            "📋 **Мои таблицы**\n\n"
            "У вас пока нет сохраненных таблиц.\n\n"
            "💡 Нажмите «📥 Сохранить таблицу», чтобы добавить первую таблицу.",
            parse_mode='Markdown'
        )
        return
    
    message = "📋 **Мои таблицы**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message += f"{i}. **{table.original_name}**\n"
        message += f"   📅 {table.created_at} | 📊 {len(table.columns)} кол. | 📈 {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"👁️ {table.original_name[:15]}...", callback_data=f"view_{table.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"confirm_delete_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")])
    
    await callback.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

# ... остальные callback обработчики без изменений ...
