import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from bot.services import table_manager
from bot.handlers.states import TableStates

start_router = Router()
logger = logging.getLogger(__name__)

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

# ... остальные обработчики (start_command, help_command) без изменений ...

@start_router.message(F.text == "❌ Удалить таблицу")
async def handle_delete_table_button(message: Message):
    """Обработчик кнопки удаления таблицы из Reply-меню"""
    user_id = message.from_user.id
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        await message.answer(
            "❌ У вас нет таблиц для удаления.",
            reply_markup=get_main_keyboard()
        )
        return
    
    message_text = "🗑️ **Выберите таблицу для удаления:**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message_text += f"{i}. **{table.original_name}**\n"
        message_text += f"   📅 {table.created_at} | 📊 {len(table.columns)} кол. | 📈 {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"❌ Удалить", callback_data=f"confirm_delete_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")])
    
    await message.answer(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

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
        f"📊 Данные: {len(table.columns)} колонок, {table.rows_count} строк\n\n"
        f"⚠️ Это действие нельзя отменить!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("delete_"))
async def handle_delete_table(callback: CallbackQuery):
    """Обработчик удаления таблицы"""
    await callback.answer()
    table_id = callback.data.replace("delete_", "")
    
    # Добавляем логирование для отладки
    logger.info(f"Попытка удаления таблицы: {table_id}")
    
    success = table_manager.delete_table(table_id)
    if success:
        await callback.message.edit_text(
            "✅ Таблица успешно удалена!",
            parse_mode='Markdown'
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении таблицы.\n\n"
            "💡 Таблица могла быть уже удалена или файл недоступен.",
            parse_mode='Markdown'
        )
