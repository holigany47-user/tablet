import logging
import os

logger = logging.getLogger(__name__)

def setup_environment():
    """
    Настройка окружения приложения
    """
    logger.info("🔧 Настройка окружения приложения")
    
    try:
        # Проверка обязательных переменных окружения
        required_vars = ['BOT_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.critical(f"❌ Отсутствуют обязательные переменные окружения: {missing_vars}")
            return False
        
        # Создание необходимых директорий
        directories = ['data', 'logs', 'temp']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"✅ Директория создана/проверена: '{directory}'")
        
        logger.info("✅ Окружение приложения настроено успешно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка при настройке окружения: {e}", exc_info=True)
        return False

def get_project_root():
    """
    Возвращает корневую директорию проекта
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logger.debug(f"Корневая директория проекта: '{current_dir}'")
    return current_dir
