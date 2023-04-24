import logging

from aiogram import types, F, Router, flags
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext

from tools.ai_tools import OpenAI
from tools.states import Text
from tools.utils import config, trim_name, split_into_chunks

logger = logging.getLogger("__name__")
router = Router()
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id.in_(config.allowed_groups))
openai = OpenAI()


@flags.chat_action("typing")
@router.message(F.text.startswith("@cyberpaperbot"))
async def ask(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        chat_id = message.chat.id
        trimmed = trim_name(message.text)

        # Generate response
        replay_text, total_tokens = await openai.get_resp(trimmed, chat_id)

        if replay_text:
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

        if openai.show_tokens or chat_id == -1001582049557:
            tokens_text = f"💰 Использовано Токенов: {total_tokens}"
            await message.reply(tokens_text, parse_mode=None)


@flags.chat_action("typing")
@router.message(Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask(message: types.Message) -> None:
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        logging.info("%s", message)
        chat_id = message.chat.id
        trimmed = trim_name(message.text)

        # Generate response
        replay_text, total_tokens = await openai.get_resp(trimmed, chat_id)
        if replay_text:
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

        if openai.show_tokens or chat_id == -1001582049557:
            tokens_text = f"💰 Использовано Токенов: {total_tokens}"
            await message.reply(tokens_text, parse_mode=None)


@router.message(Command(commands="help"))
async def info_user(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Бот написан специально для Neuropunk Академии!\n" \
               "Хочешь со мной поговорить? Обратись ко мне через никнейм: @cyberpaperbot <твой вопрос> \n" \
               "Нужно полностью описать свою проблему и рассказать о своем опыте. не баловаться.\n" \
               "Мы внимательно наблюдаем за вами и тестируем «Кибер Папера» в режиме 24 на 7, поэтому используйте его грамотно. Мы за это платим.\n" \
               "Чтобы прислать мне демку для эфира Neuropunk Академии, напиши мне в ЛС /start" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)
