import logging
import os

from aiogram import types, F, Router, flags
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.user import has_active_subscription
from main import paper
from tools.ai.listener_tools import OpenAIListener, Audio
from tools.utils import config, split_into_chunks

logger = logging.getLogger("__name__")
router = Router()
router.message.filter(F.chat.type.in_({'private'}))
openai = OpenAIListener()
audio = Audio()


@flags.chat_action(action="typing", interval=5, initial_sleep=2)
@router.message(F.audio)
async def handle_audio(message: types.Message, state: FSMContext, session: AsyncSession):
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
            await message.answer("У вас нет активной подписки. Пожалуйста, купите подписку, чтобы продолжить.", reply_markup=keyboard)
            return
    
        file_path = f"tmp/{str(uid)}.mp3"
        file_info = await paper.get_file(message.audio.file_id)
        file_data = file_info.file_path
        await paper.download_file(file_data, file_path)

        result = await audio.process_audio_file(file_path)
        os.remove(file_path)
        replay_text, total_tokens = await openai.get_resp_listen(uid, str(result))
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    logging.info('From try in for index chunks: %s', err)
                    await message.reply(chunk + err, parse_mode=None)
                except Exception as error:
                    logging.info('Last exception from Core: %s', error)
                    await message.reply(error, parse_mode=None)
