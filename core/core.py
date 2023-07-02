import html
import logging

from aiogram import types, F, Router, flags
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import send_reply, reply_if_banned
from tools.ai.ai_tools import OpenAI
from tools.states import Text
from tools.utils import config, split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_(config.allowed_groups))
openai = OpenAI()


@flags.chat_action("typing")
@router.message(F.text.startswith("@cyberpaperbot"))
async def ask(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(Text.get)

    uid = message.from_user.id
    if await reply_if_banned(message, uid):
        return

    logging.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('@cyberpaperbot ')

    replay_text, total_tokens = await openai.get_resp(escaped_text, uid, session)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@flags.chat_action("typing")
@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask(message: types.Message, session: AsyncSession) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid):
        return

    logging.info("%s", message)
    text = html.escape(message.text)

    replay_text, total_tokens = await openai.get_resp(text, uid, session)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)
