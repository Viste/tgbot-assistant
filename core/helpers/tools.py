import logging
import json
import os

from aiogram import types

from tools.utils import config

logger = logging.getLogger(__name__)

banned = set(config.banned_user_ids)
shadowbanned = set(config.shadowbanned_user_ids)


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


def update_config():
    config.banned_user_ids = list(banned)
    config.shadowbanned_user_ids = list(shadowbanned)
    with open(os.path.join(os.path.dirname(__file__), 'config.json'), 'w', encoding='utf8') as cfg_file:
        json.dump(config, cfg_file, default=lambda o: o.__dict__)
