import os
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.utils.helpers import get_tables_keyboard, get_main_keyboard, get_back_keyboard, create_table_action_keyboard, validate_file_extension, read_file, save_dataframe, format_file_size
from bot.models import TableManager
from bot.models.services.local_storage import LocalStorage

logger = logging.getLogger(__name__)

router = Router()
storage_service = LocalStorage()
table_manager = TableManager()

class FileStates(StatesGroup):
    waiting_file = State()
    waiting_file_action = State()
    waiting_table_selection = State()
    waiting_update_file = State()
    table_to_update = State()

@router.message(F.text == "📋 Мои таблицы")
@router.message(Command("tables"))
async def list_tables_handler(message: Message, state: FSMContext):
    """Обработчик списка таблиц"""
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    
    logger.info(f"📋 Пользователь {user_id} (@{username}) запросил список таблиц")
    
    try:
        # Получаем список таблиц пользователя из TableManager
        user_tables = table_manager.get_user_tables(user_id)
        logger.debug(f"Найдено таблиц для пользователя {user_id}: {len(user_tables)}")
        
        if not user_tables:
            logger.info(f"У пользователя {user_id} нет таблиц")
            await message.answer(
                "📋 **Мои таблицы**\n\n"
                "У вас пока нет сохраненных таблиц.\n\n"
                "💡 Нажмите «📥 Сохранить таблицу», чтобы добавить первую таблицу.",
                reply_markup=get_tables_keyboard()
            )
            return
        
        # Формируем список таблиц для отображения
        tables_text = "📋 **Мои таблицы**\n\n"
        for table in user_tables:
            tables_text += f"📊 {table.original_name}\n"
            tables_text += f"📅 {table.created_at} • 📊 {len(table.columns)} кол. • 📈 {table.rows_count} стр.\n\n"
        
        tables_text += "Выберите действие:"
        
        await message.answer(tables_text, reply_markup=get_tables_keyboard())
        logger.info(f"✅ Список таблиц показан пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в list_tables_handler для пользователя {user_id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении списка таблиц")

