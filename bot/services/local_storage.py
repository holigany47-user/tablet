import os
import json
from typing import Dict, Any, List
from datetime import datetime

class LocalStorage:
    """Локальное хранилище для пользовательских данных"""
    
    def __init__(self, storage_path: str = "user_data"):
        self.storage_path = storage_path
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Создание папки для хранения данных"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def _get_user_file_path(self, user_id: int) -> str:
        """Получение пути к файлу пользователя"""
        return os.path.join(self.storage_path, f"user_{user_id}.json")
    
    def save_user_data(self, user_id: int, key: str, value: Any):
        """Сохранение данных пользователя"""
        try:
            file_path = self._get_user_file_path(user_id)
            
            # Загрузка существующих данных
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # Обновление данных
            data[key] = value
            data['last_updated'] = datetime.now().isoformat()
            
            # Сохранение
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"Ошибка сохранения данных пользователя: {e}")
    
    def get_user_data(self, user_id: int, key: str = None) -> Any:
        """Получение данных пользователя"""
        try:
            file_path = self._get_user_file_path(user_id)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return data.get(key) if key else data
            
        except Exception as e:
            print(f"Ошибка получения данных пользователя: {e}")
            return None
    
    def delete_user_data(self, user_id: int, key: str = None) -> bool:
        """Удаление данных пользователя"""
        try:
            file_path = self._get_user_file_path(user_id)
            
            if not os.path.exists(file_path):
                return False
            
            if key is None:
                # Удаление всех данных пользователя
                os.remove(file_path)
                return True
            else:
                # Удаление конкретного ключа
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if key in data:
                    del data[key]
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Ошибка удаления данных пользователя: {e}")
            return False
    
    def get_all_users(self) -> List[int]:
        """Получение списка всех пользователей"""
        try:
            users = []
            for filename in os.listdir(self.storage_path):
                if filename.startswith('user_') and filename.endswith('.json'):
                    user_id = int(filename[5:-5])  # Извлекаем ID из 'user_12345.json'
                    users.append(user_id)
            return users
        except Exception as e:
            print(f"Ошибка получения списка пользователей: {e}")
            return []
