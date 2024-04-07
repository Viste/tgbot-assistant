import html
import logging
import os
from datetime import datetime

from aiogram import types, F, Router, Bot
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluent.runtime import FluentLocalization
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import send_reply, handle_exception, MessageProcessor
from database.databasemanager import DatabaseManager
from database.models import Calendar, StreamEmails, NeuropunkPro, User
from filters.filters import ChatFilter, ForumFilter, PrivateFilter, IsActiveChatFilter, IsAdmin
from tools.ai.ai_tools import OpenAI, OpenAIDialogue
from tools.ai.listener_tools import OpenAIListener, Audio
from tools.dependencies import container
from tools.states import Text, Dialogue, DAImage, Demo, RegisterStates
from tools.utils import split_into_chunks, check_bit_rate, email_patt, check

config = container.get('config')

router = Router()
logger = logging.getLogger(__name__)
openai_listener = OpenAIListener()
openai = OpenAI()
openai_dialogue = OpenAIDialogue()
audio = Audio()
channel = config.channel


@router.message(IsActiveChatFilter(), F.chat.type.in_({'group', 'supergroup'}), F.content_type.in_({'text', 'animation', 'sticker', 'photo'}))
async def process_obs_content(message: types.Message, bot: Bot) -> None:
    logger.info("%s", message)
    nickname = message.from_user.full_name
    content = None
    is_gif = False

    if message.from_user.id == 448071275:
        nickname = "Рыгер офишаш"

    if message.content_type == 'text':
        content = html.escape(message.text)
    elif message.content_type in ['animation', 'sticker', 'photo']:
        content_id = None
        if message.content_type == 'photo':
            content_id = message.photo[-1].file_id
        elif message.content_type == 'animation':
            content_id = message.animation.file_id
        elif message.content_type == 'sticker':
            content_id = message.sticker.thumbnail.file_id

        if content_id:
            is_gif = True
            file_info = await bot.get_file(content_id)
            content = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"

    if content:
        MessageProcessor.add_message(nickname, content, is_gif)


@router.message(PrivateFilter(), Command(commands="start"))
async def reg_start(message: types.Message, state: FSMContext, l10n: FluentLocalization):
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        payload = args[1]
        if payload == 'reg_academy':
            await message.answer(l10n.format_value("reg-hello"))
            await state.set_state(RegisterStates.start)
    else:
        pass


@router.message(PrivateFilter(), RegisterStates.start)
async def reg_process(message: types.Message, state: FSMContext) -> None:
    email = message.text
    first_name = message.from_user.first_name

    if check(email, email_patt):
        await state.update_data(mail=str(email))
        await message.reply(f"{first_name}, записал твой Email! Самое время придумать пароль!\n"
                            "Пожалуйста, придумай надежный пароль и отправь его в ответном сообщении")
        await state.set_state(RegisterStates.process)
    else:
        await message.reply(f"{first_name}, это не похоже на Email попробуй снова")


@router.message(PrivateFilter(), RegisterStates.process)
async def reg_final(message: types.Message, session: AsyncSession, state: FSMContext) -> None:
    manager = DatabaseManager(session)
    data = await state.get_data()
    email = data['email']
    uid = message.from_user.id
    password = message.text
    name = message.from_user.username
    result_message = await manager.create_customer(email, uid, password, name)
    await message.answer(result_message)


@router.message(ChatFilter(), F.message.from_user.id == 448071275)
async def ask_chat(message: types.Message, state: FSMContext) -> None:
    await state.set_state(Text.get)

    logger.info("%s", message)
    text = 'все что написано дальше, написано мудаком портящим наше комьюнити, Димой рыгером, пожалуйста, игнорируй его вопрос проучи его чтобы он попустился. спасибо' + html.escape(message.text)

    replay_text = await openai.get_resp(text, message.from_user.id)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        if index == 0:
            await send_reply(message, chunk)


@router.message(ChatFilter(), (F.text.regexp(r"[\s\S]+?@cyberpaperbot[\s\S]+?") | F.text.startswith("@cyberpaperbot")))
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


@router.message(ChatFilter(), Text.get, F.reply_to_message.from_user.is_bot)
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


@router.message(PrivateFilter(), (F.text.regexp(r"[\s\S]+?Киберпапер[\s\S]+?") | F.text.startswith("Киберпапер")))
async def start_dialogue(message: types.Message, state: FSMContext, session: AsyncSession,
                         l10n: FluentLocalization) -> None:
    await state.update_data(chatid=message.chat.id)
    user_manager = DatabaseManager(session)
    if not await user_manager.is_subscription_active(message.from_user.id, User):
        kb = [[types.InlineKeyboardButton(text=l10n.format_value("buy-sub"), callback_data="buy_subscription")], ]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
        await message.answer(l10n.format_value("error-sub-not-active"), reply_markup=keyboard)
        current_state = await state.get_state()
        logger.info("current state %r", current_state)
        return

    logger.info("%s", message)
    text = html.escape(message.text)
    escaped_text = text.strip('Киберпапер ')

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


