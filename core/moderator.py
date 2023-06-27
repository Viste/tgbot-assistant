import html
import logging

from aiogram import types, F, Router, flags

from core.helpers.tools import reply_if_banned
from tools.ai.moderator import Moderator
from tools.utils import split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_(-1001647523732))
moderator = Moderator()


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(F.text)
async def process_moderating(message: types.Message) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid):
        return
    else:
        logging.info("%s", message)
        text = html.escape(message.text)

        replay_text = await moderator.get_resp_mod(uid, text)
        chunks = split_into_chunks(replay_text)
        # for index, chunk in enumerate(chunks):
        # if index == 0:
        # await send_reply(message, chunk)
