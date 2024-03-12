from aiogram import BaseMiddleware, types
from aiogram.dispatcher.middlewares.error import CancelHandler

from core.helpers.tools import reply_if_banned, create_chat_member_for_message


class CommonTasksMiddleware(BaseMiddleware):
    def __init__(self, session_maker):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            l10n = data.get('l10n')
            async with self.session_maker() as session:
                data['session'] = session

                uid = event.from_user.id
                if await reply_if_banned(event, uid, l10n, session):
                    raise CancelHandler()

                await create_chat_member_for_message(event, session)

        return await handler(event, data)
