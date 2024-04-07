import logging
from typing import Callable, Optional, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User, Chat, Message

from database.databasemanager import DatabaseManager

logger = logging.getLogger(__name__)


class BasicMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(self, handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: dict[str, Any]) -> Optional[Any]:
        user_id: Optional[User] = data.get("event_from_user")
        chat_id: Optional[Chat] = data.get("event_chat")
        event: Message
        result = await handler(event, data)
        logger.info("CommonTasksMiddleware called User: %s Chat: %s Event: %s", user_id, chat_id, event)
        if user_id is None or chat_id is None or user_id.is_bot:
            return await handler(event, data)

        l10n = data.get('l10n')
        async with self.session_maker() as session:
            data['session'] = session
            user_manager = DatabaseManager(session)

            if await user_manager.is_user_banned(event.from_user.id):
                await event.reply(l10n.format_value("you-were-banned-error"))

        return result
