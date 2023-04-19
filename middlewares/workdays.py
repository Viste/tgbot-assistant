import logging
from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

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
        try:
            result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
            close_date = result.scalar_one()
        except NoResultFound:
            close_date = None
        # Если не выключен и по датам все ок продолжаем
        if close_date is None or close_date.end_time is not None or now < close_date.end_time:
            return await handler(event, data)
        # В противном случае просто вернётся None и обработка прекратится
