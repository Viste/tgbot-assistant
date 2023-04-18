from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message

from core.admin import end_date


class WorkdaysMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        # If end_date is empty, treat it as if work is ongoing
        if not end_date:
            return await handler(event, data)
        # Otherwise, check the end date
        close_date = end_date[0]
        if close_date is None or isinstance(close_date, datetime) and datetime.now() > close_date:
            return await handler(event, data)

        # If the end date is in the future, stop processing
        return None
