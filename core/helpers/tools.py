import hashlib
import logging
from datetime import datetime
from typing import Type
from urllib import parse

import aiohttp
from aiogram import types
from aiogram.enums import ParseMode
from fluent.runtime import FluentLocalization
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta

from database.databasemanager import DatabaseManager
from tools.data import Merchant, Order

logger = logging.getLogger(__name__)

ALLOWED_CHAT_IDS = {
    -1001647523732, -1001700103389, -1001537420102,
    -1002004353654, -1001170569681, -1002021584528,
    -1002117966241, -1002042364255
}

ALLOWED_CHAT_THREAD_IDS = {
    -1001922960346: {12842},
    -1002040950538: {305},
    -1002094481198: {58},
    -1001921488615: {9078},
    -1002085114945: {28},
    -1002021584528: {136},
    -1002117966241: {36},
    -1002042364255: {21}
}

chat_settings = {
    "academy_chat": {"active_chat": -1001647523732, "thread_id": None},
    "np_pro": {"active_chat": -1001814931266, "thread_id": 5146},
    "np_basic": {"active_chat": -1001922960346, "thread_id": 25503},
    "liquid_chat": {"active_chat": -1001999768206, "thread_id": 4284},
    "super_pro": {"active_chat": -1002040950538, "thread_id": 293},
    "neuro": {"active_chat": -1001961684542, "thread_id": 4048},
    "nerve": {"active_chat": -1002094481198, "thread_id": 72},
    "girls": {"active_chat": -1001921488615, "thread_id": 9075},
    "zoom": {"active_chat": -1002085114945, "thread_id": 30},
    "fll21free": {"active_chat": -1002021584528, "thread_id": 52},
    "gydra": {"active_chat": 1002042364255, "thread_id": 76},
    "receptor": {"active_chat": -1002117966241,"thread_id": 36},
}

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


async def reply_if_banned(message: types.Message, uid: int, l10n: FluentLocalization, session: AsyncSession) -> bool:
    user_manager = DatabaseManager(session)
    if await user_manager.is_user_banned(uid):
        await message.reply(l10n.format_value("you-were-banned-error"))
        return True
    return False


async def send_reply(message: types.Message, text: str) -> None:
    try:
        await message.reply(text, parse_mode=ParseMode.HTML)
    except Exception as err:
        logger.info('Exception while sending reply: %s', err)
        try:
            await message.reply(str(err), parse_mode=None)
        except Exception as error:
            logger.info('Last exception from Core: %s', error)


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


async def handle_exception(message: types.Message, err: Exception,
                           error_message: str = "Не удалось получить картинку. Попробуйте еще раз.\n "):
    try:
        logger.info('From exception in Picture: %s', err)
        await message.reply(error_message, parse_mode=None)
    except Exception as error:
        logger.info('Last exception from Picture: %s', error)
        await message.reply(str(error), parse_mode=None)


async def send_payment_message(message: types.Message, link: str, l10n: FluentLocalization, button_text_key: str,
                               answer_text_key: str):
    kb = [[types.InlineKeyboardButton(text=l10n.format_value(button_text_key), url=link)]]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)
    await message.reply(l10n.format_value(answer_text_key), reply_markup=keyboard)


async def update_or_create_user(session: AsyncSession, user_data: dict, model: Type[DeclarativeMeta]):
    user_manager = DatabaseManager(session)
    user = await user_manager.get_user(user_data['telegram_id'], model)
    if user:
        # Если подписка уже активна, продлеваем ее
        if user.subscription_end and user.subscription_end > datetime.utcnow():
            await user_manager.extend_subscription(user_data['telegram_id'], model)
        else:
            # Если подписка не активна, обновляем данные пользователя
            for key, value in user_data.items():
                setattr(user, key, value)
    else:
        # Создаем нового пользователя, если он не найден
        user = await user_manager.create_user(user_data, model)
    await session.commit()


class MessageProcessor:
    _instance = None
    messages = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MessageProcessor, cls).__new__(cls)
        return cls._instance

    @classmethod
    def add_message(cls, name, message, isGif):
        cls.messages.append({'name': name, 'message': message, 'isGif': isGif})

    @classmethod
    def get_messages(cls):
        return cls.messages

    @classmethod
    def clear_messages(cls):
        cls.messages.clear()
