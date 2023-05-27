import logging
import os

from aiogram import types, F, Router, flags

from main import paper
from tools.ai.listener_tools import OpenAIListener, Audio
from tools.utils import config, split_into_chunks

logger = logging.getLogger("__name__")

router = Router()
router.message.filter(F.chat.type.in_({'group', 'supergroup'}))
openai = OpenAIListener()
audio = Audio()


@flags.chat_action(action="typing", interval=5, initial_sleep=2)
@router.message(F.from_user.id.in_(config.test_users), F.content_type.in_({'audio'}))
async def handle_audio(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        file_path = f"tmp/{str(uid)}.mp3"
        file_info = await paper.get_file(message.audio.file_id)
        file_data = file_info.file_path
        await paper.download_file(file_data, file_path)

        result = await audio.process_audio_file(file_path)
        os.remove(file_path)
        replay_text, total_tokens = await openai.get_resp_listen(str(result))
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
