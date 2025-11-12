import os
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Абсолютные импорты
from bot.models import TableInfo, TableManager
from bot.utils.helpers import read_table_file, save_table_file, compare_tables, get_file_size, generate_timestamp

class AdvancedTableManager:
    """Расширенный менеджер для работы с таблицами"""
    
    def __init__(self, storage_path: str = "storage"):
        self.storage_path = storage_path
        self.table_manager = TableManager()
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Создание папки для хранения таблиц"""
        os.makedirs(self.storage_path, exist_ok=True)
    
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
            
            # Сохранение файла
            save_table_file(df, save_path, 'xlsx')
            file_size = get_file_size(save_path)
            
            # Добавление в менеджер
            table_info = self.table_manager.add_table(
                user_id=user_id,
                filename=filename,
                file_path=save_path,
                original_name=original_name,
                columns=columns,
                rows_count=rows_count,
                file_size=file_size
            )
            
            return table_info
            
        except Exception as e:
            raise Exception(f"Ошибка сохранения таблицы: {e}")
    
    def get_user_tables(self, user_id: int) -> List[TableInfo]:
        """Получение всех таблиц пользователя"""
        return self.table_manager.get_user_tables(user_id)
    
    def get_table(self, table_id: str) -> Optional[TableInfo]:
        """Получение таблицы по ID"""
        return self.table_manager.get_table(table_id)
    
    def delete_table(self, table_id: str) -> bool:
        """Удаление таблицы"""
        table = self.table_manager.get_table(table_id)
        if table:
            # Удаление файла
            if os.path.exists(table.file_path):
                os.remove(table.file_path)
            # Удаление из менеджера
            return self.table_manager.delete_table(table_id)
        return False
    
    def update_table(self, table_id: str, new_file_path: str, update_type: str = 'replace') -> Tuple[bool, Dict[str, Any]]:
        """Обновление таблицы с различными стратегиями"""
        try:
            table = self.table_manager.get_table(table_id)
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
            self.table_manager.update_table(
                table_id=table_id,
                columns=result_df.columns.tolist(),
                rows_count=len(result_df),
                file_size=get_file_size(table.file_path)
            )
            
            return True, {
                "message": message,
                "comparison": comparison,
                "new_columns": result_df.columns.tolist(),
                "new_rows_count": len(result_df)
            }
            
        except Exception as e:
            return False, {"error": f"Ошибка обновления таблицы: {e}"}
    
    def export_table(self, table_id: str, format: str) -> Optional[str]:
        """Экспорт таблицы в другой формат"""
        try:
            table = self.table_manager.get_table(table_id)
            if not table:
                return None
            
            df, _, _ = read_table_file(table.file_path)
            
            # Создание пути для экспорта
            export_filename = f"{os.path.splitext(table.filename)[0]}.{format}"
            export_path = os.path.join(self.storage_path, export_filename)
            
            save_table_file(df, export_path, format)
            return export_path
            
        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            return None
    
    def get_table_preview(self, table_id: str, rows: int = 5) -> Optional[pd.DataFrame]:
        """Получение превью таблицы"""
        try:
            table = self.table_manager.get_table(table_id)
            if not table:
                return None
            
            df, _, _ = read_table_file(table.file_path)
            return df.head(rows)
            
        except Exception as e:
            print(f"Ошибка получения превью: {e}")
            return None
