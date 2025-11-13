import os
import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.utils.helpers import get_tables_keyboard, get_main_keyboard, get_back_keyboard, create_table_action_keyboard, validate_file_extension, format_file_size
from bot.utils.helpers import get_scenario_selection_keyboard, get_conflict_resolution_keyboard, get_update_confirmation_keyboard, get_scenario_description, get_conflict_rule_description
from bot.utils.table_analyzer import TableAnalyzer
from bot.utils.scenario_applier import ScenarioApplier
from bot.services.local_storage import LocalStorage
from bot.services.table_manager import AdvancedTableManager
from bot.handlers.states import TableStates, UpdateScenarioStates

logger = logging.getLogger(__name__)

router = Router()
storage_service = LocalStorage()
table_manager = AdvancedTableManager()
table_analyzer = TableAnalyzer()
scenario_applier = ScenarioApplier()

# СУЩЕСТВУЮЩИЕ ОБРАБОТЧИКИ (без изменений)

@router.message(F.text == "📥 Сохранить таблицу")
async def save_table_handler(message: Message, state: FSMContext):
    """Обработчик сохранения таблицы"""
    user_id = message.from_user.id
    logger.info(f"📥 Пользователь {user_id} начал сохранение таблицы")
    
    try:
        await state.set_state(TableStates.waiting_file)
        
        await message.answer(
            "📥 **Сохранение таблицы**\n\n"
            "Пожалуйста, загрузите файл таблицы (CSV, JSON, Excel).\n"
            "Файл будет сохранен с датой в названии.\n\n"
            "📁 **Поддерживаемые форматы:**\n"
            "• CSV (.csv)\n"
            "• JSON (.json)\n"
            "• Excel (.xlsx, .xls)"
        )
        logger.info(f"✅ Инструкции по сохранению отправлены пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в save_table_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при подготовке к сохранению таблицы")

@router.message(TableStates.waiting_file, F.document)
async def process_save_file(message: Message, state: FSMContext):
    """Обработка загруженного файла для сохранения"""
    user_id = message.from_user.id
    file_name = message.document.file_name
    
    logger.info(f"📎 Пользователь {user_id} загрузил файл для сохранения: '{file_name}'")
    
    try:
        if not validate_file_extension(file_name):
            logger.warning(f"⚠️ Неподдерживаемый формат файла от пользователя {user_id}: {file_name}")
            await message.answer("❌ Неподдерживаемый формат файла. Используйте Excel, CSV или JSON.")
            return
        
        # Скачиваем файл от пользователя
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        
        # Сохраняем временный файл
        temp_path = f"temp_{user_id}_{file_name}"
        with open(temp_path, 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())
        
        # Сохраняем таблицу через AdvancedTableManager
        table_info = table_manager.save_table(user_id, temp_path, file_name)
        
        # Удаляем временный файл
        os.remove(temp_path)
        
        await message.answer(
            f"✅ **Таблица успешно сохранена!**\n\n"
            f"📁 Имя: {table_info.original_name}\n"
            f"📅 Дата: {table_info.created_at}\n"
            f"📊 Столбцы: {len(table_info.columns)}\n"
            f"📈 Строки: {table_info.rows_count}\n"
            f"💾 Размер: {format_file_size(table_info.file_size)}\n\n"
            f"💡 Таблица сохранена в формате Excel с датой в названии."
        )
        logger.info(f"✅ Таблица {table_info.original_name} сохранена пользователем {user_id}")
        
        # Сбрасываем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла '{file_name}': {e}", exc_info=True)
        await message.answer("❌ Ошибка при сохранении таблицы")
        await state.clear()

@router.message(TableStates.waiting_file)
async def wrong_save_file_input(message: Message):
    """Обработчик неправильного ввода при ожидании файла для сохранения"""
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.warning(f"⚠️ Пользователь {user_id} отправил не файл в режиме сохранения: '{text}'")
    await message.answer("❌ Пожалуйста, отправьте файл в формате Excel, CSV или JSON для сохранения таблицы.")

@router.message(F.text == "📋 Мои таблицы")
@router.message(Command("tables"))
async def list_tables_handler(message: Message, state: FSMContext):
    """Обработчик списка таблиц"""
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    
    logger.info(f"📋 Пользователь {user_id} (@{username}) запросил список таблиц")
    
    try:
        # Получаем список таблиц пользователя из AdvancedTableManager
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

