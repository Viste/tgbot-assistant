from aiogram.fsm.state import State, StatesGroup


class RegisterStates(StatesGroup):
    start = State()
    process = State()
    end = State()


class Text(StatesGroup):
    get = State()
    result = State()


class Dialogue(StatesGroup):
    get = State()
    result = State()


class Payment(StatesGroup):
    start = State()
    process = State()
    end = State()


class NpPayment(StatesGroup):
    start = State()
    process = State()
    end = State()


class ZoomPayment(StatesGroup):
    start = State()
    process = State()
    end = State()


class DAImage(StatesGroup):
    get = State()
    result = State()
