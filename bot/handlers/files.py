@router.message(F.text == "📥 Сохранить таблицу")
async def save_table_handler(message: Message, state: FSMContext):
    """Обработчик сохранения таблицы"""
    user_id = message.from_user.id
    logger.info(f"📥 Пользователь {user_id} начал сохранение таблицы")
    
    try:
        await state.set_state(FileStates.waiting_file)
        
        await message.answer(
            "📥 **Сохранение таблицы**\n\n"
            "Пожалуйста, загрузите файл таблицы (CSV, JSON, Excel).\n"
            "Файл будет сохранен с датой в названии.\n\n"
            "📁 **Поддерживаемые форматы:**\n"
            "• CSV (.csv)\n"
            "• JSON (.json)\n"
            "• Excel (.xlsx, .xls)"
        )
        logger.info(f"✅ Инструкции по сохранению отправлены пользователю {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в save_table_handler для пользователя {user_id}: {e}")
        await message.answer("❌ Ошибка при подготовке к сохранению таблицы")

@router.message(FileStates.waiting_file, F.document)
async def process_save_file(message: Message, state: FSMContext):
    """Обработка загруженного файла для сохранения"""
    user_id = message.from_user.id
    file_name = message.document.file_name
    
    logger.info(f"📎 Пользователь {user_id} загрузил файл для сохранения: '{file_name}'")
    
    try:
        if not validate_file_extension(file_name):
            logger.warning(f"⚠️ Неподдерживаемый формат файла от пользователя {user_id}: {file_name}")
            await message.answer("❌ Неподдерживаемый формат файла. Используйте Excel, CSV или JSON.")
            return
        
        # Здесь должна быть реальная логика сохранения файла
        # Пока просто сообщим, что файл получен
        await message.answer(
            f"✅ **Файл получен:** {file_name}\n\n"
            f"Файл принят к обработке. Скоро здесь будет сохранение."
        )
        logger.info(f"Файл {file_name} принят от пользователя {user_id}")
        
        # Сбрасываем состояние
        await state.clear()
        
    except Exception as e:
        logger.error(f"❌ Ошибка при обработке файла '{file_name}': {e}", exc_info=True)
        await message.answer("❌ Ошибка при обработке файла")
        await state.clear()

@router.message(FileStates.waiting_file)
async def wrong_save_file_input(message: Message):
    """Обработчик неправильного ввода при ожидании файла для сохранения"""
    user_id = message.from_user.id
    text = message.text or ""
    
    logger.warning(f"⚠️ Пользователь {user_id} отправил не файл в режиме сохранения: '{text}'")
    await message.answer("❌ Пожалуйста, отправьте файл в формате Excel, CSV или JSON для сохранения таблицы.")
