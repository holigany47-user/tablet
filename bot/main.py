import asyncio
import logging
import sys
import os
from os import getenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.handlers import router

# Настройка расширенного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('bot_debug.log', encoding='utf-8', mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Дополнительный логгер для ошибок
error_logger = logging.getLogger('error_logger')
error_handler = logging.FileHandler('bot_errors.log', encoding='utf-8', mode='w')
error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

async def main():
    logger.info("🚀 === ЗАПУСК ТАБЛИЧНОГО БОТА ===")
    
    try:
        # Получение токена из переменных окружения
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        logger.debug("Проверка переменной окружения BOT_TOKEN")
        
        if not BOT_TOKEN:
            logger.critical("❌ BOT_TOKEN не найден в переменных окружения!")
            error_logger.error("BOT_TOKEN отсутствует в окружении")
            raise ValueError("BOT_TOKEN не установлен")
            
        logger.info(f"✅ Токен получен: {BOT_TOKEN[:10]}...")
        logger.info(f"🔧 Режим: {getenv('BOT_ENV', 'development')}")
        logger.debug(f"Текущая директория: {os.getcwd()}")
        logger.debug(f"Python версия: {sys.version}")
        
        # Инициализация бота
        logger.debug("Инициализация бота...")
        bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        logger.info("✅ Бот инициализирован")
        
        # Инициализация диспетчера
        logger.debug("Инициализация диспетчера и хранилища...")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        logger.info("✅ Диспетчер инициализирован")
        
        # Регистрация роутеров
        logger.debug("Регистрация роутеров...")
        dp.include_router(router)
        logger.info("✅ Роутеры зарегистрированы")
        
        # Запуск бота
        logger.info("🔄 Запуск поллинга...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.critical(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        error_logger.critical(f"Критическая ошибка при запуске: {e}", exc_info=True)
    finally:
        logger.info("🛑 Бот остановлен")
        if 'bot' in locals():
            await bot.session.close()
            logger.debug("Сессия бота закрыта")

if __name__ == "__main__":
    logger.debug("Запуск asyncio event loop")
    asyncio.run(main())
