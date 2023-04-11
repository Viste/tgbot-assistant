import logging

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, Message
from tools.utils import config

logger = logging.getLogger("__name__")


def setup_routers() -> Router:
    from . import core, demoget, admin

    router = Router()

    @router.message(Command(commands=["cancel"]), F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_(config.allowed_groups))
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
    router.include_router(demoget.router)
    router.include_router(admin.router)

    return router
