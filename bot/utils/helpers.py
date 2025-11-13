import os
import pandas as pd
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging

logger = logging.getLogger(__name__)

def get_main_keyboard():
    """Создает главную клавиатуру меню"""
    logger.debug("Создание главной клавиатуры меню")
    try:
        buttons = [
            [KeyboardButton(text="📥 Сохранить таблицу"), KeyboardButton(text="📋 Мои таблицы")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        logger.debug("✅ Главная клавиатура создана успешно")
        return keyboard
    except Exception as e:
        logger.error(f"❌ Ошибка при создании главной клавиатуры: {e}")
        raise

def get_tables_keyboard():
    """Создает клавиатуру для работы с таблицами"""
    logger.debug("Создание клавиатуры для таблиц")
    try:
        buttons = [
            [KeyboardButton(text="📤 Скачать таблицу"), KeyboardButton(text="🔄 Обновить таблицу")],
            [KeyboardButton(text="🗑️ Удалить таблицу"), KeyboardButton(text="🔙 Назад")]
        ]
        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        logger.debug("✅ Клавиатура таблиц создана успешно")
        return keyboard
    except Exception as e:
        logger.error(f"❌ Ошибка при создании клавиатуры таблиц: {e}")
        raise

def get_back_keyboard():
    """Создает клавиатуру с кнопкой Назад"""
    logger.debug("Создание клавиатуры с кнопкой Назад")
    try:
        buttons = [[KeyboardButton(text="🔙 Назад")]]
        keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
        return keyboard
    except Exception as e:
        logger.error(f"❌ Ошибка при создании клавиатуры Назад: {e}")
        raise

def create_table_action_keyboard(tables_list, action_type="view"):
    """Создает инлайн-клавиатуру для действий с таблицами"""
    logger.debug(f"Создание инлайн-клавиатуры для действия: {action_type}")
    try:
        keyboard = []
        
        for table_info in tables_list:
            # Получаем короткое имя таблицы для отображения
            if hasattr(table_info, 'original_name'):
                display_name = table_info.original_name
                table_id = table_info.id
            else:
                # Если передали просто строку
                display_name = table_info
                table_id = table_info
            
            # Обрезаем длинные имена для кнопок
            if len(display_name) > 20:
                display_name = display_name[:17] + "..."
            
            # Создаем безопасный callback_data (только буквы, цифры, подчеркивания)
            safe_table_id = "".join(c for c in str(table_id) if c.isalnum() or c in ['_', '-'])
            
            if action_type == "delete":
                button_text = f"🗑️ {display_name}"
                callback_data = f"delete_{safe_table_id}"
            elif action_type == "update":
                button_text = f"🔄 {display_name}"
                callback_data = f"update_{safe_table_id}"
            elif action_type == "download":
                button_text = f"📤 {display_name}"
                callback_data = f"download_{safe_table_id}"
            else:
                button_text = f"👀 {display_name}"
                callback_data = f"view_{safe_table_id}"
            
            # Проверяем длину callback_data (Telegram ограничение 64 байта)
            if len(callback_data.encode('utf-8')) > 64:
                # Если слишком длинный, используем только ID
                callback_data = safe_table_id[:64]
            
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
            logger.debug(f"Создана кнопка: {button_text}, callback_data: {callback_data}")
        
        # Добавляем кнопку отмены
        keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    except Exception as e:
        logger.error(f"❌ Ошибка при создании инлайн-клавиатуры: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[])

def validate_file_extension(filename: str) -> bool:
    """Проверяет разрешение файла"""
    logger.debug(f"🔍 Проверка расширения файла: '{filename}'")
    try:
        allowed_extensions = {'.xlsx', '.xls', '.csv', '.json'}
        result = any(filename.lower().endswith(ext) for ext in allowed_extensions)
        logger.debug(f"Результат проверки расширения '{filename}': {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке расширения файла '{filename}': {e}")
        return False

def format_file_size(size_bytes: int) -> str:
    """Форматирует размер файла в читаемый вид"""
    logger.debug(f"📏 Форматирование размера файла: {size_bytes} байт")
    try:
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                result = f"{size_bytes:.1f} {unit}"
                logger.debug(f"Размер отформатирован: {result}")
                return result
            size_bytes /= 1024.0
        
        result = f"{size_bytes:.1f} TB"
        logger.debug(f"Размер отформатирован: {result}")
        return result
    except Exception as e:
        logger.error(f"❌ Ошибка при форматировании размера файла: {e}")
        return "Unknown size"

def read_file(file_path: str):
    """Читает файл в зависимости от расширения"""
    logger.info(f"📖 Чтение файла: '{file_path}'")
    try:
        if not os.path.exists(file_path):
            logger.error(f"❌ Файл не существует: '{file_path}'")
            return None
            
        if file_path.endswith('.csv'):
            logger.debug("Чтение CSV файла")
            df = pd.read_csv(file_path)
            logger.info(f"✅ CSV файл прочитан успешно, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
        elif file_path.endswith(('.xlsx', '.xls')):
            logger.debug("Чтение Excel файла")
            df = pd.read_excel(file_path)
            logger.info(f"✅ Excel файл прочитан успешно, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
        elif file_path.endswith('.json'):
            logger.debug("Чтение JSON файла")
            df = pd.read_json(file_path)
            logger.info(f"✅ JSON файл прочитан успешно, строк: {len(df)}, колонок: {len(df.columns)}")
            return df
        else:
            logger.error(f"❌ Неподдерживаемый формат файла: '{file_path}'")
            return None
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении файла '{file_path}': {e}", exc_info=True)
        return None

def save_dataframe(df: pd.DataFrame, file_path: str):
    """Сохраняет DataFrame в файл"""
    logger.info(f"💾 Сохранение DataFrame в файл: '{file_path}'")
    logger.debug(f"Размер DataFrame: {len(df)} строк, {len(df.columns)} колонок")
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if file_path.endswith('.csv'):
            logger.debug("Сохранение в CSV формат")
            df.to_csv(file_path, index=False)
        elif file_path.endswith(('.xlsx', '.xls')):
            logger.debug("Сохранение в Excel формат")
            df.to_excel(file_path, index=False)
        elif file_path.endswith('.json'):
            logger.debug("Сохранение в JSON формат")
            df.to_json(file_path, indent=2)
        else:
            logger.error(f"❌ Неподдерживаемый формат для сохранения: '{file_path}'")
            return False
        
        file_size = os.path.getsize(file_path)
        logger.info(f"✅ Файл успешно сохранен: '{file_path}' ({format_file_size(file_size)})")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении файла '{file_path}': {e}", exc_info=True)
        return False

def get_file_info(file_path: str) -> dict:
    """Возвращает информацию о файле"""
    logger.debug(f"🔍 Получение информации о файле: '{file_path}'")
    try:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            info = {
                'size': format_file_size(stat.st_size),
                'modified': pd.Timestamp(stat.st_mtime, unit='s'),
                'exists': True
            }
            logger.debug(f"Информация о файле получена: {info}")
            return info
        logger.warning(f"⚠️ Файл не существует: '{file_path}'")
        return {'exists': False}
    except Exception as e:
        logger.error(f"❌ Ошибка при получении информации о файле '{file_path}': {e}")
        return {'exists': False, 'error': str(e)}

def read_table_file(file_path: str):
    """Чтение таблицы из файла и возврат DataFrame, колонок и количества строк"""
    logger.info(f"📖 Чтение таблицы из файла: '{file_path}'")
    try:
        df = read_file(file_path)
        if df is not None:
            return df, list(df.columns), len(df)
        return None, [], 0
    except Exception as e:
        logger.error(f"❌ Ошибка при чтении таблицы '{file_path}': {e}")
        return None, [], 0

def save_table_file(df: pd.DataFrame, file_path: str, format: str):
    """Сохранение таблицы в файл"""
    logger.info(f"💾 Сохранение таблицы в файл: '{file_path}' формата {format}")
    try:
        if format == 'csv':
            df.to_csv(file_path, index=False)
        elif format in ['xlsx', 'xls']:
            df.to_excel(file_path, index=False)
        elif format == 'json':
            df.to_json(file_path, indent=2)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
        logger.info(f"✅ Таблица сохранена в {file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении таблицы в {file_path}: {e}")
        return False

def compare_tables(old_df: pd.DataFrame, new_df: pd.DataFrame) -> dict:
    """Сравнение двух таблиц"""
    logger.debug("🔍 Сравнение таблиц")
    try:
        old_cols = set(old_df.columns)
        new_cols = set(new_df.columns)
        
        return {
            'columns_diff': {
                'added': list(new_cols - old_cols),
                'removed': list(old_cols - new_cols),
                'common': list(old_cols & new_cols)
            },
            'rows_diff': {
                'old_rows': len(old_df),
                'new_rows': len(new_df),
                'difference': len(new_df) - len(old_df)
            }
        }
    except Exception as e:
        logger.error(f"❌ Ошибка при сравнении таблиц: {e}")
        return {}

def get_file_size(file_path: str) -> int:
    """Получение размера файла в байтах"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def generate_timestamp() -> str:
    """Генерация временной метки"""
    from datetime import datetime
    return datetime.now().strftime("%H%M%S")

# НОВЫЕ ФУНКЦИИ ДЛЯ СЦЕНАРИЕВ ОБНОВЛЕНИЯ

def get_scenario_selection_keyboard():
    """Клавиатура для выбора сценария обновления"""
    buttons = [
        [InlineKeyboardButton(text="📊 Сохранить структуру + добавить строки", callback_data="scenario_1")],
        [InlineKeyboardButton(text="🔄 Расширить структуру + сохранить строки", callback_data="scenario_2")],
        [InlineKeyboardButton(text="🧩 Полное объединение (структура + строки)", callback_data="scenario_3")],
        [InlineKeyboardButton(text="⚡ Умное объединение (авто)", callback_data="scenario_4")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_update")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_conflict_resolution_keyboard():
    """Клавиатура для выбора правила обработки конфликтов"""
    buttons = [
        [InlineKeyboardButton(text="✅ Сохранить имена из СТАРОЙ таблицы", callback_data="conflict_A")],
        [InlineKeyboardButton(text="🔄 Использовать имена из НОВОЙ таблицы", callback_data="conflict_B")],
        [InlineKeyboardButton(text="⚡ Объединить (приоритет новых)", callback_data="conflict_C")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_update")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_update_confirmation_keyboard():
    """Клавиатура для подтверждения обновления"""
    buttons = [
        [InlineKeyboardButton(text="✅ ДА, ОБНОВИТЬ", callback_data="confirm_update")],
        [InlineKeyboardButton(text="🔄 ВЫБРАТЬ ДРУГОЙ СЦЕНАРИЙ", callback_data="change_scenario")],
        [InlineKeyboardButton(text="❌ ОТМЕНА", callback_data="cancel_update")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_key_column_keyboard(columns: list, table_type: str = "common"):
    """Клавиатура для выбора ключевого столбца"""
    buttons = []
    
    # Кнопки для общих столбцов
    for col in columns:
        buttons.append([InlineKeyboardButton(text=f"🔑 {col}", callback_data=f"key_{col}")])
    
    # Дополнительные опции
    if table_type == "common":
        buttons.extend([
            [InlineKeyboardButton(text="📋 Использовать все столбцы", callback_data="key_all_columns")],
            [InlineKeyboardButton(text="🚫 Без ключа (добавить все)", callback_data="key_no_key")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_update")]
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_scenario_description(scenario: str) -> str:
    """Возвращает описание сценария"""
    descriptions = {
        '1': "📊 **Сценарий 1: Сохранить структуру + добавить строки**\n\n"
             "✅ Сохраняет оригинальные столбцы старой таблицы\n"
             "✅ Добавляет новые строки из новой таблицы\n"
             "⚠️ Игнорирует новые столбцы из новой таблицы",
        
        '2': "🔄 **Сценарий 2: Расширить структуру + сохранить строки**\n\n"
             "✅ Добавляет новые столбцы из новой таблицы\n"
             "✅ Сохраняет все строки из старой таблицы\n"
             "⚠️ Не добавляет новые строки из новой таблицы",
        
        '3': "🧩 **Сценарий 3: Полное объединение (структура + строки)**\n\n"
             "✅ Добавляет новые столбцы из новой таблицы\n"
             "✅ Добавляет новые строки из новой таблицы\n"
             "✅ Сохраняет все строки из старой таблицы",
        
        '4': "⚡ **Сценарий 4: Умное объединение (авто)**\n\n"
             "🤖 Автоматический выбор оптимальной стратегии\n"
             "📊 Анализирует объем изменений и предлагает баланс\n"
             "👁️ Показывает предварительный результат для подтверждения"
    }
    return descriptions.get(scenario, "❌ Неизвестный сценарий")

def get_conflict_rule_description(rule: str) -> str:
    """Возвращает описание правила конфликтов"""
    descriptions = {
        'A': "✅ **Сохранить имена из СТАРОЙ таблицы**\n"
             "Использует названия столбцов из исходной таблицы",
        
        'B': "🔄 **Использовать имена из НОВОЙ таблицы**\n"
             "Использует названия столбцов из новой таблицы",
        
        'C': "⚡ **Объединить (приоритет новых)**\n"
             "Использует новые названия, сохраняя старые как резерв"
    }
    return descriptions.get(rule, "❌ Неизвестное правило")

def get_key_column_description(key_option: str) -> str:
    """Описание вариантов выбора ключевого столбца"""
    descriptions = {
        "all_columns": "📋 **Использовать все столбцы**\nСравнивает строки по всем общим столбцам (точное совпадение)",
        "no_key": "🚫 **Без ключа (добавить все)**\nДобавляет все строки из новой таблицы (возможны дубликаты)",
    }
    return descriptions.get(key_option, f"🔑 **Ключевой столбец:** {key_option}")

def get_table_preview_text(df: pd.DataFrame, table_name: str, max_rows: int = 5) -> str:
    """Генерирует текстовое превью таблицы"""
    try:
        preview_text = [
            f"📊 **Превью таблицы: {table_name}**",
            f"📈 Строк: {len(df)}, 📋 Столбцов: {len(df.columns)}",
            "",
            "```",
        ]
        
        # Берем первые несколько строк
        preview_df = df.head(max_rows)
        
        # Формируем заголовок
        headers = "\t".join(str(col) for col in preview_df.columns)
        preview_text.append(headers)
        
        # Формируем строки данных
        for _, row in preview_df.iterrows():
            row_data = "\t".join(str(cell) if pd.notna(cell) else "" for cell in row)
            preview_text.append(row_data)
        
        preview_text.append("```")
        
        if len(df) > max_rows:
            preview_text.append(f"*... и еще {len(df) - max_rows} строк*")
        
        return "\n".join(preview_text)
    except Exception as e:
        logger.error(f"Ошибка при создании превью: {e}")
        return f"❌ Не удалось создать превью таблицы"
