import logging
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from database.models import CourseParticipant

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

    async def add_course_participant(self, email: str, course_name: str, telegram_nickname: str) -> Optional[CourseParticipant]:
        try:
            new_participant = CourseParticipant(email=email, course_name=course_name, telegram_nickname=telegram_nickname)
            self.session.add(new_participant)
            await self.session.commit()
            logging.info(f"Added new course participant: {email} for course {course_name}")
            return new_participant
        except IntegrityError:
            await self.session.rollback()
            logging.error(f"Failed to add course participant: {email} for course {course_name}. The email might already be registered for this course.")
            return None

    async def get_emails_by_course(self, course_name: str) -> List[str]:
        stmt = select(CourseParticipant.email).where(CourseParticipant.course_name == course_name)
        result = await self.session.execute(stmt)
        emails = result.scalars().all()
        logging.info(f"Retrieved emails for course {course_name}: {emails}")
        return emails
