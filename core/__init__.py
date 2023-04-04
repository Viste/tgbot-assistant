from aiogram import Router, F

from tools.utils import config


def setup_routers() -> Router:
    from . import core

    router = Router()
    router.message.filter(F.chat.id != config.allowed_group)
    router.include_router(core.router)

    return router
