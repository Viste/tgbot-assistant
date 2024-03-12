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
                (message.chat.id == -1001921488615 and message.message_thread_id == 9078)
            )
        )


class ChatFilter(BaseFilter):
    def __init__(self, allowed_groups):
        self.allowed_groups = allowed_groups

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in {'group', 'supergroup'} and message.chat.id in self.allowed_groups


class PrivateFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type == 'private'


class SubscribeChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return (
            message.chat.type in {'group', 'supergroup'} and
            message.chat.id == -1001814931266 and
            message.message_thread_id == 5472
        )