# СТАРЫЙ ОБРАБОТЧИК ОБНОВЛЕНИЯ - ЗАМЕНЯЕМ НА НОВЫЙ
@router.callback_query(F.data.startswith("update_"))
async def process_update_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик callback для обновления таблицы - начинает процесс с анализа"""
    user_id = callback.from_user.id
    table_id = callback.data.replace("update_", "")
    
    logger.info(f"🔄 Пользователь {user_id} начинает обновление таблицы: {table_id}")
    
    try:
        # Получаем информацию о текущей таблице
        table_info = table_manager.get_table(table_id)
        if not table_info:
            await callback.message.edit_text("❌ Таблица не найдена.")
            return
        
        # Сохраняем ID таблицы для обновления в состоянии
        await state.update_data(table_to_update=table_id)
        await state.set_state(UpdateScenarioStates.waiting_update_file)
        
        await callback.message.edit_text(
            f"🔄 **Обновление таблицы: {table_info.original_name}**\n\n"
            f"📅 Текущая дата: {table_info.created_at}\n"
            f"📊 Текущие столбцы: {len(table_info.columns)}\n"
            f"📈 Текущие строки: {table_info.rows_count}\n\n"
            f"📎 Пожалуйста, загрузите новый файл для обновления этой таблицы.\n\n"
            f"💡 **Поддерживаемые форматы:** CSV, JSON, Excel\n\n"
            f"⚠️ **Внимание:** После загрузки файла будет предложено выбрать сценарий объединения."
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
        
        # Проверяем существование файла
        if os.path.exists(table_info.file_path):
            # Импортируем BufferedInputFile
            from aiogram.types import BufferedInputFile
            
            # Читаем файл в память и создаем BufferedInputFile
            with open(table_info.file_path, 'rb') as file:
                file_data = file.read()
            
            input_file = BufferedInputFile(
                file=file_data,
                filename=table_info.original_name
            )
            
            # Отправляем файл пользователю
            await callback.message.answer_document(
                document=input_file,
                caption=(
                    f"📤 **Таблица: {table_info.original_name}**\n\n"
                    f"📊 Столбцы: {len(table_info.columns)}\n"
                    f"📈 Строки: {table_info.rows_count}\n"
                    f"📅 Дата сохранения: {table_info.created_at}"
                )
            )
            logger.info(f"✅ Таблица {table_info.original_name} отправлена пользователю {user_id}")
            
            # Редактируем исходное сообщение
            await callback.message.edit_text(
                f"✅ **Таблица отправлена:** {table_info.original_name}\n\n"
                f"Файл успешно загружен и отправлен."
            )
        else:
            await callback.message.edit_text(
                f"❌ **Файл не найден**\n\n"
                f"Файл таблицы {table_info.original_name} не существует."
            )
            logger.error(f"❌ Файл таблицы не существует: {table_info.file_path}")
            
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

# НОВЫЕ ОБРАБОТЧИКИ ДЛЯ РАСШИРЕННОГО ОБНОВЛЕНИЯ

@router.message(UpdateScenarioStates.waiting_update_file, F.document)
async def process_update_file_analysis(message: Message, state: FSMContext):
    """Обработка файла для обновления таблицы с анализом и предложением сценариев"""
    user_id = message.from_user.id
    file_name = message.document.file_name
    
    logger.info(f"📎 Пользователь {user_id} загрузил файл для обновления: '{file_name}'")
    
    try:
        # Получаем ID таблицы для обновления из состояния
        state_data = await state.get_data()
        table_id = state_data.get('table_to_update')
        
        if not table_id:
            logger.error(f"❌ Не найдено ID таблицы для обновления у пользователя {user_id}")
            await message.answer("❌ Ошибка: не найдена информация о таблице для обновления.")
            await state.clear()
            return
        
        if not validate_file_extension(file_name):
            logger.warning(f"⚠️ Неподдерживаемый формат файла от пользователя {user_id}: {file_name}")
            await message.answer("❌ Неподдерживаемый формат файла. Используйте Excel, CSV или JSON.")
            return
        
        # Скачиваем новый файл
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        
        # Сохраняем временный файл
        temp_path = f"temp_update_{user_id}_{file_name}"
        with open(temp_path, 'wb') as new_file:
            new_file.write(downloaded_file.getvalue())
        
        # Получаем информацию о старой таблице
        table_info = table_manager.get_table(table_id)
        if not table_info:
            await message.answer("❌ Таблица для обновления не найдена.")
            await state.clear()
            return
        
        # Читаем старую и новую таблицы
        old_df, _, _ = table_manager.read_table_file(table_info.file_path)
        new_df, _, _ = table_manager.read_table_file(temp_path)
        
        if old_df is None or new_df is None:
            await message.answer("❌ Ошибка при чтении таблиц. Проверьте формат файлов.")
            await state.clear()
            return
        
        # Анализируем различия
        analysis = table_analyzer.analyze_tables_diff(old_df, new_df)
        
        # Сохраняем данные в состоянии
        await state.update_data(
            temp_file_path=temp_path,
            analysis=analysis,
            old_df_columns=list(old_df.columns),
            old_df_rows=len(old_df),
            new_df_columns=list(new_df.columns),
            new_df_rows=len(new_df)
        )
        
        # Форматируем отчет для пользователя
        report = table_analyzer.format_analysis_report(analysis)
        
        # Предлагаем выбрать сценарий
        await message.answer(
            f"{report}\n\n"
            "🔄 **ВЫБЕРИТЕ СЦЕНАРИЙ ОБНОВЛЕНИЯ:**",
            reply_markup=get_scenario_selection_keyboard()
        )
        
        await state.set_state(UpdateScenarioStates.waiting_scenario_selection)
        logger.info(f"✅ Анализ завершен, предложены сценарии пользователю {user_id}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при анализе файла '{file_name}': {e}", exc_info=True)
        await message.answer("❌ Ошибка при анализе таблицы. Проверьте формат файла.")
        await state.clear()

@router.callback_query(UpdateScenarioStates.waiting_scenario_selection, F.data.startswith("scenario_"))
async def process_scenario_selection(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора сценария обновления"""
    user_id = callback.from_user.id
    scenario = callback.data.replace("scenario_", "")
    
    logger.info(f"🔄 Пользователь {user_id} выбрал сценарий {scenario}")
    
    try:
        # Сохраняем выбранный сценарий
        await state.update_data(selected_scenario=scenario)
        
        # Показываем описание сценария
        scenario_desc = get_scenario_description(scenario)
        
        # Для сценария 4 (умное объединение) пропускаем выбор правила конфликтов
        if scenario == '4':
            await state.update_data(conflict_rule='A')  # по умолчанию
            await show_preview_and_confirm(callback, state)
        else:
            # Для остальных сценариев предлагаем выбрать правило конфликтов
            await callback.message.edit_text(
                f"{scenario_desc}\n\n"
                "⚡ **ВЫБЕРИТЕ ПРАВИЛО ДЛЯ КОНФЛИКТУЮЩИХ ИМЕН:**",
                reply_markup=get_conflict_resolution_keyboard()
            )
            await state.set_state(UpdateScenarioStates.waiting_conflict_resolution)
            
    except Exception as e:
        logger.error(f"❌ Ошибка при выборе сценария {scenario}: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при выборе сценария")

