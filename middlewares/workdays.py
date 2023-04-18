import logging
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from core.admin import end_date

logger = logging.getLogger("__name__")


def _is_working() -> bool:
    now = datetime.now()
    close_date = end_date[0]
    if len(end_date[0]) == 1:
        if close_date is None:
            return True
        elif isinstance(close_date, datetime):
            if now > close_date:
                return True
            else:
                return False
        else:
            raise TypeError("end_date must be a datetime.datetime object or None")
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
