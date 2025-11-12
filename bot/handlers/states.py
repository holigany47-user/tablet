from aiogram.fsm.state import State, StatesGroup

class TableStates(StatesGroup):
    waiting_table_file = State()
    waiting_update_file = State()