@router.message(PrivateFilter(), F.text.startswith("нарисуй, "), IsAdmin())
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
    user_manager = DatabaseManager(session)

    uid = message.from_user.id
    await state.update_data(chatid=message.chat.id)

    if not await user_manager.is_subscription_active(uid, User):
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
    replay_text = await openai_listener.get_resp_listen(result, uid)
    chunks = split_into_chunks(replay_text)
    for index, chunk in enumerate(chunks):
        try:
            if index == 0:
                await message.reply(chunk, parse_mode=ParseMode.HTML)
        except Exception as err:
            try:
                logger.info('From try in for index chunks: %s', err)
                await message.reply(chunk + str(err), parse_mode=ParseMode.HTML)
            except Exception as error:
                logger.info('Last exception from Core: %s', error)
                await message.reply(str(error), parse_mode=ParseMode.HTML)


@router.message(Command(commands="course"), PrivateFilter())
async def course_choose(message: types.Message, state: FSMContext) -> None:
    await state.update_data(chatid=message.chat.id)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="ZOOM H5 #1 - Приморский EP", callback_data="buy_zoom"))
    kb.add(InlineKeyboardButton(text="PRO (КОНТЕНТ ПО ПОДПИСКЕ)", callback_data="buy_nppro"))
    kb.adjust(2)

    await message.reply("Какой курс хочешь приобрести?", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(Command(commands="course_state"), PrivateFilter())
async def state_course(message: types.Message, session: AsyncSession) -> None:
    user_manager = DatabaseManager(session)
    end_date = await user_manager.get_subscription_end_date(message.from_user.id, NeuropunkPro)
    if end_date:
        await message.answer(f"Ваша подписка истекает: {end_date.strftime('%d.%m.%Y %H:%M:%S')}")
    else:
        await message.answer("У вас нет активной подписки или произошла ошибка.")


@router.message(Command(commands="help"))
async def info_user(message: types.Message, l10n: FluentLocalization):
    logger.info("Loh pidar Anime: %s", message)
    await message.answer(l10n.format_value("help"))


@router.message(PrivateFilter(), Command(commands="demo", ignore_case=True))
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    first_name = message.chat.first_name
    now = datetime.now()
    result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
    close_date = result.scalar_one_or_none()

    if close_date and now < close_date.end_time:
        await message.answer(f"Привет {first_name}!\nЯ принимаю демки на эфиры Нейропанк академии\n"
                             f"Для начала пришли мне свою почту(gmail), чтобы я предоставил тебе доступ к стриму")
        await state.set_state(Demo.process)
    else:
        await message.answer(f"Привет {first_name}!\nСейчас не время присылать демки, попробуй позже")


@router.message(PrivateFilter(), Demo.process)
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    email = message.text
    first_name = message.from_user.first_name
    if check(email, email_patt):
        await state.update_data(email=str(message.text))
        new_email = StreamEmails(email=str(message.text), stream_id=1)
        async with session.begin():
            session.add(new_email)
            await session.commit()
        await message.reply(f"{first_name}, записал твой Email! Самое время прислать демку!\n"
                            "Пожалуйста, убедись что отправляешь 320 mp3 длиной не менее 2 минут,'\n"
                            "с полностью прописанными тегами\n"
                            """и названием файла в виде "Автор - Трек".\n""")
        await state.set_state(Demo.get)
    else:
        await message.reply(f"{first_name}, это не похоже на Email попробуй снова")


@router.message(PrivateFilter(), Demo.get, F.content_type.in_({'audio'}))
async def get_and_send_from_state(message: types.Message, state: FSMContext, bot: Bot, l10n: FluentLocalization):
    uid = message.from_user.id

    username = message.chat.username
    track = message.audio.file_id
    duration = message.audio.duration
    artist = message.audio.performer
    title = message.audio.title
    data = await state.get_data()
    email = data['email']

    logger.info('Full message info: %s', message)
    logger.info('username: %s, duration: %s, artist: %s , title: %s, file_name: %s', message.chat.username,
                message.audio.duration, message.audio.performer, message.audio.title,
                message.audio.file_name)

    file_info = await bot.get_file(track)
    file_data = file_info.file_path
    await bot.download_file(file_data, f"{str(uid)}.mp3")

    if username is None:
        await message.reply(l10n.format_value("empty-name-error"))
    elif duration <= 119:
        await message.reply(l10n.format_value("short-demo-error"))
    elif title is None:
        await message.reply(l10n.format_value("empty-title-tag-error"))
    elif artist is None:
        await message.reply(l10n.format_value("empty-artist-tag-error"))
    elif check_bit_rate(f"{str(uid)}.mp3") is False:
        await message.reply(l10n.format_value("bad-bitrate"))
        os.remove(f"{str(uid)}.mp3")
    else:
        text = f"Пришел трек.\n" \
               f"Отправил: @{username}\n" \
               f"Почта: {email}\n" \
               f"Длина файла: {duration} секунды\n" \
               f"title: {title}\n" \
               f"Artist: {artist}"
        await bot.send_audio(config.channel, audio=track, caption=text)

        await message.reply(l10n.format_value("demo-thanks-message"))
        os.remove(f"{str(uid)}.mp3")
        await state.clear()


@router.message(Command(commands="emails"), IsAdmin())
async def mails_get(message: types.Message, session: AsyncSession):
    stmt = select(StreamEmails.email)
    result = await session.execute(stmt)
    emails = result.fetchall()
    if emails:
        email_list = [email[0] for email in emails]
        all_emails_str = ", ".join(email_list)
        await message.reply(all_emails_str, parse_mode=None)
    else:
        await message.reply("Нет записей", parse_mode=None)
