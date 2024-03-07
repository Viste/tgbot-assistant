import hashlib
import json
import logging
import os
from urllib import parse

import aiohttp
from aiogram import types, F
from aiogram.enums import ParseMode
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession

from database.manager import UserManager
from database.models import User, NeuropunkPro
from tools.utils import config, Merchant, Order

logger = logging.getLogger(__name__)

banned = set(config.banned_user_ids)
shadowbanned = set(config.shadowbanned_user_ids)

chat_settings = {
    "academy_chat": {"active_chat": -1001647523732, "thread_id": None}, "np_pro": {"active_chat": -1001814931266, "thread_id": 5146}, "np_basic": {"active_chat": -1001922960346, "thread_id": 25503},
    "liquid_chat": {"active_chat": -1001999768206, "thread_id": 4284}, "super_pro": {"active_chat": -1002040950538, "thread_id": 293}, "neuro": {"active_chat": -1001961684542, "thread_id": 4048},
    "nerve": {"active_chat": -1002094481198, "thread_id": 72}, "girls": {"active_chat": -1001921488615, "thread_id": 9075},
    }

forum_filter = ((F.chat.type.in_({'group', 'supergroup'})) & (((F.chat.id == -1001922960346) & (F.message_thread_id == 12842)) |
                                                              ((F.chat.id == -1002040950538) & (F.message_thread_id == 305)) |
                                                              ((F.chat.id == -1002094481198) & (F.message_thread_id == 58)) |
                                                              ((F.chat.id == -1001921488615) & (F.message_thread_id == 9078))))
chat_filter = F.chat.type.in_({'group', 'supergroup'}) & F.chat.id.in_(config.allowed_groups)
basic_chat_filter = F.chat.type.in_({'group', 'supergroup'})
private_filter = F.chat.type == 'private'
subscribe_chat_filter = ((F.chat.type.in_({'group', 'supergroup'})) & ((F.chat.id == -1001814931266) & (F.message_thread_id == 5472)))
subscribe_chat_check_filter = ((F.chat.type.in_({'group', 'supergroup'})) & ((F.chat.id == -1001814931266) & (F.message_thread_id == 1)))

robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx'
robokassa_check_url = 'https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt'
is_test = 0


class Robokassa:
    def __init__(self, merchant: Merchant):
        self.merchant = merchant

    async def generate_payment_link(self, order: Order) -> str:
        signature = calculate_signature(self.merchant.login, order.cost, order.number, self.merchant.password1)
        data = {
            'MerchantLogin': self.merchant.login,
            'OutSum': order.cost,
            'InvId': order.number,
            'Description': order.description,
            'SignatureValue': str(signature),
            'IsTest': is_test}
        return f'{robokassa_payment_url}?{parse.urlencode(data)}'


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
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


async def parse_response(request: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(request) as response:
            text = await response.text()
            params = {}
            for item in text.split('&'):
                key, value = item.split('=')
                params[key] = value
            return params


def get_payment_status_message(result_code: int, l10n: FluentLocalization) -> str:
    status_messages = {
        0: l10n.format_value("success-query"),
        1: l10n.format_value("wrong-sing-error"),
        2: l10n.format_value("wrong-merchant-name-error"),
        3: l10n.format_value("wrong-invoice-error"),
        4: l10n.format_value("duplicate-invoice-error"),
        1000: l10n.format_value("service-error")}
    return status_messages.get(result_code, l10n.format_value("unknown-payment-error"))


async def generate_robokassa_link(merchant_login: str, invoice_id: int, password2: str) -> str:
    base_url = robokassa_check_url
    signature_string = f"{merchant_login}:{invoice_id}:{password2}"
    signature = hashlib.md5(signature_string.encode()).hexdigest()
    url = f"{base_url}?MerchantLogin={merchant_login}&InvoiceID={invoice_id}&Signature={signature}"
    return url


async def handle_exception(message: types.Message, err: Exception, error_message: str = "Не удалось получить картинку. Попробуйте еще раз.\n "):
    try:
        logging.info('From exception in Picture: %s', err)
        await message.reply(error_message, parse_mode=None)
    except Exception as error:
        logging.info('Last exception from Picture: %s', error)
        await message.reply(str(error), parse_mode=None)


async def send_payment_message(message: types.Message, link: str, l10n: FluentLocalization, button_text_key: str, answer_text_key: str):
    kb = [[types.InlineKeyboardButton(text=l10n.format_value(button_text_key), url=link)]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.reply(l10n.format_value(answer_text_key), reply_markup=keyboard)


async def update_or_create_user(session: AsyncSession, user_data: dict, is_course=False):
    user_manager = UserManager(session)
    if is_course:
        user = await user_manager.get_course_user(user_data['telegram_id'])
        if user is None:
            user = NeuropunkPro(**user_data)
            session.add(user)
        else:
            for key, value in user_data.items():
                setattr(user, key, value)
    else:
        user = await user_manager.get_user(user_data['telegram_id'])
        if user is None:
            user = User(**user_data)
            session.add(user)
        else:
            for key, value in user_data.items():
                setattr(user, key, value)
    await session.commit()
