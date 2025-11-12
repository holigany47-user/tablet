import os
import glob
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

# Используем единый менеджер
from bot.services import table_manager
from bot.handlers.states import TableStates
from bot.utils.helpers import validate_file_extension, safe_filename

files_router = Router()

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
            await message.answer("❌ Пожалуйста, отправьте файл как документ.", reply_markup=get_main_keyboard())
            return

        # Проверка формата файла
        if not validate_file_extension(original_name, ['.csv', '.json', '.xlsx', '.xls']):
            await message.answer(
                f"❌ Неподдерживаемый формат файла.\n\n"
                f"📁 **Поддерживаемые форматы:**\n"
                f"• CSV (.csv)\n"
                f"• JSON (.json)\n" 
                f"• Excel (.xlsx, .xls)\n\n"
                f"💡 Файл должен быть отправлен как документ (не как фото или сжатый архив).",
                parse_mode='Markdown',
                reply_markup=get_main_keyboard()
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
            f"💾 Размер: {table_info.file_size / 1024:.1f} KB\n\n"
            f"💡 Таблица сохранена в формате Excel с датой в названии.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

        # Сбрасываем состояние
        await state.clear()

    except Exception as e:
        error_message = f"❌ Ошибка при сохранении таблицы: {str(e)}"
        
        # Более понятные сообщения об ошибках
        if "Unsupported file format" in str(e):
            error_message += "\n\n💡 Убедитесь, что файл не поврежден и имеет правильный формат."
        elif "No columns to parse from file" in str(e):
            error_message += "\n\n💡 Файл не содержит данных или имеет неправильную структуру."
        
        await message.answer(error_message, reply_markup=get_main_keyboard())
        
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
        f"❌ Пожалуйста, отправьте файл таблицы.\n\n"
        f"📁 **Поддерживаемые форматы:**\n"
        f"• CSV (.csv)\n"
        f"• JSON (.json)\n"
        f"• Excel (.xlsx, .xls)\n\n"
        f"💡 Файл должен быть отправлен как **документ** (не как фото или сжатый архив).\n"
        f"Или нажмите /start для возврата в меню.",
        parse_mode='Markdown',
        reply_markup=get_main_keyboard()
    )
