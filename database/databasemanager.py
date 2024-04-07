import logging
from datetime import datetime, timedelta
from typing import Optional, Type

from sqlalchemy import select, inspect, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from werkzeug.security import generate_password_hash

from database.models import ChatMember, Config, NeuropunkPro, Customer

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

    async def create_chat_member(self, telegram_id: int, telegram_username: str, chat_name: str, chat_id: int,
                                 status: str = 'active') -> ChatMember:
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
                logging.info(
                    f"Chat member already exists with the same data: telegram_id={telegram_id}, chat_name={chat_name}")
            return chat_member
        else:
            # Если член чата не существует, создаем новую запись
            chat_member = ChatMember(telegram_id=telegram_id, telegram_username=telegram_username, chat_name=chat_name,
                                     chat_id=chat_id, status=status)
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

    async def extend_subscription(self, user_id: int, model: Type[DeclarativeMeta]) -> None:
        user = await self.get_user(user_id, model)
        if user and user.subscription_end and user.subscription_end > datetime.utcnow():
            user.subscription_end += timedelta(days=30)
            await self.session.commit()
            logger.info(f"Subscription extended for user_id={user_id}, new_end_date={user.subscription_end}")
        else:
            logger.info(f"No active subscription found for user_id={user_id} to extend")

    async def get_all_chat_member_telegram_ids(self) -> list[int]:
        stmt = select(ChatMember.telegram_id).distinct()
        result = await self.session.execute(stmt)
        telegram_ids = [telegram_id[0] for telegram_id in result.all()]
        logger.info(f"Retrieved {len(telegram_ids)} unique telegram_ids from chat_members")
        return telegram_ids

    async def is_user_banned(self, telegram_id: int) -> bool:
        result = await self.session.execute(select(ChatMember.banned).where(ChatMember.telegram_id == telegram_id))
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

    async def create_customer(self, email: str, telegram_id: int, password: str, username: str, message) -> None:
        # Проверяем, существует ли уже пользователь с таким email или Telegram ID
        stmt = select(Customer).where(or_(Customer.email == email, Customer.telegram_id == str(telegram_id)))
        result = await self.session.execute(stmt)
        user_exists = result.scalar_one_or_none()

        if user_exists:
            await message.answer("Пользователь с таким email или Telegram ID уже существует.")
            return

        try:
            new_user = Customer(email=email, telegram_id=str(telegram_id), password=generate_password_hash(password),
                                username=username, allowed_courses='', is_moderator=False, is_admin=False, is_banned=False)
            self.session.add(new_user)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            await message.answer("Ошибка при создании пользователя.")