import os
import glob
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from bot.services.table_manager import AdvancedTableManager
from bot.handlers.states import TableStates
from bot.utils.helpers import validate_file_extension, safe_filename

files_router = Router()
table_manager = AdvancedTableManager()

# Поддерживаемые форматы
SUPPORTED_EXTENSIONS = ['.csv', '.json']

@files_router.message(StateFilter(TableStates.waiting_table_file), F.document)
async def handle_table_file(message: Message, state: FSMContext):
    """Обработчик загружаемых файлов таблиц"""
    user_id = message.from_user.id
    
    try:
        document = message.document
        if document:
            file = await message.bot.get_file(document.file_id)
            original_name = document.file_name or "unknown_file"
        else:
            await message.answer("❌ Пожалуйста, отправьте файл как документ.")
            return

        # Проверка формата файла
        if not validate_file_extension(original_name, SUPPORTED_EXTENSIONS):
            await message.answer(
                f"❌ Неподдерживаемый формат файла.\n"
                f"Поддерживаемые форматы: {', '.join(SUPPORTED_EXTENSIONS)}"
            )
            return

        # Скачивание файла
        safe_name = safe_filename(original_name)
        temp_path = f"temp_{user_id}_{safe_name}"
        await message.bot.download_file(file.file_path, temp_path)

        # Сохранение таблицы
        table_info = table_manager.save_table(user_id, temp_path, original_name)
        
        # Очистка временного файла
        if os.path.exists(temp_path):
            os.remove(temp_path)

        await message.answer(
            f"✅ **Таблица успешно сохранена!**\n\n"
            f"📁 Имя: {table_info.original_name}\n"
            f"📅 Дата: {table_info.created_at}\n"
            f"📊 Столбцы: {len(table_info.columns)}\n"
            f"📈 Строки: {table_info.rows_count}\n"
            f"💾 Размер: {table_info.file_size / 1024:.1f} KB",
            parse_mode='Markdown'
        )

        # Сбрасываем состояние
        await state.clear()

    except Exception as e:
        await message.answer(f"❌ Ошибка при сохранении таблицы: {str(e)}")
        
        # Очистка временного файла в случае ошибки
        temp_path = f"temp_{user_id}_*"
        for temp_file in glob.glob(temp_path):
            try:
                os.remove(temp_file)
            except:
                pass
        await state.clear()

@files_router.message(StateFilter(TableStates.waiting_table_file))
async def handle_wrong_input(message: Message, state: FSMContext):
    """Обработчик неправильного ввода в состоянии ожидания файла"""
    await message.answer(
        "❌ Пожалуйста, отправьте файл таблицы (CSV или JSON).\n"
        "Или нажмите /start для возврата в меню."
    )
