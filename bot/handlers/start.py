import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile  # ДОБАВЛЯЕМ ЭТОТ ИМПОРТ

from bot.services.table_manager import AdvancedTableManager
from bot.handlers.states import TableStates

start_router = Router()
table_manager = AdvancedTableManager()

@start_router.message(Command("start"))
async def start_command(message: Message):
    """Обработчик команды /start с инлайн-кнопками"""
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

@start_router.message(Command("help"))
async def help_command(message: Message):
    """Обработчик команды /help"""
    help_text = """
📊 **Table Manager Bot - Помощь**

**Основные команды:**
/start - Главное меню
/help - Эта справка

**Поддерживаемые форматы:**
• CSV (.csv) 
• JSON (.json)

**Функционал:**
• Сохранение таблиц с датой в названии
• Просмотр списка таблиц
• Удаление таблиц
"""
    await message.answer(help_text, parse_mode='Markdown')

@start_router.callback_query(F.data == "save_table")
async def handle_save_table(callback: CallbackQuery, state: FSMContext):
    """Обработчик сохранения таблицы"""
    await callback.answer()
    await callback.message.edit_text(
        "📥 **Сохранение таблицы**\n\n"
        "Пожалуйста, загрузите файл таблицы (CSV, JSON).\n"
        "Файл будет сохранен с датой в названии.",
        parse_mode='Markdown'
    )
    await state.set_state(TableStates.waiting_table_file)

@start_router.callback_query(F.data == "list_tables")
async def handle_list_tables(callback: CallbackQuery):
    """Обработчик просмотра таблиц"""
    await callback.answer()
    user_id = callback.from_user.id
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        await callback.message.edit_text(
            "📋 **Мои таблицы**\n\n"
            "У вас пока нет сохраненных таблиц.",
            parse_mode='Markdown'
        )
        return
    
    message = "📋 **Мои таблицы**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message += f"{i}. **{table.original_name}**\n"
        message += f"   📅 {table.created_at}\n"
        message += f"   📊 {len(table.columns)} кол., {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"👁️ {table.original_name}", callback_data=f"view_{table.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"delete_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    
    await callback.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("view_"))
async def handle_view_table(callback: CallbackQuery):
    """Обработчик просмотра деталей таблицы"""
    await callback.answer()
    table_id = callback.data.replace("view_", "")
    table = table_manager.get_table(table_id)
    
    if not table:
        await callback.message.edit_text("❌ Таблица не найдена.")
        return
    
    preview = table_manager.get_table_preview(table_id, 3)
    
    message = f"📊 **{table.original_name}**\n\n"
    message += f"📅 Дата: {table.created_at}\n"
    message += f"📊 Столбцы: {len(table.columns)}\n"
    message += f"📈 Строки: {table.rows_count}\n"
    message += f"💾 Размер: {table.file_size / 1024:.1f} KB\n\n"
    
    if preview:
        message += "**Превью:**\n```\n"
        message += preview + "\n```\n\n"
    
    message += "**Столбцы:** " + ", ".join(table.columns)
    
    keyboard = [
        [InlineKeyboardButton(text="📤 Скачать", callback_data=f"download_{table.id}"),
         InlineKeyboardButton(text="❌ Удалить", callback_data=f"confirm_delete_{table.id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="list_tables")]
    ]
    
    await callback.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("download_"))
async def handle_download_table(callback: CallbackQuery):
    """Обработчик скачивания таблицы"""
    await callback.answer()
    table_id = callback.data.replace("download_", "")
    table = table_manager.get_table(table_id)
    
    if not table or not os.path.exists(table.file_path):
        await callback.message.answer("❌ Файл таблицы не найден.")
        return
    
    try:
        file = FSInputFile(table.file_path, filename=table.original_name)
        await callback.message.answer_document(
            document=file,
            caption=f"📊 {table.original_name}\n📅 {table.created_at}"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при скачивании: {e}")

@start_router.callback_query(F.data.startswith("confirm_delete_"))
async def handle_confirm_delete(callback: CallbackQuery):
    """Обработчик подтверждения удаления"""
    await callback.answer()
    table_id = callback.data.replace("confirm_delete_", "")
    table = table_manager.get_table(table_id)
    
    if not table:
        await callback.message.edit_text("❌ Таблица не найдена.")
        return
    
    keyboard = [
        [InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_{table.id}")],
        [InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"view_{table.id}")]
    ]
    
    await callback.message.edit_text(
        f"❌ **Подтверждение удаления**\n\n"
        f"Вы уверены, что хотите удалить таблицу:\n"
        f"**{table.original_name}**?\n\n"
        f"📅 Дата: {table.created_at}\n"
        f"📊 Данные: {len(table.columns)} колонок, {table.rows_count} строк",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("delete_"))
async def handle_delete_table(callback: CallbackQuery):
    """Обработчик удаления таблицы"""
    await callback.answer()
    table_id = callback.data.replace("delete_", "")
    
    success = table_manager.delete_table(table_id)
    if success:
        await callback.message.edit_text(
            "✅ Таблица успешно удалена!",
            parse_mode='Markdown'
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении таблицы.",
            parse_mode='Markdown'
        )

@start_router.callback_query(F.data == "back_main")
async def handle_back_main(callback: CallbackQuery):
    """Обработчик возврата в главное меню"""
    await callback.answer()
    keyboard = [
        [InlineKeyboardButton(text="📥 Сохранить таблицу", callback_data="save_table")],
        [InlineKeyboardButton(text="📋 Мои таблицы", callback_data="list_tables")],
        [InlineKeyboardButton(text="🔄 Обновить таблицу", callback_data="update_table")],
        [InlineKeyboardButton(text="❌ Удалить таблицу", callback_data="delete_table")],
        [InlineKeyboardButton(text="📤 Экспорт таблицы", callback_data="export_table")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await callback.message.edit_text(
        "📊 **Table Manager Bot**\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Обработчики временно заглушенных функций
@start_router.callback_query(F.data == "update_table")
async def handle_update_table(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "🔄 **Обновление таблиц**\n\n"
        "Эта функция временно недоступна.\n"
        "Используйте сохранение новой таблицы.",
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data == "export_table")
async def handle_export_table(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "📤 **Экспорт таблиц**\n\n"
        "Эта функция временно недоступна.\n"
        "Вы можете скачать оригинальный файл таблицы.",
        parse_mode='Markdown'
    )
