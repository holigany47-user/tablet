from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict

@dataclass
class TableInfo:
    """Модель для хранения информации о таблице"""
    id: str
    user_id: int
    filename: str
    original_name: str
    file_path: str
    created_at: str
    columns: List[str]
    rows_count: int
    file_size: int

class TableManager:
    """Менеджер для работы с таблицами"""
    
    def __init__(self):
        self.tables: Dict[str, TableInfo] = {}
    
    def add_table(self, user_id: int, filename: str, file_path: str, original_name: str, columns: List[str], rows_count: int, file_size: int) -> TableInfo:
        """Добавление новой таблицы"""
        table_id = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        created_at = datetime.now().strftime('%d.%m.%Y')
        
        table_info = TableInfo(
            id=table_id,
            user_id=user_id,
            filename=filename,
            original_name=original_name,
            file_path=file_path,
            created_at=created_at,
            columns=columns,
            rows_count=rows_count,
            file_size=file_size
        )
        
        self.tables[table_id] = table_info
        return table_info
    
    def get_user_tables(self, user_id: int) -> List[TableInfo]:
        """Получение таблиц пользователя"""
        return [table for table in self.tables.values() if table.user_id == user_id]
    
    def get_table(self, table_id: str) -> TableInfo:
        """Получение таблицы по ID"""
        return self.tables.get(table_id)
    
    def delete_table(self, table_id: str) -> bool:
        """Удаление таблицы"""
        if table_id in self.tables:
            del self.tables[table_id]
            return True
        return False
    
    def update_table(self, table_id: str, **kwargs) -> bool:
        """Обновление информации о таблице"""
        if table_id in self.tables:
            table = self.tables[table_id]
            for key, value in kwargs.items():
                if hasattr(table, key):
                    setattr(table, key, value)
            return True
        return False
