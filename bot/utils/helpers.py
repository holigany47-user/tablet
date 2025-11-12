import os
import logging
import pandas as pd
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Tuple
import tempfile

# Настройка логирования
logger = logging.getLogger(__name__)

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )

def get_file_extension(filename):
    """Получение расширения файла"""
    return os.path.splitext(filename)[1].lower()

def validate_file_extension(filename, allowed_extensions):
    """Проверка расширения файла"""
    extension = get_file_extension(filename)
    return extension in allowed_extensions

def generate_timestamp():
    """Генерация временной метки для имен файлов"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def safe_filename(filename):
    """Создание безопасного имени файла"""
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ")
    return safe_name.strip()

def get_current_date():
    """Получение текущей даты в формате дд.мм.гггг"""
    return datetime.now().strftime('%d.%m.%Y')

def read_table_file(file_path: str) -> Tuple[pd.DataFrame, List[str], int]:
    """Чтение табличного файла в различных форматах"""
    ext = get_file_extension(file_path)
    
    try:
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif ext == '.csv':
            df = pd.read_csv(file_path)
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Преобразуем JSON в DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([data])
        elif ext == '.xml':
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Простое преобразование XML в DataFrame
            data = []
            for child in root:
                row = {}
                for subchild in child:
                    row[subchild.tag] = subchild.text
                data.append(row)
            df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        # Обработка пустого DataFrame
        if df.empty:
            logger.warning(f"Файл {file_path} пустой")
            return pd.DataFrame(), [], 0
        
        # Очистка названий колонок от пробелов
        df.columns = df.columns.astype(str).str.strip()
        
        columns = df.columns.tolist()
        rows_count = len(df)
        
        logger.info(f"Успешно прочитан файл {file_path}: {rows_count} строк, {len(columns)} колонок")
        
        return df, columns, rows_count
        
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise ValueError(f"Ошибка чтения файла {file_path}: {str(e)}")

def save_table_file(df: pd.DataFrame, file_path: str, format: str = 'xlsx'):
    """Сохранение таблицы в различных форматах"""
    try:
        # Создание директории если не существует
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        if format == 'xlsx':
            df.to_excel(file_path, index=False)
        elif format == 'csv':
            df.to_csv(file_path, index=False, encoding='utf-8')
        elif format == 'json':
            df.to_json(file_path, orient='records', indent=2, force_ascii=False)
        elif format == 'xml':
            # Простое сохранение в XML
            root = ET.Element('root')
            for _, row in df.iterrows():
                item = ET.SubElement(root, 'item')
                for col, value in row.items():
                    child = ET.SubElement(item, str(col))
                    child.text = str(value) if pd.notna(value) else ''
            
            tree = ET.ElementTree(root)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Успешно сохранен файл {file_path} в формате {format}")
            
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        raise

def compare_tables(df1: pd.DataFrame, df2: pd.DataFrame) -> Dict[str, Any]:
    """Сравнение двух таблиц"""
    comparison = {
        'same_structure': False,
        'columns_diff': {
            'added': [],
            'removed': [],
            'changed': []
        },
        'rows_diff': {
            'added': len(df2) - len(df1) if len(df2) > len(df1) else 0,
            'removed': len(df1) - len(df2) if len(df1) > len(df2) else 0
        },
        'data_diff': {}
    }
    
    # Сравнение столбцов
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    comparison['columns_diff']['added'] = list(cols2 - cols1)
    comparison['columns_diff']['removed'] = list(cols1 - cols2)
    
    # Проверка одинаковой структуры
    comparison['same_structure'] = (
        len(comparison['columns_diff']['added']) == 0 and
        len(comparison['columns_diff']['removed']) == 0 and
        len(df1) == len(df2)
    )
    
    return comparison

def get_file_size(file_path: str) -> int:
    """Получение размера файла в байтах"""
    try:
        return os.path.getsize(file_path)
    except OSError as e:
        logger.error(f"Error getting file size for {file_path}: {e}")
        return 0

def format_file_size(size_bytes: int) -> str:
    """Форматирование размера файла в читаемый вид"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
        
    return f"{size_bytes:.1f} {size_names[i]}"

def validate_dataframe(df: pd.DataFrame) -> Tuple[bool, str]:
    """Валидация DataFrame на корректность"""
    if df.empty:
        return False, "Таблица пустая"
    
    if len(df.columns) == 0:
        return False, "В таблице нет колонок"
    
    # Проверка на наличие NaN в названиях колонок
    if df.columns.isna().any():
        return False, "Обнаружены пустые названия колонок"
    
    # Проверка на дубликаты в названиях колонок
    if df.columns.duplicated().any():
        return False, "Обнаружены дублирующиеся названия колонок"
    
    return True, "OK"
