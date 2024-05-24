import logging
from datetime import datetime, timedelta
from typing import Optional, Type

from sqlalchemy import select, inspect, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from werkzeug.security import generate_password_hash

from database.models import Config, NeuropunkPro, Customer, CourseRegistration, Course

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_subscription_active(self, user_id: int, model: Type[DeclarativeMeta]) -> bool:
        user = await self.get_user(user_id, model)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            return True
        return False

    async def get_user(self, user_id: int, model: Type[DeclarativeMeta]) -> Optional[DeclarativeMeta]:
        stmt = select(model).where(model.telegram_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        logger.info(f"get_user: user_id={user_id}, user={user}")
        return user

    async def create_user(self, user_data: dict, model: Type[DeclarativeMeta]) -> DeclarativeMeta:
        user = model(**user_data)
        self.session.add(user)
        await self.session.commit()
        return user

    async def get_active_emails(self, model: Type[DeclarativeMeta]) -> list[str]:
        if 'subscription_end' in inspect(model).columns:
            stmt = select(model.email).where(model.subscription_end > datetime.utcnow(),
                                             model.email.isnot(None))
            result = await self.session.execute(stmt)
            emails = [email[0] for email in result.all() if email[0] is not None]
            return emails
        else:
            stmt = select(model.email).where(model.email.isnot(None))

        result = await self.session.execute(stmt)
        emails = [email[0] for email in result.all() if email[0] is not None]
        return emails

    async def extend_subscription(self, user_id: int, model: Type[DeclarativeMeta]) -> None:
        user = await self.get_user(user_id, model)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            user.subscription_end += timedelta(days=30)
            await self.session.commit()
            logger.info(f"Subscription extended for user_id={user_id}, new_end_date={user.subscription_end}")
        else:
            logger.info(f"No active subscription found for user_id={user_id} to extend")

    async def get_all_customer_telegram_ids(self) -> list[int]:
        stmt = select(Customer.telegram_id).distinct()
        result = await self.session.execute(stmt)
        telegram_ids = [int(telegram_id[0]) for telegram_id in result.all()]
        logger.info(f"Retrieved {len(telegram_ids)} unique telegram_ids from customers")
        return telegram_ids

    async def is_user_banned(self, telegram_id: int) -> bool:
        result = await self.session.execute(select(Customer.is_banned).where(Customer.telegram_id == telegram_id))
        chat_member_bans = result.scalars().all()
        return any(chat_member_bans)

    async def get_subscription_end_date(self, user_id: int, model: Type[DeclarativeMeta]) -> Optional[datetime]:
        user = await self.get_user(user_id, model)
        if user:
            return user.subscription_end
        return None

    async def get_config_value(self, key_name: str) -> Optional:
        stmt = select(Config).where(Config.key_name == key_name)
        result = await self.session.execute(stmt)
        config_entry = result.scalar_one_or_none()
        if config_entry:
            return config_entry.value
        else:
            return None

    async def delete_neuropunk_pro_user(self, telegram_id: int) -> None:
        stmt = select(NeuropunkPro).where(NeuropunkPro.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user_to_delete = result.scalar_one_or_none()

        if user_to_delete:
            await self.session.delete(user_to_delete)
            await self.session.commit()
            logger.info(f"NeuropunkPro user deleted: telegram_id={telegram_id}")
        else:
            logger.info(f"No NeuropunkPro user found with telegram_id={telegram_id} to delete")

    async def create_customer(self, email: str, telegram_id: int, password: str, name: str) -> str:
        # Проверяем, существует ли уже пользователь с таким email или Telegram ID
        stmt = select(Customer).where(or_(Customer.email == email, Customer.telegram_id == str(telegram_id)))
        result = await self.session.execute(stmt)
        user_exists = result.scalar_one_or_none()

        if user_exists:
            return "Пользователь с таким email или Telegram ID уже существует."

        try:
            new_user = Customer(email=email, telegram_id=str(telegram_id), password=generate_password_hash(password), username=name,
                                allowed_courses='academy', is_moderator=False, is_admin=False, is_banned=False)
            self.session.add(new_user)
            await self.session.commit()
            return ("Вы успешно зарегистрированы! Логин это твой username в телеграмм!\n"
                    "Если username не установлен, используй свой ник из email(та часть что до собаки)\n"
                    "Например: dave@mail.ru - твой логин будет dave")
        except IntegrityError:
            await self.session.rollback()
            return "Ошибка при создании пользователя."

    async def add_course_to_customer(self, telegram_id: int, course_shortname: str) -> str:
        # Находим пользователя по telegram_id
        stmt_customer = select(Customer).where(Customer.telegram_id == str(telegram_id))
        result_customer = await self.session.execute(stmt_customer)
        customer = result_customer.scalar_one_or_none()

        if not customer:
            return "Пользователь не найден."

        # Находим курс по короткому имени
        stmt_course = select(Course).where(Course.short_name == course_shortname)
        result_course = await self.session.execute(stmt_course)
        course = result_course.scalar_one_or_none()

        if not course:
            return "Курс не найден."

        # Проверяем, зарегистрирован ли уже пользователь на курс
        stmt_reg = select(CourseRegistration).where(
            CourseRegistration.customer_id == customer.id,
            CourseRegistration.course_id == course.id
        )
        result_reg = await self.session.execute(stmt_reg)
        registration = result_reg.scalar_one_or_none()

        if registration:
            return "Курс уже добавлен к пользователю."

        # Добавляем новую регистрацию
        new_registration = CourseRegistration(customer_id=customer.id, course_id=course.id)
        self.session.add(new_registration)
        await self.session.commit()

        return "Курс успешно добавлен."

    async def remove_course_from_customer(self, telegram_id: int, course_shortname: str) -> str:
        # Находим пользователя по telegram_id
        stmt_customer = select(Customer).where(Customer.telegram_id == str(telegram_id))
        result_customer = await self.session.execute(stmt_customer)
        customer = result_customer.scalar_one_or_none()

        if not customer:
            return "Пользователь не найден."

        # Находим курс по короткому имени
        stmt_course = select(Course).where(Course.short_name == course_shortname)
        result_course = await self.session.execute(stmt_course)
        course = result_course.scalar_one_or_none()

        if not course:
            return "Курс не найден."

        # Находим регистрацию пользователя на курс
        stmt_reg = select(CourseRegistration).where(CourseRegistration.customer_id == customer.id, CourseRegistration.course_id == course.id)
        result_reg = await self.session.execute(stmt_reg)
        registration = result_reg.scalar_one_or_none()

        if not registration:
            return "Регистрация на курс не найдена."

        # Удаляем регистрацию
        await self.session.delete(registration)
        await self.session.commit()

        return "Регистрация на курс успешно удалена."
