import logging
import json
import os
import hashlib
import aiohttp
from xml.etree.ElementTree import fromstring

from aiogram import types
from fluent.runtime import FluentLocalization
from aiogram.enums import ParseMode

from tools.utils import config

logger = logging.getLogger(__name__)

banned = set(config.banned_user_ids)
shadowbanned = set(config.shadowbanned_user_ids)

# academy, neuropunk pro, neuropunk basic, liquid, SUPER PRO, neurofunk, nerve, girls
active_chats = {
    -1001647523732: 0, -1001814931266: 5146, -1001922960346: 34, -1001999768206: 4, -1002040950538: 2, -1001961684542: 2450, -1002094481198: 2, -1001921488615: 9076
    }

chat_settings = {
    "academy_chat": {"active_chat": -1001647523732, "thread_id": None}, "np_pro": {"active_chat": -1001814931266, "thread_id": 5146}, "np_basic": {"active_chat": -1001922960346, "thread_id": 25503},
    "liquid_chat": {"active_chat": -1001999768206, "thread_id": 4284}, "super_pro": {"active_chat": -1002040950538, "thread_id": 293}, "neuro": {"active_chat": -1001961684542, "thread_id": 4048},
    "nerve": {"active_chat": -1002094481198, "thread_id": 72}, "girls": {"active_chat": -1001921488615, "thread_id": 9075},
    }

robokassa_payment_url = 'https://auth.robokassa.ru/Merchant/Index.aspx'
robokassa_check_url = 'https://auth.robokassa.ru/Merchant/WebService/Service.asmx/OpStateExt'
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


def parse_xml_response(xml_data: str):
    ns = {'ns': 'http://merchant.roboxchange.com/WebService/'}
    root = fromstring(xml_data)
    result = {
        "Result": {}, "State": {}, "Info": {}, "UserField": []
        }
    result_section = root.find(".//ns:Result", ns)
    if result_section is not None:
        result["Result"]["Code"] = result_section.find("ns:Code", ns).text
        description = result_section.find("ns:Description", ns)
        if description is not None:
            result["Result"]["Description"] = description.text

    state_section = root.find(".//ns:State", ns)
    if state_section is not None:
        result["State"]["Code"] = state_section.find("ns:Code", ns).text
        result["State"]["RequestDate"] = state_section.find("ns:RequestDate", ns).text
        result["State"]["StateDate"] = state_section.find("ns:StateDate", ns).text

    info_section = root.find(".//ns:Info", ns)
    if info_section is not None:
        result["Info"]["IncCurrLabel"] = info_section.find("ns:IncCurrLabel", ns).text
        result["Info"]["IncSum"] = info_section.find("ns:IncSum", ns).text
        result["Info"]["IncAccount"] = info_section.find("ns:IncAccount", ns).text

    user_field_section = root.findall(".//ns:UserField/ns:Field", ns)
    for field in user_field_section:
        name = field.find("ns:Name", ns).text
        value = field.find("ns:Value", ns).text
        result["UserField"].append({"Name": name, "Value": value})

    return result


async def generate_robokassa_link(merchant_login: str, invoice_id: int, password2: str) -> str:
    base_url = robokassa_check_url
    signature_string = f"{merchant_login}:{invoice_id}:{password2}"
    signature = hashlib.md5(signature_string.encode()).hexdigest()
    url = f"{base_url}?MerchantLogin={merchant_login}&InvoiceID={invoice_id}&Signature={signature}"
    return url
