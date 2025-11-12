import os
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import json

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
                self.tables_data = json.load(f)
        else:
            self.tables_data = {}
    
    def _save_data(self):
        """Сохранение данных в JSON файл"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.tables_data, f, ensure_ascii=False, indent=2)
    
    def save_table(self, user_id: int, file_path: str, original_name: str) -> Dict[str, Any]:
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
            
            # Создание записи о таблице
            table_id = str(len(self.tables_data) + 1)
            table_info = {
                'table_id': table_id,
                'user_id': user_id,
                'filename': filename,
                'file_path': save_path,
                'original_name': original_name,
                'columns': columns,
                'rows_count': rows_count,
                'file_size': file_size,
                'created_at': current_date
            }
            
            # Сохранение в данных
            if str(user_id) not in self.tables_data:
                self.tables_data[str(user_id)] = {}
            self.tables_data[str(user_id)][table_id] = table_info
            self._save_data()
            
            return table_info
            
        except Exception as e:
            raise Exception(f"Ошибка сохранения таблицы: {e}")
    
    def get_user_tables(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех таблиц пользователя"""
        user_tables = self.tables_data.get(str(user_id), {})
        return list(user_tables.values())
    
    def get_table(self, table_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение таблицы по ID для конкретного пользователя"""
        user_tables = self.tables_data.get(str(user_id), {})
        return user_tables.get(table_id)
    
    def delete_table(self, table_id: str, user_id: int) -> bool:
        """Удаление таблицы"""
        try:
            user_tables = self.tables_data.get(str(user_id), {})
            if table_id in user_tables:
                table = user_tables[table_id]
                # Удаление файла
                if os.path.exists(table['file_path']):
                    os.remove(table['file_path'])
                # Удаление из данных
                del user_tables[table_id]
                self._save_data()
                return True
            return False
        except Exception as e:
            print(f"Ошибка при удалении таблицы: {e}")
            return False
