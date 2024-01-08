import html
import logging

from aiogram import types, F, Router, flags
# from sqlalchemy.ext.asyncio import AsyncSession
from fluent.runtime import FluentLocalization

from core.helpers.tools import reply_if_banned, send_reply
# from tools.ai.moderator import Moderator
# from tools.ai.ai_tools import OpenAIDialogue
from tools.utils import split_into_chunks
from core.helpers.obs import ClientOBS


router = Router()
logger = logging.getLogger(__name__)
router.message.filter(F.chat.type.in_({'group', 'supergroup'}), F.chat.id == -1001647523732)

# openai = OpenAIDialogue()
# moderator = Moderator()


@flags.chat_action(action="typing", interval=1, initial_sleep=2)
@router.message(F.text)
async def process_obs(message: types.Message, l10n: FluentLocalization) -> None:
    uid = message.from_user.id
    obs = ClientOBS()
    username = message.from_user.username
    if await reply_if_banned(message, uid, l10n):
        return
    else:
        logging.info("%s", message)
        text = html.escape(message.text)
        result = await obs.send_message(message.from_user.first_name, text)

#        moderation = await moderator.query_gpt_mod(text)
#        logging.info("Flagged: %s", moderation['flagged'])
#        logging.info("Categories: %s", moderation['categories'])
#        if moderation['flagged'] is True:
#            if moderation['categories']['sexual'] is True:
#                text = f'Пользователь академии @{username}, использует в своей речи контент сексуального характера. ' \
#                       f'Сейчас ты пишешь ему, вынеси ему предупреждение'
#                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
#                chunks = split_into_chunks(replay_text)
#                for index, chunk in enumerate(chunks):
#                    if index == 0:
#                        await send_reply(message, chunk)
#            elif moderation['categories']['hate'] is True:
#                explain = f'Пользователь академии @{username}, использует в своей речи очень много ненависти. Сейчас ты ' \
#                       f'пишешь ему, вынеси ему предупреждение'
#                replay_text, total_tokens = await openai.get_resp(query=explain, chat_id=uid, session=session)
#                chunks = split_into_chunks(replay_text)
#                for index, chunk in enumerate(chunks):
#                    if index == 0:
#                        await send_reply(message, chunk)
#            elif moderation['categories']['violence'] is True:
#                exp = f'Пользователь академии @{username}, угрожает другим участникам чата физической расправой. ' \
#                       f'Сейчас ты пишешь ему, вынеси ему предупреждение'
#                replay_text, total_tokens = await openai.get_resp(query=exp, chat_id=uid, session=session)
#                chunks = split_into_chunks(replay_text)
#                for index, chunk in enumerate(chunks):
#                    if index == 0:
#                        await send_reply(message, chunk)
#            elif moderation['categories']['self-harm'] is True:
#                text = f'Пользователь академии @{username}, хочет себе навредить. Сейчас ты пишешь ему, поговори с ним'
#                replay_text, total_tokens = await openai.get_resp(query=text, chat_id=uid, session=session)
#                chunks = split_into_chunks(replay_text)
#                for index, chunk in enumerate(chunks):
#                    if index == 0:
#                        await send_reply(message, chunk)
#            else:
#                pass
