import html
import logging
from datetime import datetime

from aiogram import types, F, Router, flags
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fluent.runtime import FluentLocalization

from core.helpers.tools import send_reply, reply_if_banned
from database.models import User
from tools.ai.user_dialogue import OpenAIDialogue
from tools.states import Dialogue
from tools.utils import split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({'private'}))
openai = OpenAIDialogue()


async def has_active_subscription(user_id: int, session: AsyncSession) -> bool:
    result = await session.execute(select(User).filter(User.telegram_id == user_id))
    subscription = result.scalars().one_or_none()

    if subscription and subscription.subscription_status == 'active' and subscription.subscription_start and subscription.subscription_end:
        now = datetime.now()
        if subscription.subscription_start <= now <= subscription.subscription_end:
            return True
    return False


@flags.chat_action(action="typing", interval=5, initial_sleep=2)
@router.message(F.text.startswith("Папер!"))
async def start_dialogue(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization) -> None:
    await state.update_data(chatid=message.chat.id)
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        if not await has_active_subscription(uid, session):
            kb = [
                [
                    types.InlineKeyboardButton(text="Купить подписку", callback_data="buy_subscription")
                ],
            ]
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
            await message.answer("У вас нет активной подписки. Пожалуйста, купите подписку, чтобы продолжить.",
                                 reply_markup=keyboard)
            print(uid)
            return

        logging.info("%s", message)
        text = html.escape(message.text)
        escaped_text = text.strip('Папер! ')

        await state.set_state(Dialogue.get)
        replay_text, total_tokens = await openai.get_resp(escaped_text, uid, session)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            if index == 0:
                await send_reply(message, chunk)


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(Dialogue.get, F.text)
async def process_dialogue(message: types.Message, session: AsyncSession, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logging.info("%s", message)
        text = html.escape(message.text)

        replay_text, total_tokens = await openai.get_resp(text, uid, session)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            if index == 0:
                await send_reply(message, chunk)