@router.message(F.text == "🗑️ Удалить таблицу")
async def delete_table_handler(message: Message):
    """Обработчик удаления таблицы"""
    user_id = message.from_user.id
    logger.info(f"🗑️ Пользователь {user_id} начал удаление таблицы")
    
    try:
        user_tables = table_manager.get_user_tables(user_id)
        
        if not user_tables:
            await message.answer(
                "❌ У вас нет таблиц для удаления.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками удаления
        keyboard = create_table_action_keyboard(user_tables, "delete")
        
        await message.answer(
            "🗑️ **Удаление таблицы**\n\n"
            "Выберите таблицу для удаления:",
            reply_markup=keyboard
        )
        logger.info(f"✅ Клавиатура удаления показана пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в delete_table_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при подготовке к удалению таблицы")

@router.message(F.text == "🔄 Обновить таблицу")
async def update_table_handler(message: Message):
    """Обработчик обновления таблицы"""
    user_id = message.from_user.id
    logger.info(f"🔄 Пользователь {user_id} начал обновление таблицы")
    
    try:
        user_tables = table_manager.get_user_tables(user_id)
        
        if not user_tables:
            await message.answer(
                "❌ У вас нет таблиц для обновления.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками обновления
        keyboard = create_table_action_keyboard(user_tables, "update")
        
        await message.answer(
            "🔄 **Обновление таблицы**\n\n"
            "Выберите таблицу для обновления:",
            reply_markup=keyboard
        )
        logger.info(f"✅ Клавиатура обновления показана пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в update_table_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при подготовке к обновлению таблицы")

@router.message(F.text == "📤 Скачать таблицу")
async def download_table_handler(message: Message):
    """Обработчик скачивания таблицы"""
    user_id = message.from_user.id
    logger.info(f"📤 Пользователь {user_id} начал скачивание таблицы")
    
    try:
        user_tables = table_manager.get_user_tables(user_id)
        
        if not user_tables:
            await message.answer(
                "❌ У вас нет таблиц для скачивания.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками скачивания
        keyboard = create_table_action_keyboard(user_tables, "download")
        
        await message.answer(
            "📤 **Скачать таблицу**\n\n"
            "Выберите таблицу для скачивания:",
            reply_markup=keyboard
        )
        logger.info(f"✅ Клавиатура скачивания показана пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в download_table_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при подготовке к скачиванию таблицы")

@router.callback_query(F.data.startswith("delete_"))
async def process_delete_callback(callback: CallbackQuery):
    """Обработчик callback для удаления таблицы"""
    user_id = callback.from_user.id
    table_id = callback.data.replace("delete_", "")
    
    logger.info(f"🗑️ Пользователь {user_id} удаляет таблицу: {table_id}")
    
    try:
        # Получаем информацию о таблице перед удалением
        table_info = table_manager.get_table(table_id)
        if not table_info:
            await callback.message.edit_text("❌ Таблица не найдена.")
            return
        
        # Удаляем таблицу
        success = table_manager.delete_table(table_id)
        
        if success:
            await callback.message.edit_text(
                f"✅ **Таблица удалена**\n\n"
                f"📁 Имя: {table_info.original_name}\n\n"
                f"Таблица успешно удалена."
            )
            logger.info(f"✅ Таблица {table_info.original_name} удалена пользователем {user_id}")
        else:
            await callback.message.edit_text(
                f"❌ **Ошибка удаления**\n\n"
                f"Не удалось удалить таблицу {table_info.original_name}.\n"
                f"Возможно, она уже была удалена."
            )
            logger.warning(f"⚠️ Не удалось удалить таблицу {table_info.original_name} для пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении таблицы {table_id} пользователем {user_id}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении таблицы")

@router.callback_query(F.data.startswith("update_"))
async def process_update_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback для обновления таблицы"""
    user_id = callback.from_user.id
    table_id = callback.data.replace("update_", "")
    
    logger.info(f"🔄 Пользователь {user_id} обновляет таблицу: {table_id}")
    
    try:
        # Получаем информацию о текущей таблице
        table_info = table_manager.get_table(table_id)
        if not table_info:
            await callback.message.edit_text("❌ Таблица не найдена.")
            return
        
        # Сохраняем ID таблицы для обновления в состоянии
        await state.update_data(table_to_update=table_id)
        await state.set_state(FileStates.waiting_update_file)
        
        await callback.message.edit_text(
            f"🔄 **Обновление таблицы: {table_info.original_name}**\n\n"
            f"📅 Текущая дата: {table_info.created_at}\n"
            f"📊 Текущие столбцы: {len(table_info.columns)}\n"
            f"📈 Текущие строки: {table_info.rows_count}\n\n"
            f"📎 Пожалуйста, загрузите новый файл для обновления этой таблицы.\n\n"
            f"💡 **Поддерживаемые форматы:** CSV, JSON, Excel\n\n"
            f"⚠️ **Внимание:** Данные таблицы будут полностью заменены на новые."
        )
        logger.info(f"✅ Запрос нового файла для обновления таблицы {table_info.original_name} от пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при подготовке обновления таблицы {table_id}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при подготовке к обновлению таблицы")

@router.callback_query(F.data.startswith("download_"))
async def process_download_callback(callback: CallbackQuery):
    """Обработчик callback для скачивания таблицы"""
    user_id = callback.from_user.id
    table_id = callback.data.replace("download_", "")
    
    logger.info(f"📤 Пользователь {user_id} скачивает таблицу: {table_id}")
    
    try:
        # Получаем информацию о таблице
        table_info = table_manager.get_table(table_id)
        if not table_info:
            await callback.message.edit_text("❌ Таблица не найдена.")
            return
        
        # Загружаем данные таблицы из файла
        if os.path.exists(table_info.file_path):
            df = read_file(table_info.file_path)
            if df is not None:
                # Создаем временный файл для скачивания
                temp_filename = f"temp_{table_info.original_name}"
                success = save_dataframe(df, temp_filename)
                
                if success and os.path.exists(temp_filename):
                    file_info = get_file_info(temp_filename)
                    
                    # Здесь должна быть реальная логика отправки файла
                    # Пока просто показываем информацию
                    await callback.message.edit_text(
                        f"📤 **Скачать таблицу: {table_info.original_name}**\n\n"
                        f"📊 Столбцы: {len(table_info.columns)}\n"
                        f"📈 Строки: {table_info.rows_count}\n"
                        f"💾 Размер: {file_info.get('size', 'неизвестно')}\n\n"
                        f"💡 **Функция в разработке**\n"
                        f"Скоро здесь можно будет скачать таблицу в выбранном формате."
                    )
                    logger.info(f"✅ Информация для скачивания таблицы {table_info.original_name} отправлена пользователю {user_id}")
                    
                    # Удаляем временный файл
                    os.remove(temp_filename)
                else:
                    await callback.message.edit_text(
                        f"❌ **Ошибка скачивания**\n\n"
                        f"Не удалось подготовить таблицу {table_info.original_name} для скачивания."
                    )
            else:
                await callback.message.edit_text(
                    f"❌ **Ошибка загрузки**\n\n"
                    f"Не удалось загрузить данные таблицы {table_info.original_name}."
                )
        else:
            await callback.message.edit_text(
                f"❌ **Файл не найден**\n\n"
                f"Файл таблицы {table_info.original_name} не существует."
            )
            
    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании таблицы {table_id} пользователем {user_id}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при подготовке таблицы к скачиванию")

@router.callback_query(F.data == "cancel_action")
async def process_cancel_callback(callback: CallbackQuery):
    """Обработчик отмены действия"""
    user_id = callback.from_user.id
    logger.info(f"❌ Пользователь {user_id} отменил действие")
    
    await callback.message.edit_text("❌ Действие отменено.")
    await callback.message.answer(
        "Выберите следующее действие:",
        reply_markup=get_tables_keyboard()
    )

@router.message(F.text == "🔙 Назад")
async def back_handler(message: Message, state: FSMContext):
    """Обработчик кнопки Назад"""
    user_id = message.from_user.id
    logger.info(f"🔙 Пользователь {user_id} вернулся в главное меню")
    
    try:
        await state.clear()
        
        await message.answer(
            "🔙 Возврат в главное меню\n\nВыберите действие:",
            reply_markup=get_main_keyboard()
        )
        logger.info(f"✅ Пользователь {user_id} возвращен в главное меню")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в back_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при возврате в меню")

# Остальные обработчики остаются без изменений...
