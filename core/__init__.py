import logging

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, Message

logger = logging.getLogger(__name__)


def setup_routers() -> Router:
    from . import handler, payment
    from core.helpers import callbacks

    router = Router()

    @router.message(Command(commands=["cancel"]), F.chat.type.in_({'group', 'supergroup', 'private'}))
    @router.message(F.text.casefold() == "cancel")
    async def cancel_handler(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        logger.info("%s", message)
        if current_state is None:
            return

        logger.info("Cancelling state %r", current_state)
        await state.clear()
        await message.answer("Контекст обнулен.", reply_markup=ReplyKeyboardRemove())

    router.include_router(handler.router)
    router.include_router(payment.router)
    router.include_router(callbacks.router)

    return router
