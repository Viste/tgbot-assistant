from aiogram import types
from aiogram.filters import BaseFilter

from core.helpers.tools import ChatState, ALLOWED_CHAT_IDS, ALLOWED_CHAT_THREAD_IDS

state = ChatState()


class IsActiveChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == state.active_chat and (not message.chat.is_forum or message.message_thread_id == state.thread_id)


class ForumFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in {'group', 'supergroup'} and (message.chat.id in ALLOWED_CHAT_THREAD_IDS and message.message_thread_id in ALLOWED_CHAT_THREAD_IDS[message.chat.id])


class ChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in {'group', 'supergroup'} and message.chat.id in ALLOWED_CHAT_IDS


class PrivateFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type == 'private'


class IsAdmin(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        # Список админов
        admin_ids = {'58800377', '273896204', '910007939', '350493882', '824834852', '766871228'}

        # Проверяем, что сообщение в приватном чате
        is_private = message.chat.type == 'private'

        # Проверяем, является ли пользователь админом
        is_admin = str(message.from_user.id) in admin_ids

        # Возвращаем True, если сообщение в приватном чате и пользователь является админом
        return is_private and is_admin
