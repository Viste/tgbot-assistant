import logging

from aiogram import types

from tools.utils import config

logger = logging.getLogger(__name__)


async def reply_if_banned(message: types.Message, uid: int) -> bool:
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
        return True
    return False


async def send_reply(message: types.Message, text: str) -> None:
    try:
        await message.reply(text, parse_mode=None)
    except Exception as err:
        logging.info('Exception while sending reply: %s', err)
        try:
            await message.reply(str(err), parse_mode=None)
        except Exception as error:
            logging.info('Last exception from Core: %s', error)
