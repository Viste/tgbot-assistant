import logging

from aiogram import types, F, Router, flags
from aiogram.filters.command import Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

from tools.ai_tools import OpenAI
from tools.states import Text
from tools.utils import config, trim_name, split_into_chunks

logger = logging.getLogger("__name__")
router = Router()

openai = OpenAI()


@router.message(F.text.startswith("@cyberpaperbot"), F.chat.id.in_(config.allowed_groups), F.chat.type.in_({'group', 'supergroup'}))
@flags.chat_action("typing")
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
        print(await openai.get_response(query=trimmed, user_id=uid))
        replay_text, total_tokens = await openai.get_response(query=trimmed, user_id=uid)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
            except Exception as err:
                try:
                    await message.reply(chunk + err, parse_mode=None)
                except Exception as error:
                    logging.info('error: %s', error)
                    await message.reply(error, parse_mode=None)


@router.message(Text.get, F.reply_to_message.from_user.is_bot, F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_(config.allowed_groups))
@flags.chat_action("typing")
async def process_ask(message: types.Message) -> None:
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        trimmed = trim_name(message.text)

        # Generate response
        print(await openai.get_response(query=trimmed, user_id=uid))
        replay_text, total_tokens = await openai.get_response(query=trimmed, user_id=uid)
        chunks = split_into_chunks(replay_text)
        for index, chunk in enumerate(chunks):
            try:
                if index == 0:
                    await message.reply(chunk, parse_mode=None)
                    logging.info("%s", message)
            except Exception as err:
                try:
                    await message.reply(chunk + err, parse_mode=None)
                except Exception as error:
                    logging.info('error: %s', error)
                    await message.reply(error, parse_mode=None)


@router.message(Command(commands="help"), F.chat.id.in_(config.allowed_groups), F.chat.type.in_({'group', 'supergroup'}))
async def info(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Бот написан специально для Neuropunk Академии!\n" \
               "Хочешь со мной поговорить? Обратись ко мне через никнейм: @cyberpaperbot <твой вопрос> \n" \
               "Нужно полностью описать свою проблему и рассказать о своем опыте. не баловаться.\n" \
               "Мы внимательно наблюдаем за вами и тестируем «Кибер Папера» в режиме 24 на 7, поэтому используйте его грамотно. Мы за это платим.\n" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)


@router.message(F.chat.type.in_({'private'}), F.from_user.id.in_(config.admins), Command(commands="money"))
async def usage(message: types.Message):
    text = openai.get_money()
    await message.reply(text, parse_mode=None)