@router.callback_query(UpdateScenarioStates.waiting_conflict_resolution, F.data.startswith("conflict_"))
async def process_conflict_resolution(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора правила обработки конфликтов"""
    user_id = callback.from_user.id
    conflict_rule = callback.data.replace("conflict_", "")
    
    logger.info(f"🔄 Пользователь {user_id} выбрал правило конфликтов {conflict_rule}")
    
    try:
        await state.update_data(conflict_rule=conflict_rule)
        await show_preview_and_confirm(callback, state)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при выборе правила конфликтов: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при выборе правила")

async def show_preview_and_confirm(callback: CallbackQuery, state: FSMContext):
    """Показывает предварительный результат и запрашивает подтверждение"""
    user_id = callback.from_user.id
    
    try:
        state_data = await state.get_data()
        scenario = state_data.get('selected_scenario')
        conflict_rule = state_data.get('conflict_rule', 'A')
        table_id = state_data.get('table_to_update')
        temp_path = state_data.get('temp_file_path')
        analysis = state_data.get('analysis', {})
        
        # Получаем таблицы
        table_info = table_manager.get_table(table_id)
        old_df, _, _ = table_manager.read_table_file(table_info.file_path)
        new_df, _, _ = table_manager.read_table_file(temp_path)
        
        # Применяем сценарий для предварительного просмотра
        preview_df, message = scenario_applier.apply_scenario(scenario, old_df, new_df, conflict_rule)
        
        # Формируем сообщение с предварительным результатом
        scenario_names = {
            '1': 'Сохранить структуру + добавить строки',
            '2': 'Расширить структуру + сохранить строки', 
            '3': 'Полное объединение',
            '4': 'Умное объединение'
        }
        
        conflict_names = {
            'A': 'Сохранить имена из СТАРОЙ таблицы',
            'B': 'Использовать имена из НОВОЙ таблицы',
            'C': 'Объединить (приоритет новых)'
        }
        
        preview_text = (
            f"✅ **ПРЕДВАРИТЕЛЬНЫЙ РЕЗУЛЬТАТ**\n\n"
            f"📋 **Сценарий:** {scenario_names.get(scenario, 'Неизвестный')}\n"
            f"⚡ **Правило конфликтов:** {conflict_names.get(conflict_rule, 'Неизвестное')}\n"
            f"📊 **Итоговые размеры:** {len(preview_df)} строк, {len(preview_df.columns)} столбцов\n\n"
            f"📈 **Изменения:**\n"
            f"• Столбцов: +{len(preview_df.columns) - analysis.get('columns', {}).get('total_old', 0)}\n"
            f"• Строк: +{len(preview_df) - analysis.get('rows', {}).get('total_old', 0)}\n\n"
            f"💡 {message}\n\n"
            f"**Подтверждаете обновление?**"
        )
        
        await callback.message.edit_text(
            preview_text,
            reply_markup=get_update_confirmation_keyboard()
        )
        await state.set_state(UpdateScenarioStates.waiting_update_confirmation)
        
    except Exception as e:
        logger.error(f"❌ Ошибка при формировании предпросмотра: {e}")
        await callback.message.edit_text("❌ Ошибка при формировании предпросмотра результата")

@router.callback_query(UpdateScenarioStates.waiting_update_confirmation, F.data == "confirm_update")
async def process_update_confirmation(callback: CallbackQuery, state: FSMContext):
    """Обработчик подтверждения обновления таблицы"""
    user_id = callback.from_user.id
    
    logger.info(f"🔄 Пользователь {user_id} подтвердил обновление таблицы")
    
    try:
        state_data = await state.get_data()
        table_id = state_data.get('table_to_update')
        temp_path = state_data.get('temp_file_path')
        scenario = state_data.get('selected_scenario')
        conflict_rule = state_data.get('conflict_rule', 'A')
        
        # Получаем таблицы
        table_info = table_manager.get_table(table_id)
        old_df, _, _ = table_manager.read_table_file(table_info.file_path)
        new_df, _, _ = table_manager.read_table_file(temp_path)
        
        # Применяем сценарий
        result_df, message = scenario_applier.apply_scenario(scenario, old_df, new_df, conflict_rule)
        
        # Сохраняем обновленную таблицу
        table_manager.save_table_file(result_df, table_info.file_path, 'xlsx')
        
        # Обновляем информацию о таблице
        table_info.columns = result_df.columns.tolist()
        table_info.rows_count = len(result_df)
        table_info.file_size = table_manager.get_file_size(table_info.file_path)
        
        # Сохраняем данные в table_manager
        table_manager._save_data()
        
        await callback.message.edit_text(
            f"✅ **ТАБЛИЦА УСПЕШНО ОБНОВЛЕНА!**\n\n"
            f"📁 **Имя:** {table_info.original_name}\n"
            f"📊 **Столбцы:** {len(table_info.columns)}\n"
            f"📈 **Строки:** {table_info.rows_count}\n"
            f"💾 **Размер:** {format_file_size(table_info.file_size)}\n\n"
            f"💡 {message}"
        )
        
        logger.info(f"✅ Таблица {table_info.original_name} обновлена пользователем {user_id}")
        
        # Очищаем состояние
        await state.clear()
        
        # Удаляем временный файл
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении таблицы: {e}")
        await callback.message.edit_text("❌ Произошла ошибка при обновлении таблицы")
        await state.clear()

@router.callback_query(UpdateScenarioStates.waiting_scenario_selection, F.data == "cancel_update")
@router.callback_query(UpdateScenarioStates.waiting_conflict_resolution, F.data == "cancel_update")
@router.callback_query(UpdateScenarioStates.waiting_update_confirmation, F.data == "cancel_update")
async def process_cancel_update(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены обновления"""
    user_id = callback.from_user.id
    logger.info(f"❌ Пользователь {user_id} отменил обновление таблицы")
    
    # Удаляем временный файл
    state_data = await state.get_data()
    temp_path = state_data.get('temp_file_path')
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
    
    await state.clear()
    await callback.message.edit_text("❌ Обновление таблицы отменено.")
    await callback.message.answer(
        "Выберите следующее действие:",
        reply_markup=get_tables_keyboard()
    )

@router.callback_query(UpdateScenarioStates.waiting_update_confirmation, F.data == "change_scenario")
async def process_change_scenario(callback: CallbackQuery, state: FSMContext):
    """Обработчик смены сценария"""
    user_id = callback.from_user.id
    logger.info(f"🔄 Пользователь {user_id} запросил смену сценария")
    
    await callback.message.edit_text(
        "🔄 **ВЫБЕРИТЕ СЦЕНАРИЙ ОБНОВЛЕНИЯ:**",
        reply_markup=get_scenario_selection_keyboard()
    )
    await state.set_state(UpdateScenarioStates.waiting_scenario_selection)

@router.message(UpdateScenarioStates.waiting_update_file)
async def wrong_update_file_input(message: Message):
    """Обработчик неправильного ввода при ожидании файла для обновления"""
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.warning(f"⚠️ Пользователь {user_id} отправил не файл в режиме обновления: '{text}'")
    await message.answer("❌ Пожалуйста, отправьте файл в формате Excel, CSV или JSON для обновления таблицы.")
