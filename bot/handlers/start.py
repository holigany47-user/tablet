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
• Обновление существующих таблиц
• Удаление таблиц
• Экспорт в разные форматы
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

@start_router.callback_query(F.data == "save_table")
async def handle_save_table(callback: CallbackQuery, state: FSMContext):
    """Обработчик сохранения таблицы"""
    await callback.answer()
    await callback.message.edit_text(
        "📥 **Сохранение таблицы**\n\n"
        "Пожалуйста, загрузите файл таблицы (CSV, JSON, Excel).\n"
        "Файл будет сохранен с датой в названии.\n\n"
        "📁 **Поддерживаемые форматы:**\n"
        "• CSV (.csv)\n"
        "• JSON (.json)\n"
        "• Excel (.xlsx, .xls)",
        parse_mode='Markdown'
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

@start_router.callback_query(F.data.startswith("view_"))
async def handle_view_table(callback: CallbackQuery):
    """Обработчик просмотра деталей таблицы"""
    await callback.answer()
    table_id = callback.data.replace("view_", "")
    table = table_manager.get_table(table_id)
    
    if not table:
        await callback.message.edit_text("❌ Таблица не найдена.")
        return
    
    preview_df = table_manager.get_table_preview(table_id, 3)
    
    message = f"📊 **{table.original_name}**\n\n"
    message += f"📅 Дата сохранения: {table.created_at}\n"
    message += f"📊 Столбцы: {len(table.columns)}\n"
    message += f"📈 Строки: {table.rows_count}\n"
    message += f"💾 Размер: {table.file_size / 1024:.1f} KB\n\n"
    
    if preview_df is not None and not preview_df.empty:
        message += "**Превью данных:**\n"
        message += "```\n"
        # Форматируем превью для лучшего отображения
        preview_text = preview_df.to_string(index=False, max_cols=4, max_rows=3)
        if len(preview_text) > 500:
            preview_text = preview_text[:500] + "..."
        message += preview_text + "\n```\n\n"
    else:
        message += "**Превью недоступно**\n\n"
    
    message += f"**Столбцы ({len(table.columns)}):**\n"
    # Показываем до 10 столбцов, остальные через "..."
    if len(table.columns) <= 10:
        message += ", ".join(table.columns)
    else:
        message += ", ".join(table.columns[:10]) + f"... (+{len(table.columns) - 10} еще)"
    
    keyboard = [
        [InlineKeyboardButton(text="📤 Скачать оригинал", callback_data=f"download_{table.id}")],
        [InlineKeyboardButton(text="🔄 Обновить таблицу", callback_data=f"select_update_{table.id}")],
        [InlineKeyboardButton(text="❌ Удалить таблицу", callback_data=f"confirm_delete_{table.id}")],
        [InlineKeyboardButton(text="🔙 К списку таблиц", callback_data="list_tables")]
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
        await callback.answer("✅ Файл отправлен")
    except Exception as e:
        await callback.message.answer(f"❌ Ошибка при скачивании: {e}")

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

@start_router.message(F.text == "📤 Экспорт таблицы")
async def handle_export_table_button(message: Message):
    """Обработчик кнопки экспорта таблицы из Reply-меню"""
    user_id = message.from_user.id
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        await message.answer(
            "❌ У вас нет таблиц для экспорта.",
            reply_markup=get_main_keyboard()
        )
        return
    
    message_text = "📤 **Выберите таблицу для экспорта:**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message_text += f"{i}. **{table.original_name}**\n"
        message_text += f"   📅 {table.created_at} | 📊 {len(table.columns)} кол. | 📈 {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"📤 Экспорт", callback_data=f"select_export_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")])
    
    await message.answer(
        message_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("select_export_"))
async def handle_select_export(callback: CallbackQuery):
    """Обработчик выбора формата экспорта"""
    await callback.answer()
    table_id = callback.data.replace("select_export_", "")
    table = table_manager.get_table(table_id)
    
    if not table:
        await callback.message.edit_text("❌ Таблица не найдена.")
        return
    
    keyboard = [
        [InlineKeyboardButton(text="📊 Excel (.xlsx)", callback_data=f"export_{table.id}_xlsx")],
        [InlineKeyboardButton(text="📝 CSV (.csv)", callback_data=f"export_{table.id}_csv")],
        [InlineKeyboardButton(text="🔙 Назад к таблицам", callback_data="list_tables")]
    ]
    
    await callback.message.edit_text(
        f"📤 **Экспорт таблицы:** {table.original_name}\n\n"
        f"Выберите формат для экспорта:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@start_router.callback_query(F.data.startswith("export_"))
async def handle_export_table(callback: CallbackQuery):
    """Обработчик экспорта таблицы"""
    await callback.answer()
    
    # Парсим данные: export_{table_id}_{format}
    data_parts = callback.data.replace("export_", "").split("_")
    if len(data_parts) < 2:
        await callback.message.answer("❌ Ошибка формата экспорта.")
        return
    
    table_id = data_parts[0]
    export_format = data_parts[1]
    
    table = table_manager.get_table(table_id)
    if not table:
        await callback.message.answer("❌ Таблица не найдена.")
        return
    
    try:
        # Экспортируем таблицу
        export_path = table_manager.export_table(table_id, export_format)
        
        if export_path and os.path.exists(export_path):
            # Создаем понятное имя файла для экспорта
            original_name_without_ext = os.path.splitext(table.original_name)[0]
            export_filename = f"{original_name_without_ext}.{export_format}"
            
            file = FSInputFile(export_path, filename=export_filename)
            await callback.message.answer_document(
                document=file,
                caption=f"📤 Экспорт: {table.original_name}\n"
                       f"📅 Дата: {table.created_at}\n"
                       f"🔄 Формат: {export_format.upper()}"
            )
            
            # Удаляем временный файл экспорта
            try:
                os.remove(export_path)
            except:
                pass
                
        else:
            await callback.message.answer("❌ Ошибка при экспорте таблицы.")
            
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")
        await callback.message.answer(f"❌ Ошибка при экспорте: {str(e)}")

@start_router.message(F.text == "🔄 Обновить таблицу")
@start_router.callback_query(F.data == "update_table")
async def handle_update_table(message_or_callback: Message | CallbackQuery, state: FSMContext):
    """Обработчик обновления таблицы"""
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.answer()
        message = message_or_callback.message
        user_id = message_or_callback.from_user.id
    else:
        message = message_or_callback
        user_id = message.from_user.id
    
    tables = table_manager.get_user_tables(user_id)
    
    if not tables:
        if isinstance(message_or_callback, CallbackQuery):
            await message.edit_text(
                "❌ У вас нет таблиц для обновления.\n\n"
                "💡 Сначала сохраните таблицу через «📥 Сохранить таблицу».",
                parse_mode='Markdown'
            )
        else:
            await message.answer(
                "❌ У вас нет таблиц для обновления.\n\n"
                "💡 Сначала сохраните таблицу через «📥 Сохранить таблицу».",
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )
        return
    
    message_text = "🔄 **Выберите таблицу для обновления:**\n\n"
    keyboard = []
    
    for i, table in enumerate(tables, 1):
        message_text += f"{i}. **{table.original_name}**\n"
        message_text += f"   📅 {table.created_at} | 📊 {len(table.columns)} кол. | 📈 {table.rows_count} стр.\n\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"🔄 Обновить", callback_data=f"select_update_{table.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в меню", callback_data="back_main")])
    
    if isinstance(message_or_callback, CallbackQuery):
        await message.edit_text(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode='Markdown'
        )
    else:
        await message.answer(
            message_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode='Markdown'
        )

@start_router.callback_query(F.data.startswith("select_update_"))
async def handle_select_update(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора таблицы для обновления"""
    await callback.answer()
    table_id = callback.data.replace("select_update_", "")
    
    # Сохраняем ID таблицы для обновления в состоянии
    await state.update_data(update_table_id=table_id)
    await state.set_state(TableStates.waiting_update_file)
    
    table = table_manager.get_table(table_id)
    if table:
        await callback.message.edit_text(
            f"🔄 **Обновление таблицы:** {table.original_name}\n\n"
            f"📅 Текущая дата: {table.created_at}\n"
            f"📊 Столбцы: {len(table.columns)}\n"
            f"📈 Строки: {table.rows_count}\n\n"
            f"📎 Пожалуйста, загрузите новый файл для обновления этой таблицы.\n\n"
            f"💡 **Поддерживаемые форматы:** CSV, JSON, Excel",
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
