import logging

from aiogram import Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, Message

logger = logging.getLogger(__name__)


def setup_routers() -> Router:
    from . import core, demo_catcher, email_catcher, demo_listener, user, moderator, ban_manager
    from core.helpers import work_manager, callbacks, payment
    from core.ansma import edit_manager, unsupported_manager, user_manager

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

    router.include_router(work_manager.router)
    router.include_router(unsupported_manager.router)
    router.include_router(ban_manager.router)
    router.include_router(edit_manager.router)
    router.include_router(user_manager.router)
    router.include_router(core.router)
    router.include_router(callbacks.router)
    router.include_router(payment.router)
    router.include_router(user.router)
    router.include_router(moderator.router)
    router.include_router(demo_catcher.router)
    router.include_router(email_catcher.router)
    router.include_router(demo_listener.router)

    return router
