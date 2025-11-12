import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from bot.utils.helpers import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

class MainMenu(StatesGroup):
    main = State()

@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    
    logger.info(f"🎬 Команда START от пользователя {user_id} (@{username})")
    
    try:
        await state.set_state(MainMenu.main)
        
        welcome_text = (
            "👋 **Table Manager Bot**\n\n"
            "Я помогу вам работать с таблицами:\n\n"
            "📥 **Сохранить таблицу** - загрузить новую таблицу\n"
            "📋 **Мои таблицы** - просмотр и управление таблицами\n"
            "ℹ️ **Помощь** - справка по использованию бота\n\n"
            "Выберите действие в меню ниже 👇"
        )
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_keyboard()
        )
        logger.info(f"✅ Приветственное сообщение отправлено пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в обработчике start для пользователя {user_id}: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при запуске бота")

@router.message(Command("help"))
@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    user_id = message.from_user.id
    logger.info(f"ℹ️ Команда HELP от пользователя {user_id}")
    
    try:
        help_text = (
            "ℹ️ **Table Manager Bot - Помощь**\n\n"
            "**Основные команды:**\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n\n"
            "**Поддерживаемые форматы:**\n"
            "• CSV (.csv)\n"
            "• JSON (.json) \n"
            "• Excel (.xlsx, .xls)\n\n"
            "**Функционал:**\n"
            "• Сохранение таблиц с датой в названии\n"
            "• Просмотр списка таблиц\n"
            "• Обновление существующих таблиц\n"
            "• Удаление таблиц\n"
            "• Скачивание таблиц\n\n"
            "💡 **Совет:** Используйте кнопки меню для удобной навигации!"
        )
        
        await message.answer(help_text)
        logger.debug(f"✅ Справка отправлена пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в help_handler для пользователя {user_id}: {e}")

@router.message(F.text == "❌ Закрыть меню")
async def close_menu_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"❌ Закрытие меню пользователем {user_id}")
    
    try:
        await state.clear()
        
        await message.answer(
            "Меню закрыто. Используйте /start чтобы открыть снова.",
            reply_markup=ReplyKeyboardRemove()
        )
        logger.info(f"✅ Меню закрыто для пользователя {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при закрытии меню пользователем {user_id}: {e}")

@router.message(MainMenu.main)
async def main_menu_handler(message: Message):
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.info(f"🎯 Действие в главном меню от пользователя {user_id}: '{text}'")
    
    try:
        if message.text == "📥 Сохранить таблицу":
            logger.debug(f"Пользователь {user_id} выбрал 'Сохранить таблицу'")
            await message.answer("📥 Переходим к сохранению таблицы...")
            
        elif message.text == "📋 Мои таблицы":
            logger.debug(f"Пользователь {user_id} выбрал 'Мои таблицы'")
            await message.answer("📋 Переходим к просмотру таблиц...")
            
        elif message.text == "ℹ️ Помощь":
            logger.debug(f"Пользователь {user_id} выбрал 'Помощь'")
            await message.answer("ℹ️ Открываю справку...")
            
        else:
            logger.warning(f"⚠️ Неизвестная команда в меню от пользователя {user_id}: '{text}'")
            await message.answer("❌ Неизвестная команда. Используйте кнопки меню.")
            
    except Exception as e:
        logger.error(f"❌ Ошибка в main_menu_handler для пользователя {user_id}: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обработке команды")
