import logging
import pandas as pd
from typing import Dict, Any, List, Tuple
import os

logger = logging.getLogger(__name__)

def validate_dataframe_structure(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Проверяет структуру DataFrame на корректность
    """
    logger.info("🔍 Валидация структуры DataFrame")
    
    try:
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {}
        }
        
        # Проверка на пустой DataFrame
        if df.empty:
            logger.warning("⚠️ DataFrame пустой")
            validation_result['warnings'].append("DataFrame пустой")
            validation_result['is_valid'] = False
            return validation_result
        
        # Базовая информация
        validation_result['info']['rows'] = len(df)
        validation_result['info']['columns'] = len(df.columns)
        validation_result['info']['column_names'] = list(df.columns)
        
        logger.debug(f"Информация о DataFrame: {validation_result['info']}")
        
        # Проверка на наличие NaN в названиях колонок
        if df.columns.isna().any():
            error_msg = "Обнаружены NaN в названиях колонок"
            logger.error(f"❌ {error_msg}")
            validation_result['errors'].append(error_msg)
            validation_result['is_valid'] = False
        
        # Проверка на дубликаты в названиях колонок
        if df.columns.duplicated().any():
            error_msg = "Обнаружены дублирующиеся названия колонок"
            logger.error(f"❌ {error_msg}")
            validation_result['errors'].append(error_msg)
            validation_result['is_valid'] = False
        
        # Проверка типов данных
        dtype_info = {}
        for col in df.columns:
            dtype_info[col] = str(df[col].dtype)
            # Проверка на слишком много NaN в колонке
            null_count = df[col].isna().sum()
            null_percentage = (null_count / len(df)) * 100
            if null_percentage > 50:
                warning_msg = f"Колонка '{col}' содержит {null_percentage:.1f}% пустых значений"
                logger.warning(f"⚠️ {warning_msg}")
                validation_result['warnings'].append(warning_msg)
        
        validation_result['info']['dtypes'] = dtype_info
        logger.debug(f"Типы данных колонок: {dtype_info}")
        
        if validation_result['is_valid']:
            logger.info("✅ Валидация DataFrame завершена успешно")
        else:
            logger.warning("⚠️ Валидация DataFrame завершена с ошибками")
            
        return validation_result
        
    except Exception as e:
        logger.error(f"❌ Ошибка при валидации DataFrame: {e}", exc_info=True)
        return {
            'is_valid': False,
            'errors': [f"Ошибка валидации: {str(e)}"],
            'warnings': [],
            'info': {}
        }

def validate_csv_content(content: str) -> bool:
    """
    Проверяет содержимое CSV на корректность
    """
    logger.debug("🔍 Валидация содержимого CSV")
    
    try:
        lines = content.split('\n')
        if len(lines) < 2:
            logger.error("❌ CSV содержит недостаточно строк")
            return False
        
        # Проверка, что все строки имеют одинаковое количество колонок
        first_line_columns = len(lines[0].split(','))
        for i, line in enumerate(lines[1:], 1):
            if line.strip():  # Пропускаем пустые строки
                if len(line.split(',')) != first_line_columns:
                    logger.error(f"❌ Несоответствие количества колонок в строке {i}")
                    return False
        
        logger.debug("✅ Валидация CSV завершена успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при валидации CSV: {e}")
        return False

def validate_excel_headers(headers: List[str]) -> bool:
    """
    Проверяет заголовки Excel файла на корректность
    """
    logger.debug(f"🔍 Валидация заголовков Excel: {headers}")
    
    try:
        if not headers:
            logger.error("❌ Заголовки пустые")
            return False
        
        # Проверка на пустые заголовки
        if any(not header or header.strip() == '' for header in headers):
            logger.error("❌ Обнаружены пустые заголовки")
            return False
        
        # Проверка на слишком длинные заголовки
        if any(len(header) > 100 for header in headers):
            logger.warning("⚠️ Обнаружены очень длинные заголовки")
        
        logger.debug("✅ Валидация заголовков Excel завершена успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при валидации заголовков Excel: {e}")
        return False

def validate_file_size(file_path: str, max_size_mb: int = 10) -> Tuple[bool, str]:
    """
    Проверяет размер файла
    """
    try:
        file_size = os.path.getsize(file_path)
        file_size_mb = file_size / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return False, f"Размер файла ({file_size_mb:.1f} MB) превышает максимальный допустимый ({max_size_mb} MB)"
        
        return True, f"Размер файла: {file_size_mb:.1f} MB"
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке размера файла: {e}")
        return False, f"Ошибка проверки размера файла: {str(e)}"

def validate_excel_file(file_path: str) -> Tuple[bool, List[str]]:
    """
    Проверяет Excel файл на корректность
    """
    errors = []
    
    try:
        # Попытка прочитать файл
        df = pd.read_excel(file_path)
        
        # Проверка на пустой файл
        if df.empty:
            errors.append("Excel файл пустой")
            return False, errors
        
        # Проверка структуры
        validation_result = validate_dataframe_structure(df)
        if not validation_result['is_valid']:
            errors.extend(validation_result['errors'])
        
        return len(errors) == 0, errors
        
    except Exception as e:
        error_msg = f"Ошибка чтения Excel файла: {str(e)}"
        logger.error(f"❌ {error_msg}")
        errors.append(error_msg)
        return False, errors

def validate_table_file(file_path: str, file_extension: str) -> Tuple[bool, List[str]]:
    """
    Общая валидация табличных файлов
    """
    errors = []
    
    try:
        # Проверка размера файла
        size_valid, size_msg = validate_file_size(file_path)
        if not size_valid:
            errors.append(size_msg)
        
        # Специфичные проверки для разных форматов
        if file_extension in ['.xlsx', '.xls']:
            excel_valid, excel_errors = validate_excel_file(file_path)
            if not excel_valid:
                errors.extend(excel_errors)
        
        # Для CSV и JSON полагаемся на базовое чтение файла
        # Если файл прочитается без ошибок - он валиден
        
        return len(errors) == 0, errors
        
    except Exception as e:
        error_msg = f"Ошибка валидации файла: {str(e)}"
        logger.error(f"❌ {error_msg}")
        errors.append(error_msg)
        return False, errors
