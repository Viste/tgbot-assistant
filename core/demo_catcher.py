import logging
import os
from datetime import datetime

from aiogram import types, F, Router, flags, Bot
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound
from fluent.runtime import FluentLocalization

from database.models import Calendar, StreamEmails
from core.helpers.tools import reply_if_banned
from tools.states import Demo
from tools.utils import config, check_bit_rate, email_patt, check
from tools.ai.vision import OpenAIVision

router = Router()
logger = logging.getLogger(__name__)
router.message.filter(F.chat.type.in_({'private'}))
channel = config.channel


@router.message(Command(commands="demo", ignore_case=True))
@flags.chat_action("typing")
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    uid = message.from_user.id

    if await reply_if_banned(message, uid, l10n):
        return

    first_name = message.chat.first_name
    now = datetime.now()
    try:
        result = await session.execute(select(Calendar).order_by(desc(Calendar.end_time)).limit(1))
        close_date = result.scalar_one()
        await session.commit()
    except NoResultFound:
        close_date = None
    if close_date is not None:
        if close_date.end_time is not None or now < close_date.end_time:
            await message.answer(f"Привет {first_name}!\nЯ принимаю демки на эфиры Нейропанк академии\n"
                                 f"Для начала пришли мне свое фото с клоунским носом, затем продолжим")
            await state.set_state(Demo.start)
        else:
            await message.answer(f"Привет {first_name}!\nСейчас не время присылать демки, попробуй позже")
    else:
        await message.answer(f"Привет {first_name}!\nСейчас не время присылать демки, попробуй позже")


@router.message(Demo.start)
@flags.chat_action("typing")
async def process_cmd(message: types.Message, state: FSMContext, bot: Bot, l10n: FluentLocalization):
    openai = OpenAIVision()
    file_id = message.photo[-1].file_id
    file_info = await bot.get_file(file_id)
    file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"

    replay_text = await openai.get_vision(file_url)
    await message.reply(replay_text)
    #await message.reply("Спасибо, теперь пришли мне свой email(с сервиса gmail), чтобы я предоставил тебе доступ к стриму")
    await state.set_state(Demo.process)


@router.message(Demo.process)
@flags.chat_action("typing")
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession, l10n: FluentLocalization):
    email = message.text
    first_name = message.from_user.first_name
    if check(email, email_patt):
        await state.update_data(email=str(message.text))
        new_email = StreamEmails(email=str(message.text), stream_id=1)
        async with session.begin():
            session.add(new_email)
            await session.commit()
        await message.reply(f"{first_name}, записал твой Email! Самое время прислать демку!\n"
                            """Пожалуйста, убедись что отправляешь 320 mp3 длиной не менее 2 минут, с полностью
                            прописанными тегами\n и названием файла в виде "Автор - Трек".\n""")
        await state.set_state(Demo.get)
    else:
        await message.reply(f"{first_name}, это не похоже на Email попробуй снова")


@router.message(Demo.get, F.content_type.in_({'audio'}))
@flags.chat_action("typing")
async def get_and_send_from_state(message: types.Message, state: FSMContext, bot: Bot, l10n: FluentLocalization):
    uid = message.from_user.id
    if await reply_if_banned(message, uid, l10n):
        return

    username = message.chat.username
    track = message.audio.file_id
    duration = message.audio.duration
    artist = message.audio.performer
    title = message.audio.title
    data = await state.get_data()
    email = data['email']

    logging.info('Full message info: %s', message)
    logging.info('username: %s, duration: %s, artist: %s , title: %s, file_name: %s', message.chat.username,
                 message.audio.duration, message.audio.performer, message.audio.title, message.audio.file_name)

    file_info = await bot.get_file(track)
    file_data = file_info.file_path
    await bot.download_file(file_data, f"{str(uid)}.mp3")
    if username is None:
        await message.reply(
            "Пожалуйста, заполни username в настройках телеграм.\nЭто нужно для последующей связи с тобой")
    elif duration <= 119:
        await message.reply(
            "Длина присланного трека менее двух минут, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
    elif title is None:
        await message.reply(
            "Тег title в треке не заполнен, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
    elif artist is None:
        await message.reply(
            "Тег artist в треке не заполнен, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
    elif check_bit_rate(f"{str(uid)}.mp3") is False:
        await message.reply('Битрейт mp3 файла менее 320.')
        os.remove(f"{str(uid)}.mp3")
    else:
        text = f"Пришел трек.\n" \
               f"Отправил: @{username}\n" \
               f"Почта: {email}\n" \
               f"Длина файла: {duration} секунды\n" \
               f"title: {title}\n" \
               f"Artist: {artist}"
        await bot.send_audio(config.channel, audio=track, caption=text)
        await message.reply("Спасибо за демку! Если захочешь прислать еще один, просто снова напиши /demo и помни "
                            "про требования к треку.\n320 mp3 длиной не менее 2 минут, с полностью прописанными "
                            "тегами и названием файла в виде 'Автор - Трек'")
        os.remove(f"{str(uid)}.mp3")
        await state.clear()
