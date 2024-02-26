import html
import logging

from aiogram import types, F, Router, flags
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from aiogram.filters import Command

from core.helpers.tools import send_reply, reply_if_banned
from tools.ai.ai_tools import OpenAI
from tools.states import Text
from tools.utils import split_into_chunks

router = Router()

logger = logging.getLogger(__name__)
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_({-1001922960346}) & F.message_thread_id.in_({12842}) | F.chat.id.in_({-1002040950538}) & F.message_thread_id.in_({305})
                      | F.chat.id.in_({-1002094481198}) & F.message_thread_id.in_({58}))


@flags.chat_action("typing")
@router.message(F.text.startswith("@cyberpaperbot"))
async def ask(message: types.Message, state: FSMContext, l10n: FluentLocalization) -> None:
    await state.set_state(Text.get)
    openai = OpenAI()

    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return

    logging.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('@cyberpaperbot ')

    replay_text, total_tokens = await openai.get_resp(escaped_text, uid)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@flags.chat_action("typing")
@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask(message: types.Message, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    openai = OpenAI()

    if await reply_if_banned(message, uid, l10n):
        return

    logging.info("%s", message)
    text = html.escape(message.text)

    replay_text, total_tokens = await openai.get_resp(text, uid)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(Command(commands="help"))
async def info_user(message: types.Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("help"))
