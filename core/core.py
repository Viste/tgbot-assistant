import logging
import os

from aiogram import types, F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from tools.ai import OpenAI
from tools.states import Text
from tools.utils import config
from tools.utils import trim_name

logger = logging.getLogger("__name__")
router = Router()

openai = OpenAI()


@router.message(F.text.startswith("@naastyyaabot"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        trimmed = trim_name(message.text)

        # Generate response
        replay_text = openai.send_turbo(trimmed)
        try:
            await message.reply(replay_text, parse_mode=None)
        except ValueError as err:
            logging.info('error: %s', err)
            text = err
            await message.reply(text, parse_mode=None)


@router.message(Text.get)
async def process_ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.result)
    logging.info("%s", message)


@router.message(Command(commands="help"))
async def info(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Бот написан специально для Neuropunk Академии!\n" \
               "Хочешь со мной поговорить? Обратись ко мне через никнейм: @cyberpaperbot <твой вопрос> \n" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)
