import json
import logging
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[User]:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        logging.info(f"get_user: user_id={user_id}, user={user}")
        return user

    async def create_user(self, telegram_id: int, system_message: str) -> User:
        new_user = User(telegram_id=telegram_id, system_message=system_message)
        self.session.add(new_user)
        await self.session.commit()
        return new_user

    async def update_user_system_message(self, user_id: int, new_system_message: str) -> None:
        stmt = (update(User).where(User.telegram_id == user_id).values(system_message=new_system_message))
        await self.session.execute(stmt)
        await self.session.commit()

    async def update_user_history(self, user_id: int, new_history: list) -> None:
        new_history_json = json.dumps(new_history, ensure_ascii=False)
        stmt = (update(User).where(User.telegram_id == user_id).values(history=new_history_json))
        await self.session.execute(stmt)
        await self.session.commit()
