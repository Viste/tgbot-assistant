from aiogram.fsm.state import State, StatesGroup


class Text(StatesGroup):
    get = State()
    result = State()
