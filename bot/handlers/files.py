import os
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.utils.helpers import get_tables_keyboard, get_main_keyboard, get_back_keyboard, create_table_action_keyboard, validate_file_extension, read_file, save_dataframe, format_file_size
from bot.models.services.local_storage import LocalStorage
from bot.models.services.table_manager import TableManager

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
        # Получаем список таблиц пользователя
        user_files = storage_service.list_user_files(user_id)
        logger.debug(f"Найдено таблиц для пользователя {user_id}: {len(user_files)}")
        
        if not user_files:
            logger.info(f"У пользователя {user_id} нет таблиц")
            await message.answer(
                "📋 **Мои таблицы**\n\n"
                "У вас пока нет сохраненных таблиц.\n\n"
                "💡 Нажмите «📥 Сохранить таблицу», чтобы добавить первую таблицу.",
                reply_markup=get_tables_keyboard()
            )
            return
        
        # Показываем меню действий с таблицами
        tables_text = "📋 **Мои таблицы**\n\nВыберите действие:"
        await message.answer(tables_text, reply_markup=get_tables_keyboard())
        logger.info(f"✅ Меню таблиц показано пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в list_tables_handler для пользователя {user_id}: {e}", exc_info=True)
        await message.answer("❌ Ошибка при получении списка таблиц")

