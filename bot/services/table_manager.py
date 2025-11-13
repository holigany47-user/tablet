import os
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json
import logging

# Импорты из helpers
from bot.utils.helpers import read_table_file, save_table_file, compare_tables, get_file_size, generate_timestamp
from bot.models import TableInfo

logger = logging.getLogger(__name__)

class AdvancedTableManager:
    """Расширенный менеджер для работы с таблицами"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.data_file = os.path.join(storage_path, "tables_data.json")
        self._ensure_storage_exists()
        self._load_data()
    
    def _ensure_storage_exists(self):
        """Создание папки для хранения таблиц"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _load_data(self):
        """Загрузка данных из JSON файла"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Конвертируем обратно в TableInfo объекты
                self.tables = {}
                for table_id, table_data in data.items():
                    self.tables[table_id] = TableInfo(**table_data)
        else:
            self.tables = {}
    
    def _save_data(self):
        """Сохранение данных в JSON файл"""
        # Конвертируем TableInfo в dict для JSON
        data = {}
        for table_id, table_info in self.tables.items():
            data[table_id] = {
                'id': table_info.id,
                'user_id': table_info.user_id,
                'filename': table_info.filename,
                'original_name': table_info.original_name,
                'file_path': table_info.file_path,
                'created_at': table_info.created_at,
                'columns': table_info.columns,
                'rows_count': table_info.rows_count,
                'file_size': table_info.file_size
            }
        
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_table(self, user_id: int, file_path: str, original_name: str) -> TableInfo:
        """Сохранение новой таблицы с датой в имени"""
        try:
            # Чтение таблицы для получения информации
            df, columns, rows_count = read_table_file(file_path)
            
            # Генерация имени файла с датой
            current_date = datetime.now().strftime('%d.%m.%Y')
            safe_name = original_name.replace(' ', '_')
            filename = f"{safe_name}_{current_date}_{generate_timestamp()}.xlsx"
            save_path = os.path.join(self.storage_path, filename)
            
            # Сохраняем файл
            save_table_file(df, save_path, 'xlsx')
            file_size = get_file_size(save_path)
            
            # Создание TableInfo объекта
            table_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            table_info = TableInfo(
                id=table_id,
                user_id=user_id,
                filename=filename,
                original_name=original_name,
                file_path=save_path,
                created_at=current_date,
                columns=columns,
                rows_count=rows_count,
                file_size=file_size
            )
            
            # Сохранение в данных
            self.tables[table_id] = table_info
            self._save_data()
            
            return table_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения таблицы: {e}")
            raise Exception(f"Ошибка сохранения таблицы: {e}")
    
    def get_user_tables(self, user_id: int) -> List[TableInfo]:
        """Получение всех таблиц пользователя"""
        return [table for table in self.tables.values() if table.user_id == user_id]
    
    def get_table(self, table_id: str) -> Optional[TableInfo]:
        """Получение таблицы по ID"""
        return self.tables.get(table_id)
    
    def delete_table(self, table_id: str) -> bool:
        """Удаление таблицы"""
        try:
            if table_id in self.tables:
                table = self.tables[table_id]
                # Удаление файла
                if os.path.exists(table.file_path):
                    os.remove(table.file_path)
                # Удаление из данных
                del self.tables[table_id]
                self._save_data()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении таблицы: {e}")
            return False
    
    def update_table(self, table_id: str, new_file_path: str, update_type: str = 'replace') -> Tuple[bool, Dict[str, Any]]:
        """Обновление таблицы с различными стратегиями (старая версия для совместимости)"""
        try:
            table = self.get_table(table_id)
            if not table:
                return False, {"error": "Таблица не найдена"}
            
            # Чтение старой и новой таблиц
            old_df, _, _ = read_table_file(table.file_path)
            new_df, new_columns, new_rows_count = read_table_file(new_file_path)
            
            comparison = compare_tables(old_df, new_df)
            
            if update_type == 'replace':
                # Полная замена
                result_df = new_df
                message = "Таблица полностью заменена"
                
            elif update_type == 'add_columns':
                # Добавление новых столбцов
                result_df = old_df.copy()
                for col in comparison['columns_diff']['added']:
                    result_df[col] = new_df[col] if col in new_df.columns else None
                message = "Добавлены новые столбцы"
                
            elif update_type == 'add_rows':
                # Добавление новых строк
                result_df = pd.concat([old_df, new_df], ignore_index=True)
                result_df = result_df.drop_duplicates()
                message = "Добавлены новые строки"
                
            elif update_type == 'merge':
                # Полное объединение
                common_cols = list(set(old_df.columns) & set(new_df.columns))
                if common_cols:
                    result_df = pd.merge(old_df, new_df, on=common_cols, how='outer')
                else:
                    result_df = pd.concat([old_df, new_df], axis=1)
                message = "Таблицы объединены"
                
            else:
                return False, {"error": "Неизвестный тип обновления"}
            
            # Сохранение обновленной таблицы
            save_table_file(result_df, table.file_path, 'xlsx')
            
            # Обновление информации о таблице
            table.columns = result_df.columns.tolist()
            table.rows_count = len(result_df)
            table.file_size = get_file_size(table.file_path)
            self._save_data()
            
            return True, {
                "message": message,
                "comparison": comparison,
                "new_columns": result_df.columns.tolist(),
                "new_rows_count": len(result_df)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления таблицы: {e}")
            return False, {"error": f"Ошибка обновления таблицы: {e}"}
    
    # НОВЫЕ МЕТОДЫ ДЛЯ СОВМЕСТИМОСТИ С НОВЫМ ФУНКЦИОНАЛОМ
    
    def read_table_file(self, file_path: str):
        """Чтение таблицы из файла (для совместимости с новым функционалом)"""
        return read_table_file(file_path)
    
    def save_table_file(self, df: pd.DataFrame, file_path: str, format: str):
        """Сохранение таблицы в файл (для совместимости с новым функционалом)"""
        return save_table_file(df, file_path, format)
    
    def get_file_size(self, file_path: str) -> int:
        """Получение размера файла (для совместимости с новым функционалом)"""
        return get_file_size(file_path)
    
    def export_table(self, table_id: str, format: str) -> Optional[str]:
        """Экспорт таблицы в другой формат"""
        try:
            table = self.get_table(table_id)
            if not table:
                return None
            
            df, _, _ = read_table_file(table.file_path)
            
            # Создание пути для экспорта
            export_filename = f"{os.path.splitext(table.filename)[0]}.{format}"
            export_path = os.path.join(self.storage_path, export_filename)
            
            save_table_file(df, export_path, format)
            return export_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка экспорта: {e}")
            return None
    
    def get_table_preview(self, table_id: str, rows: int = 5) -> Optional[pd.DataFrame]:
        """Получение превью таблицы"""
        try:
            table = self.get_table(table_id)
            if not table:
                return None
            
            df, _, _ = read_table_file(table.file_path)
            return df.head(rows)
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения превью: {e}")
            return None
