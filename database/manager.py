import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, NeuropunkPro, ChatMember

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
        logger.info(f"get_user: user_id={user_id}, user={user}")
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
        logger.info(f"get_course_user: user_id={user_id}, user={user}")
        return user

    async def create_course_user(self, user_id: int) -> NeuropunkPro:
        user = NeuropunkPro(telegram_id=user_id,)
        self.session.add(user)
        await self.session.commit()
        return user

    async def is_course_subscription_active(self, user_id: int) -> bool:
        user = await self.get_course_user(user_id)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            return True
        return False

    async def get_active_course_emails(self) -> list[str]:
        stmt = select(NeuropunkPro.email).where(NeuropunkPro.subscription_end > datetime.utcnow(), NeuropunkPro.email.isnot(None))
        result = await self.session.execute(stmt)
        emails = [email[0] for email in result.all() if email[0] is not None]
        return emails

    async def create_chat_member(self, telegram_id: int, telegram_username: str, chat_name: str, chat_id: int, status: str = 'active') -> ChatMember:
        stmt = select(ChatMember).where(ChatMember.telegram_id == telegram_id, ChatMember.chat_id == chat_id)
        result = await self.session.execute(stmt)
        chat_member = result.scalar_one_or_none()

        if chat_member:
            updated = False
            if chat_member.telegram_username != telegram_username:
                chat_member.telegram_username = telegram_username
                updated = True
            if chat_member.chat_name != chat_name:
                chat_member.chat_name = chat_name
                updated = True
            if chat_member.status != status:
                chat_member.status = status
                updated = True

            if updated:
                await self.session.commit()
                logging.info(f"Chat member updated: telegram_id={telegram_id}, chat_name={chat_name}")
            else:
                logging.info(f"Chat member already exists with the same data: telegram_id={telegram_id}, chat_name={chat_name}")
            return chat_member
        else:
            # Если член чата не существует, создаем новую запись
            chat_member = ChatMember(telegram_id=telegram_id, telegram_username=telegram_username, chat_name=chat_name, chat_id=chat_id, status=status)
            self.session.add(chat_member)
            await self.session.commit()
            logging.info(f"New chat member created: telegram_id={telegram_id}, chat_name={chat_name}")
            return chat_member

    async def update_chat_member_status(self, telegram_id: int, new_status: str) -> None:
        stmt = select(ChatMember).where(ChatMember.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        chat_member = result.scalar_one_or_none()
        if chat_member:
            chat_member.status = new_status
            await self.session.commit()
            logger.info(f"Chat member status updated: telegram_id={telegram_id}, new_status={new_status}")
        else:
            logger.info(f"No chat member found for telegram_id={telegram_id} to update status")

    async def extend_subscription(self, user_id: int, is_course: bool = False) -> None:
        if is_course:
            user = await self.get_course_user(user_id)
        else:
            user = await self.get_user(user_id)

        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            user.subscription_end += timedelta(days=30)
            await self.session.commit()
            logging.info(f"Subscription extended for user_id={user_id}, new_end_date={user.subscription_end}")
        else:
            logging.info(f"No active subscription found for user_id={user_id} to extend")
