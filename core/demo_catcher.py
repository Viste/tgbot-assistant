import logging
import os
from datetime import datetime

from aiogram import types, F, Router, flags
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from database.models import Calendar, StreamEmails
from main import paper
from tools.states import Demo
from tools.utils import config, check, pattern, check_bit_rate, email_patt

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({'private'}))
channel = config.channel


@router.message(Command(commands="demo", ignore_case=True))
@flags.chat_action("typing")
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
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
                                     f"Для начала напиши мне свой email, чтобы я предоставил тебе доступ к стриму")
                await state.set_state(Demo.start)
            else:
                await message.answer(f"Привет {first_name}!\nСейчас не время присылать демки, попробуй позже")
        else:
            await message.answer(f"Привет {first_name}!\nСейчас не время присылать демки, попробуй позже")


@router.message(Demo.start)
@flags.chat_action("typing")
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
                            """Пожалуйста, убедись что отправляешь 320 mp3 длиной не менее 2 минут, с полностью прописанными тегами и названием файла в виде "Автор - Трек".\n""")
        await state.set_state(Demo.get)
    else:
        await message.reply(f"{first_name}, это не похоже на Email попробуй снова")


@router.message(Demo.get, F.content_type.in_({'audio'}))
@flags.chat_action("typing")
async def get_and_send_from_state(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        username = message.chat.username
        track = message.audio.file_id
        duration = message.audio.duration
        artist = message.audio.performer
        title = message.audio.title
        file_name = message.audio.file_name
        data = await state.get_data()
        email = data['email']

        logging.info('Full message info: %s', message)
        logging.info('username: %s, duration: %s, artist: %s , title: %s, file_name: %s', message.chat.username,
                     message.audio.duration, message.audio.performer, message.audio.title, message.audio.file_name)

        file_info = await paper.get_file(track)
        file_data = file_info.file_path
        await paper.download_file(file_data, f"{str(uid)}.mp3")

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
        elif check(file_name, pattern) is False:
            await message.reply(
                "Название не соответствует требованиям, возможно ты не указал дефис между автором и названием трека, "
                "не могу его принять.\nПожалуйста исправь и отправь еще раз.")
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
            await paper.send_audio(config.channel, audio=track, caption=text)
            await message.reply(
                "Спасибо за демку! Если захочешь прислать еще один, просто отправь его мне и помни про требования к треку.\n"
                "320 mp3 длиной не менее 2 минут, с полностью прописанными тегами и названием файла в виде 'Автор - Трек'")
            os.remove(f"{str(uid)}.mp3")
            await state.clear()
