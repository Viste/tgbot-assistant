import logging
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Calendar

logger = logging.getLogger("__name__")

session = AsyncSession()


def _is_working() -> bool:
    now = datetime.now()
    result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
    close_date = result.scalar_one()

    if close_date.end_time is None or now > close_date.end_time:
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
