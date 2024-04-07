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


class Demo(StatesGroup):
    start = State()
    process = State()
    get = State()


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


class Mail(StatesGroup):
    start = State()


class DAImage(StatesGroup):
    get = State()
    result = State()
