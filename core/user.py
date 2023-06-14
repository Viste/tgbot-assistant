import html
import logging
from datetime import datetime

from aiogram import types, F, Router, flags
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from tools.ai.user_dialogue import OpenAIDialogue
from tools.states import Dialogue
from tools.utils import config, split_into_chunks

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
async def start_dialogue(message: types.Message, state: FSMContext, session: AsyncSession) -> None:
    uid = message.from_user.id
    await state.update_data(chatid=message.chat.id)
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
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
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logging.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + str(err), parse_mode=None)
                except Exception as error:
                    logging.info('Last exception from Core: %s', error)
                    await message.reply(str(error), parse_mode=None)


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(Dialogue.get, F.text)
async def process_dialogue(message: types.Message, session: AsyncSession) -> None:
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        text = html.escape(message.text)

        # Generate response
        replay_text, total_tokens = await openai.get_resp(text, uid, session)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logging.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + str(err), parse_mode=None)
                except Exception as error:
                    logging.info('Last exception from Core: %s', error)
                    await message.reply(str(error), parse_mode=None)