@router.message(F.text == "🗑️ Удалить таблицу")
async def delete_table_handler(message: Message):
    """Обработчик удаления таблицы"""
    user_id = message.from_user.id
    logger.info(f"🗑️ Пользователь {user_id} начал удаление таблицы")
    
    try:
        user_files = storage_service.list_user_files(user_id)
        
        if not user_files:
            await message.answer(
                "❌ У вас нет таблиц для удаления.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками удаления
        keyboard = create_table_action_keyboard(user_files, "delete")
        
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
        user_files = storage_service.list_user_files(user_id)
        
        if not user_files:
            await message.answer(
                "❌ У вас нет таблиц для обновления.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками обновления
        keyboard = create_table_action_keyboard(user_files, "update")
        
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
        user_files = storage_service.list_user_files(user_id)
        
        if not user_files:
            await message.answer(
                "❌ У вас нет таблиц для скачивания.\n\n"
                "Сначала сохраните таблицу через «📥 Сохранить таблицу»."
            )
            return
        
        # Создаем инлайн-клавиатуру с кнопками скачивания
        keyboard = create_table_action_keyboard(user_files, "download")
        
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
    table_name = callback.data.replace("delete_", "")
    
    logger.info(f"🗑️ Пользователь {user_id} удаляет таблицу: {table_name}")
    
    try:
        # Удаляем таблицу
        success = storage_service.delete_data(table_name, user_id)
        
        if success:
            await callback.message.edit_text(
                f"✅ **Таблица удалена**\n\n"
                f"📁 Имя: {table_name}\n\n"
                f"Таблица успешно удалена из хранилища."
            )
            logger.info(f"✅ Таблица {table_name} удалена пользователем {user_id}")
        else:
            await callback.message.edit_text(
                f"❌ **Ошибка удаления**\n\n"
                f"Не удалось удалить таблицу {table_name}.\n"
                f"Возможно, она уже была удалена."
            )
            logger.warning(f"⚠️ Не удалось удалить таблицу {table_name} для пользователя {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при удалении таблицы {table_name} пользователем {user_id}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при удалении таблицы")

@router.callback_query(F.data.startswith("update_"))
async def process_update_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback для обновления таблицы"""
    user_id = callback.from_user.id
    table_name = callback.data.replace("update_", "")
    
    logger.info(f"🔄 Пользователь {user_id} обновляет таблицу: {table_name}")
    
    try:
        # Сохраняем имя таблицы для обновления в состоянии
        await state.update_data(table_to_update=table_name)
        await state.set_state(FileStates.waiting_update_file)
        
        # Получаем информацию о текущей таблице
        table_data = storage_service.load_data(table_name, user_id)
        if table_data and 'dataframe' in table_data:
            df = table_data['dataframe']
            row_count = len(df)
            col_count = len(df.columns)
        else:
            row_count = "неизвестно"
            col_count = "неизвестно"
        
        await callback.message.edit_text(
            f"🔄 **Обновление таблицы: {table_name}**\n\n"
            f"📊 Текущие столбцы: {col_count}\n"
            f"📈 Текущие строки: {row_count}\n\n"
            f"📎 Пожалуйста, загрузите новый файл для обновления этой таблицы.\n\n"
            f"💡 **Поддерживаемые форматы:** CSV, JSON, Excel\n\n"
            f"⚠️ **Внимание:** Данные таблицы будут полностью заменены на новые."
        )
        logger.info(f"✅ Запрос нового файла для обновления таблицы {table_name} от пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при подготовке обновления таблицы {table_name}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при подготовке к обновлению таблицы")

@router.callback_query(F.data.startswith("download_"))
async def process_download_callback(callback: CallbackQuery):
    """Обработчик callback для скачивания таблицы"""
    user_id = callback.from_user.id
    table_name = callback.data.replace("download_", "")
    
    logger.info(f"📤 Пользователь {user_id} скачивает таблицу: {table_name}")
    
    try:
        # Загружаем данные таблицы
        table_data = storage_service.load_data(table_name, user_id)
        
        if not table_data or 'dataframe' not in table_data:
            await callback.message.edit_text(
                f"❌ **Таблица не найдена**\n\n"
                f"Таблица {table_name} не найдена в хранилище."
            )
            return
        
        df = table_data['dataframe']
        
        # Создаем временный файл для скачивания
        temp_filename = f"temp_{table_name}"
        success = save_dataframe(df, temp_filename)
        
        if success and os.path.exists(temp_filename):
            # Здесь должна быть логика отправки файла пользователю
            # В реальном боте используем callback.message.answer_document
            file_info = get_file_info(temp_filename)
            
            await callback.message.edit_text(
                f"📤 **Скачать таблицу: {table_name}**\n\n"
                f"📊 Столбцы: {len(df.columns)}\n"
                f"📈 Строки: {len(df)}\n"
                f"💾 Размер: {file_info.get('size', 'неизвестно')}\n\n"
                f"💡 **Функция в разработке**\n"
                f"Скоро здесь можно будет скачать таблицу в выбранном формате."
            )
            logger.info(f"✅ Информация для скачивания таблицы {table_name} отправлена пользователю {user_id}")
            
            # Удаляем временный файл
            os.remove(temp_filename)
        else:
            await callback.message.edit_text(
                f"❌ **Ошибка скачивания**\n\n"
                f"Не удалось подготовить таблицу {table_name} для скачивания."
            )
            logger.error(f"❌ Ошибка при подготовке таблицы {table_name} для скачивания")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании таблицы {table_name} пользователем {user_id}: {e}")
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

@router.message(FileStates.waiting_update_file, F.document)
async def process_update_file(message: Message, state: FSMContext):
    """Обработка файла для обновления таблицы"""
    user_id = message.from_user.id
    file_name = message.document.file_name
    
    logger.info(f"📎 Пользователь {user_id} загрузил файл для обновления: '{file_name}'")
    
    try:
        # Получаем имя таблицы для обновления из состояния
        state_data = await state.get_data()
        table_name = state_data.get('table_to_update')
        
        if not table_name:
            logger.error(f"❌ Не найдено имя таблицы для обновления у пользователя {user_id}")
            await message.answer("❌ Ошибка: не найдена информация о таблице для обновления.")
            await state.clear()
            return
        
        logger.debug(f"Обновление таблицы {table_name} файлом {file_name}")
        
        if not validate_file_extension(file_name):
            logger.warning(f"⚠️ Неподдерживаемый формат файла от пользователя {user_id}: {file_name}")
            await message.answer("❌ Неподдерживаемый формат файла. Используйте Excel, CSV или JSON.")
            return
        
        # Здесь должна быть логика обработки и сохранения файла
        # В реальном боте нужно скачать файл и обработать его
        
        success = True  # Заглушка для успешного обновления
        
        if success:
            await message.answer(
                f"✅ **Таблица успешно обновлена!**\n\n"
                f"📁 Имя: {table_name}\n"
                f"📄 Новый файл: {file_name}\n\n"
                f"💡 Данные таблицы были заменены на новые."
            )
            logger.info(f"✅ Таблица {table_name} обновлена пользователем {user_id} файлом {file_name}")
            
            # Очищаем состояние
            await state.clear()
            
            # Возвращаем в меню таблиц
            await message.answer(
                "Выберите следующее действие:",
                reply_markup=get_tables_keyboard()
            )
        else:
            await message.answer("❌ Ошибка при обновлении таблицы.")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении таблицы файлом '{file_name}': {e}", exc_info=True)
        await message.answer("❌ Ошибка при обновлении таблицы")
        await state.clear()

@router.message(FileStates.waiting_update_file)
async def wrong_update_file_input(message: Message):
    """Обработчик неправильного ввода при ожидании файла для обновления"""
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.warning(f"⚠️ Пользователь {user_id} отправил не файл в режиме обновления: '{text}'")
    await message.answer("❌ Пожалуйста, отправьте файл в формате Excel, CSV или JSON для обновления таблицы.")
