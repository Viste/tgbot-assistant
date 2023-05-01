from aiogram.fsm.state import State, StatesGroup


class Text(StatesGroup):
    get = State()
    result = State()


class Demo(StatesGroup):
    start = State()
    get = State()


class Mail(StatesGroup):
    start = State()
