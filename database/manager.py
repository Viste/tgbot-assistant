import logging
from typing import Optional, List, Dict

from sqlalchemy import select, insert
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

logger = logging.getLogger(__name__)


class UserManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[User]:
        stmt = select(User).options(joinedload(User.history)).where(user_id == User.telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        logging.info(f"get_user: user_id={user_id}, user={user}")
        return user

    async def create_user(self, user_id: int) -> User:
        user = User(telegram_id=user_id)
        self.session.add(user)
        await self.session.commit()
        return user

    async def update_user_history_and_commit(self, user: User, history: List[Dict[str, str]]) -> None:
        user.history = history
        self.session.add(user)  # Add the user object to the session
        await self.session.commit()
        logging.info(f"User history updated in database for user_id={user.telegram_id}, history={history}")

    async def upsert_user(self, user: User) -> User:
        stmt = insert(User).values(
            telegram_id=user.telegram_id,
            system_message=user.system_message
        ).on_duplicate_key_update(
            system_message=user.system_message
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return user
