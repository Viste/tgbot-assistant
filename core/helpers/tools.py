import logging
import json
import os
import decimal
import hashlib

from aiogram import types
from fluent.runtime import FluentLocalization
from aiogram.enums import ParseMode

from tools.utils import config

logger = logging.getLogger(__name__)

banned = set(config.banned_user_ids)
shadowbanned = set(config.shadowbanned_user_ids)


active_chats = {-1001647523732: 0, -1001814931266: 5146, -1001922960346: 34, -1001999768206: 4, -1002040950538: 2, -1001961684542: 2450, -1002094481198: 2, -1001921488615: 9076}
# academy, neuropunk pro, neuropunk basic, liquid, SUPER PRO, neurofunk, nerve, girls

robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx?'
bad_response = "bad sign"
success_payment = "Thank you for using our service"
is_test = 0


class ChatState:
    _instance = None
    active_chat = None
    thread_id = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ChatState, cls).__new__(cls)
        return cls._instance


class EmailChatState:
    _instance = None
    active_chat = None
    thread_id = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmailChatState, cls).__new__(cls)
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


def calculate_signature(*args) -> str:
    """Create signature MD5.
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def parse_response(request: str) -> dict:
    """
    :param request: Link.
    :return: Dictionary.
    """
    from urllib.parse import urlparse
    params = {}

    for item in urlparse(request).query.split('&'):
        key, value = item.split('=')
        params[key] = value
    return params


def check_signature_result(order_number: int, received_sum: decimal, received_signature: hex, password: str) -> bool:
    signature = calculate_signature(received_sum, order_number, password)
    if signature.lower() == received_signature.lower():
        return True
    logger.error(f'{signature.lower()} != {received_signature.lower()}')
    return False
