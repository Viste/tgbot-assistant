import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, NeuropunkPro

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_subscription_active(self, user_id: int) -> bool:
        user = await self.get_user(user_id)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            return True
        return False

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

    async def get_course_user(self, user_id: int) -> Optional[NeuropunkPro]:
        stmt = select(NeuropunkPro).where(NeuropunkPro.telegram_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        logging.info(f"get_course_user: user_id={user_id}, user={user}")
        return user

    async def create_course_user(self, user_id: int, telegram_username: str, user_email: str = None) -> NeuropunkPro:
        user = NeuropunkPro(telegram_id=user_id, telegram_username=telegram_username, user_email=user_email)
        self.session.add(user)
        await self.session.commit()
        return user

    async def is_course_subscription_active(self, user_id: int) -> bool:
        user = await self.get_course_user(user_id)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            return True
        return False
