import logging

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, Message

logger = logging.getLogger(__name__)


def setup_routers() -> Router:
    from . import demo_catcher, global_router, obs_processor, subscribe_payment, course_payment
    from core.helpers import admin_manager, callbacks, unsupported_manager

    router = Router()

    @router.message(Command(commands=["cancel"]), F.chat.type.in_({'group', 'supergroup', 'private'}))
    @router.message(F.text.casefold() == "cancel")
    async def cancel_handler(message: Message, state: FSMContext) -> None:
        current_state = await state.get_state()
        logging.info("%s", message)
        if current_state is None:
            return

        logging.info("Cancelling state %r", current_state)
        await state.clear()
        await message.answer("Контекст обнулен.", reply_markup=ReplyKeyboardRemove())

    router.include_router(admin_manager.router)
    router.include_router(unsupported_manager.router)
    router.include_router(global_router.router)
    router.include_router(callbacks.router)
    router.include_router(obs_processor.router)
    router.include_router(subscribe_payment.router)
    router.include_router(course_payment.router)
    router.include_router(demo_catcher.router)

    return router
