import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class LocalStorage:
    """
    Сервис для локального хранения данных
    """
    
    def __init__(self, storage_path: str = "data"):
        self.storage_path = storage_path
        logger.info(f"🔄 Инициализация LocalStorage с путем: '{storage_path}'")
        
        try:
            os.makedirs(storage_path, exist_ok=True)
            logger.debug(f"✅ Директория хранения создана/проверена: '{storage_path}'")
        except Exception as e:
            logger.error(f"❌ Ошибка при создании директории хранения: {e}")
            raise

    def save_data(self, key: str, data: Any, user_id: Optional[int] = None) -> bool:
        """
        Сохраняет данные по ключу
        """
        try:
            filename = self._get_filename(key, user_id)
            logger.debug(f"💾 Сохранение данных по ключу '{key}' в файл: '{filename}'")
            
            with open(filename, 'w', encoding='utf-8') as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    f.write(str(data))
            
            logger.info(f"✅ Данные успешно сохранены по ключу '{key}'")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении данных по ключу '{key}': {e}")
            return False

    def load_data(self, key: str, user_id: Optional[int] = None) -> Optional[Any]:
        """
        Загружает данные по ключу
        """
        try:
            filename = self._get_filename(key, user_id)
            logger.debug(f"📖 Загрузка данных по ключу '{key}' из файла: '{filename}'")
            
            if not os.path.exists(filename):
                logger.warning(f"⚠️ Файл не существует: '{filename}'")
                return None
            
            with open(filename, 'r', encoding='utf-8') as f:
                # Пытаемся загрузить как JSON, иначе как текст
                try:
                    data = json.load(f)
                    logger.debug(f"✅ Данные загружены как JSON по ключу '{key}'")
                    return data
                except json.JSONDecodeError:
                    f.seek(0)
                    data = f.read()
                    logger.debug(f"✅ Данные загружены как текст по ключу '{key}'")
                    return data
                    
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке данных по ключу '{key}': {e}")
            return None

    def delete_data(self, key: str, user_id: Optional[int] = None) -> bool:
        """
        Удаляет данные по ключу
        """
        try:
            filename = self._get_filename(key, user_id)
            logger.debug(f"🗑 Удаление данных по ключу '{key}', файл: '{filename}'")
            
            if os.path.exists(filename):
                os.remove(filename)
                logger.info(f"✅ Данные удалены по ключу '{key}'")
                return True
            else:
                logger.warning(f"⚠️ Файл для удаления не существует: '{filename}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка при удалении данных по ключу '{key}': {e}")
            return False

    def list_user_files(self, user_id: int) -> List[str]:
        """
        Возвращает список файлов пользователя
        """
        try:
            user_pattern = f"user_{user_id}_"
            logger.debug(f"📋 Получение списка файлов для пользователя {user_id}")
            
            files = []
            if os.path.exists(self.storage_path):
                for filename in os.listdir(self.storage_path):
                    if filename.startswith(user_pattern):
                        files.append(filename.replace(user_pattern, "").replace(".json", ""))
            
            logger.debug(f"✅ Найдено файлов для пользователя {user_id}: {len(files)}")
            return files
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении списка файлов пользователя {user_id}: {e}")
            return []

    def _get_filename(self, key: str, user_id: Optional[int] = None) -> str:
        """
        Генерирует имя файла для хранения
        """
        if user_id:
            filename = f"user_{user_id}_{key}.json"
        else:
            filename = f"global_{key}.json"
        
        return os.path.join(self.storage_path, filename)
