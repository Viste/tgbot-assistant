from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from core.admin import end_date


def _is_working() -> bool:
    now = datetime.now()
    close_date = end_date[0]
    if now > close_date:
        return True
    else:
        return False


class WorkdaysMessageMiddleware(BaseMiddleware):
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
