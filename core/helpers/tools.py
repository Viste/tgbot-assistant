import logging
import json
import os

from aiogram import types
from fluent.runtime import FluentLocalization
from aiogram.enums import ParseMode

from tools.utils import config

logger = logging.getLogger(__name__)

banned = set(config.banned_user_ids)
shadowbanned = set(config.shadowbanned_user_ids)


class ChatState:
    _instance = None
    active_chat = None
    thread_id = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChatState, cls).__new__(cls)
        return cls._instance


async def reply_if_banned(message: types.Message, uid: int, l10n: FluentLocalization) -> bool:
    if uid in banned:
        await message.reply(l10n.format_value("you-were-banned-error"))
        return True
    return False


async def send_reply(message: types.Message, text: str) -> None:
    try:
        await message.reply(text, parse_mode=ParseMode.HTML)
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
