from aiogram import types
from aiogram.filters import BaseFilter

from core.helpers.tools import ChatState

state = ChatState()


class IsActiveChatFilter(BaseFilter):
    async def __call__(self, message: types.Message) -> bool:
        return message.chat.id == state.active_chat and (
                not message.chat.is_forum or message.message_thread_id == state.thread_id)
