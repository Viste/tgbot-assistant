import html
import logging

from aiogram import types, F, Router, flags
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import reply_if_banned, send_reply
from tools.ai.moderator import Moderator
from tools.ai.user_dialogue import OpenAIDialogue
from tools.utils import split_into_chunks

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id == -1001647523732)
openai = OpenAIDialogue()
moderator = Moderator()


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(F.text)
async def process_moderating(message: types.Message, session: AsyncSession) -> None:
    uid = message.from_user.id
    if await reply_if_banned(message, uid):
        return
    else:
        logging.info("%s", message)
        text = html.escape(message.text)

        moderation = await moderator.query_gpt_mod(text)
        print(moderation['flagged'])
        if moderation['flagged'] is True:
            if moderation['categories']['sexual'] is True:
                text = f'Пользователь академии @{uid}, использует в своей речи контент сексуального характера. Сейчас ты пишешь ему, вынеси ему предупреждение'
                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
                chunks = split_into_chunks(replay_text)
                for index, chunk in enumerate(chunks):
                    if index == 0:
                        await send_reply(message, chunk)
            elif moderation['categories']['hate'] is True:
                text = f'Пользователь академии @{uid}, использует в своей речи очень много ненависти. Сейчас ты пишешь ему, вынеси ему предупреждение'
                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
                chunks = split_into_chunks(replay_text)
                for index, chunk in enumerate(chunks):
                    if index == 0:
                        await send_reply(message, chunk)
            elif moderation['categories']['violence'] is True:
                text = f'Пользователь академии @{uid}, угрожает другим участникам чата физической расправой. Сейчас ты пишешь ему, вынеси ему предупреждение'
                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
                chunks = split_into_chunks(replay_text)
                for index, chunk in enumerate(chunks):
                    if index == 0:
                        await send_reply(message, chunk)
            elif moderation['categories']['self-harm'] is True:
                text = f'Пользователь академии @{uid}, хочет себе навредить. Сейчас ты пишешь ему, поговори с ним'
                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
                chunks = split_into_chunks(replay_text)
                for index, chunk in enumerate(chunks):
                    if index == 0:
                        await send_reply(message, chunk)
            else:
                pass
