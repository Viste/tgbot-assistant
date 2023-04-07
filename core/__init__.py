import logging

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, Message

from tools.utils import config

logger = logging.getLogger("__name__")


def setup_routers() -> Router:
    from . import core

    router = Router()
    router.message.filter(F.chat.id != config.allowed_group)

    @router.message(Command(commands=["cancel"]))
    @router.message(F.text.casefold() == "cancel")
    async def cancel_handler(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        logging.info("%s", message)
        if current_state is None:
            return

        logging.info("Cancelling state %r", current_state)
        await state.clear()
        await message.answer("Контекст обнулен.", reply_markup=ReplyKeyboardRemove())

    router.include_router(core.router)

    return router
