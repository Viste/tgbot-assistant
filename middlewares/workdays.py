import logging
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Calendar
from main import engine

logger = logging.getLogger("__name__")

session = AsyncSession(bind=engine)


class WorkdaysMessageMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:
        now = datetime.now()
        result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
        close_date = result.scalar_one()
        # Если не выключен и по датам все ок продолжаем
        if close_date.end_time is not None or now < close_date.end_time:
            return await handler(event, data)
        # В противном случае просто вернётся None и обработка прекратится
