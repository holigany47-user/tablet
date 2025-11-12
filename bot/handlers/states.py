from aiogram.fsm.state import State, StatesGroup

class TableStates(StatesGroup):
    waiting_table_file = State()      # для сохранения новых таблиц
    waiting_update_file = State()     # для обновления существующих таблиц
