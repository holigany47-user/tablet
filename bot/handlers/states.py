from aiogram.fsm.state import State, StatesGroup

class TableStates(StatesGroup):
    waiting_file = State()              # для сохранения новых таблиц (переименовано из waiting_table_file)
    waiting_update_file = State()       # для обновления существующих таблиц

class UpdateScenarioStates(StatesGroup):
    """Состояния для процесса выбора сценария обновления"""
    waiting_update_file = State()           # ожидание файла для обновления
    waiting_scenario_selection = State()    # выбор сценария
    waiting_conflict_resolution = State()   # выбор правила конфликтов
    waiting_update_confirmation = State()   # подтверждение обновления
