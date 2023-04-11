from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery


def _is_working() -> bool:
    pass
    # TODO: check datetame seted by pavel and return True/False


class WeekendMessageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Если не выключен и по датам все ок продолжаем
        if not _is_working():
            return await handler(event, data)
        # В противном случае просто вернётся None и обработка прекратится


class WeekendCallbackMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Если не выключен и по датам все ок продолжаем
        if not _is_working():
            return await handler(event, data)
        # В противном случае отвечаем самостоятельно и прекращаем дальнейшую обработку
        await event.answer(
            "Сейчас демки не принимаю!",
            show_alert=True
        )
        return
