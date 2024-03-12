import html
import logging
import os

from aiogram import types, F, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import send_reply, handle_exception
from database.manager import UserManager
from filters.filters import ChatFilter, ForumFilter, PrivateFilter, SubscribeChatFilter
from tools.ai.ai_tools import OpenAI, OpenAIDialogue
from tools.ai.listener_tools import OpenAIListener, Audio
from tools.states import Text, Dialogue, DAImage, Demo
from tools.utils import split_into_chunks, config

router = Router()
logger = logging.getLogger(__name__)
openai_listener = OpenAIListener()
openai = OpenAI()
openai_dialogue = OpenAIDialogue()
audio = Audio()


@router.message(ChatFilter(config.allowed_groups), (F.text.regexp(r"[\s\S]+?@cyberpaperbot[\s\S]+?") | F.text.startswith("@cyberpaperbot")))
async def ask_chat(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)

    logger.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('@cyberpaperbot')

    replay_text = await openai.get_resp(escaped_text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(ChatFilter(config.allowed_groups), Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask_chat(message: types.Message) -> None:
    logger.info("%s", message)
    text = html.escape(message.text)

    replay_text = await openai.get_resp(text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(ForumFilter(), (F.text.regexp(r"[\s\S]+?@cyberpaperbot[\s\S]+?") | F.text.startswith("@cyberpaperbot")))
async def ask_forum(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)

    logger.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('@cyberpaperbot ')

    replay_text = await openai.get_resp(escaped_text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(ForumFilter(), Text.get, F.reply_to_message.from_user.is_bot)
async def process_ask_forum(message: types.Message) -> None:
    logger.info("%s", message)
    text = html.escape(message.text)

    replay_text = await openai.get_resp(text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(PrivateFilter(), (F.text.regexp(r"[\s\S]+?киберпапер[\s\S]+?") | F.text.startswith("киберпапер")))
async def start_dialogue(message: types.Message, state: FSMContext, session: AsyncSession,
                         l10n: FluentLocalization) -> None:
    await state.update_data(chatid=message.chat.id)
    user_manager = UserManager(session)
    if not await user_manager.is_subscription_active(message.from_user.id):
        kb = [[types.InlineKeyboardButton(text=l10n.format_value("buy-sub"), callback_data="buy_subscription")], ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(l10n.format_value("error-sub-not-active"), reply_markup=keyboard)
        current_state = await state.get_state()
        logger.info("current state %r", current_state)
        return

    logger.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('киберпапер ')

    await state.set_state(Dialogue.get)
    replay_text = await openai_dialogue.get_resp(escaped_text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(PrivateFilter(), Dialogue.get, F.text)
async def process_dialogue(message: types.Message) -> None:
    logger.info("%s", message)
    text = html.escape(message.text)
    replay_text = await openai_dialogue.get_resp(text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(PrivateFilter(), F.text.startswith("нарисуй, "), F.from_user.id.in_(config.admins))
async def paint(message: types.Message, state: FSMContext) -> None:
    logger.info("Message: %s", message)
    await state.set_state(DAImage.get)
    text = html.escape(message.text)
    escaped_text = text.strip('нарисуй, ')
    result = await openai_dialogue.send_dalle(escaped_text)
    logger.info("Response from DaLLe: %s", result)
    try:
        photo = result
        await message.reply_photo(types.URLInputFile(photo))
    except Exception as err:
        await handle_exception(message, err)


@router.message(PrivateFilter(), DAImage.get)
async def process_paint(message: types.Message, state: FSMContext) -> None:
    await state.set_state(DAImage.result)
    logger.info("%s", message)


@router.message(PrivateFilter(), F.audio, ~StateFilter(Demo.get))
async def handle_audio(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot,
                       l10n: FluentLocalization):
    user_manager = UserManager(session)

    uid = message.from_user.id
    await state.update_data(chatid=message.chat.id)

    if not await user_manager.is_subscription_active(uid):
        kb = [[types.InlineKeyboardButton(text=l10n.format_value("buy-sub"), callback_data="buy_subscription")], ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(l10n.format_value("error-sub-not-active"), reply_markup=keyboard)
        return

    file_path = f"/app/tmp/{str(uid)}.mp3"
    file_info = await bot.get_file(message.audio.file_id)
    file_data = file_info.file_path
    await bot.download_file(file_data, file_path)

    result = await audio.process_audio_file(file_path)
    os.remove(file_path)
    replay_text = await openai_listener.get_resp_listen(uid, result)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        try:
            if index == 0:
                await message.reply(chunk, parse_mode=None)
        except Exception as err:
            try:
                logger.info('From try in for index chunks: %s', err)
                await message.reply(chunk + str(err), parse_mode=None)
            except Exception as error:
                logger.info('Last exception from Core: %s', error)
                await message.reply(str(error), parse_mode=None)


@router.message(Command(commands="course_register"), SubscribeChatFilter())
async def reg_course(message: types.Message, state: FSMContext, session: AsyncSession,
                     l10n: FluentLocalization) -> None:
    await state.update_data(chatid=message.chat.id)
    user_manager = UserManager(session)
    uid = message.from_user.id
    if not await user_manager.is_course_subscription_active(uid):
        kb = [[types.InlineKeyboardButton(text=l10n.format_value("buy-sub-course"), callback_data="buy_course")], ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.reply(l10n.format_value("button-action"), reply_markup=keyboard)
        current_state = await state.get_state()
        logger.info("current state %r", current_state)
        return


@router.message(Command(commands="help"))
async def info_user(message: types.Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("help"))
