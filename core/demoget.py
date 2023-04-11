import logging
import os

from aiogram import types, F, Router
from aiogram.filters.command import Command
from main import paper
from tools.utils import config, check, pattern, check_bit_rate

logger = logging.getLogger("__name__")
router = Router()
channel = config.channel


@router.message(Command(commands="start", ignore_case=True), F.chat.type == "private")
async def start(message: types.Message):
    first_name = message.chat.first_name
    await message.reply(f"Привет {first_name}!\n Я принимаю демки на эфиры Нейропанк академии")


@router.message(F.content_type.in_({'audio'}), F.chat.type == "private")
async def get_and_send(message: types.Message):
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

        logging.info('Full message info: %s', message)
        logging.info('username: %s, duration: %s, artist: %s , title: %s, file_name: %s', message.chat.username,
                     message.audio.duration, message.audio.performer, message.audio.title, message.audio.file_name)

        file_info = await paper.get_file(track)
        file_data = file_info.file_path
        await paper.download_file(file_data, f"{str(uid)}.mp3")

        if username is None:
            await message.reply("Пожалуйста, заполни username в настройках телеграм.\nЭто нужно для последующей связи с тобой")
        elif duration <= 119:
            await message.reply("Длина присланного трека менее двух минут, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
        elif title is None:
            await message.reply("Тег title в треке не заполнен, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
        elif artist is None:
            await message.reply("Тег artist в треке не заполнен, не могу его принять.\nПожалуйста исправь и отправь еще раз.")
        elif check(file_name, pattern) is False:
            await message.reply("Название не соответствует требованиям, возможно ты использовал ID в имени артиста, или не указал дефис между автором и названием трека, "
                                "не могу его принять.\nПожалуйста исправь и отправь еще раз.")
        elif check_bit_rate(f"{str(uid)}.mp3") is False:
            await message.reply('Битрейт mp3 файла менее 320.')
            os.remove(f"{str(uid)}.mp3")
        else:
            text = f"Пришел трек.\n" \
                   f"Отправил: @{username}\n" \
                   f"Длина файла: {duration} секунды\n" \
                   f"title: {title}\n" \
                   f"Artist: {artist}"
            await paper.send_audio(config.channel, audio=track, caption=text)
            await message.reply("Спасибо за демку! Если захочешь прислать еще один, просто отправь его мне и помни про требования к треку.\n"
                                "320 mp3 длиной не менее 2 минут, с полностью прописанными тегами и названием файла в виде 'Автор - Трек'")
            os.remove(f"{str(uid)}.mp3")


@router.message(F.content_type.in_({'text', 'photo'}), F.chat.type == "private")
async def chat(message: types.Message):
    await message.reply("Пришли трек в соответствии с условиями, а пообщаться можно тут https://t.me/pprfnkch")
