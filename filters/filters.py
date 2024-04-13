from aiogram import types
from aiogram.filters import BaseFilter

from core.helpers.tools import ChatState

state = ChatState()


class IsActiveChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == state.active_chat and (
                not message.chat.is_forum or message.message_thread_id == state.thread_id)


class ForumFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return (
            message.chat.type in {'group', 'supergroup'} and
            (
                (message.chat.id == -1001922960346 and message.message_thread_id == 12842) or
                (message.chat.id == -1002040950538 and message.message_thread_id == 305) or
                (message.chat.id == -1002094481198 and message.message_thread_id == 58) or
                (message.chat.id == -1001921488615 and message.message_thread_id == 9078) or
                (message.chat.id == -1002085114945 and message.message_thread_id == 28) or
                (message.chat.id == -1002021584528 and message.message_thread_id == 52) or
                (message.chat.id == -1002117966241 and message.message_thread_id == 36)
            )
        )


class ChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return (
            message.chat.type in {'group', 'supergroup'} and ((message.chat.id == -1001647523732) or
                                                              (message.chat.id == -1001700103389) or
                                                              (message.chat.id == -1001537420102) or
                                                              (message.chat.id == -1002004353654) or
                                                              (message.chat.id == -1001170569681) or
                                                              (message.chat.id == -1002021584528) or
                                                              (message.chat.id == -1002117966241)))


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
