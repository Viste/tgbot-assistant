import logging
from typing import Optional

from sqlalchemy import select, insert
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

    async def create_user(self, user_id: int) -> User:
        user = User(telegram_id=user_id)
        self.session.add(user)
        await self.session.commit()
        return user

    async def upsert_user(self, user: User) -> User:
        stmt = insert(User).values(telegram_id=user.telegram_id, system_message=user.system_message).on_duplicate_key_update(system_message=user.system_message)
        await self.session.execute(stmt)
        await self.session.commit()
        return user
