import logging

from aiogram import types, F, Router, flags
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import reply_if_banned
from database.manager import UserManager
from core.helpers.tools import EmailChatState
from tools.utils import gmail_patt, check
from core.helpers.tools import active_chats

router = Router()
logger = logging.getLogger(__name__)
router.message.filter(F.chat.type.in_({'group', 'supergroup'}))
state = EmailChatState()


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(F.content_type.in_({'text'}))
async def process_new_email(message: types.Message, l10n: FluentLocalization, session: AsyncSession) -> None:
    manager = UserManager(session)
    uid = message.from_user.id
    nickname = message.from_user.first_name + " " + (message.from_user.last_name if message.from_user.last_name else "")
    email = message.text
    if await reply_if_banned(message, uid, l10n):
        return
    if message.chat.is_forum is True:
        if message.chat.id in active_chats and message.message_thread_id == active_chats[message.chat.id]:
            if check(email, gmail_patt):
                await manager.add_course_participant(email=email, course_name=message.chat.title, telegram_nickname=nickname)
        else:
            return

    else:
        if message.chat.id in active_chats:
            if check(email, gmail_patt):
                await manager.add_course_participant(email=email, course_name=message.chat.title, telegram_nickname=nickname)
        else:
            return
