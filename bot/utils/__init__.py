from dataclasses import dataclass
from typing import List

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
