import decimal
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List
from xml.etree.ElementTree import fromstring

import aiohttp
import mutagen
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User

logger = logging.getLogger(__name__)
email_patt = re.compile("^(\w+?|\w+?\.\w+?|\w+?\.\w+?\.\w+?)@\w+?\.\w{2,12}$")
gmail_patt = re.compile("^[a-zA-Z0-9._%+-]+?@gmail\.com")
np_pro_chat = -1001814931266


@dataclass
class Merchant:
    login: str
    password1: str
    password2: str


@dataclass
class Order:
    number: int
    description: str
    cost: decimal


class JSONObject:
    def __init__(self, dic):
        vars(self).update(dic)


cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
config = json.loads(cfg_file.read(), object_hook=JSONObject)


def split_into_chunks(text: str, chunk_size: int = 4096) -> list[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


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


async def check_payment(url) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            xml_data = await response.text()
            parsed_response = parse_xml_response(xml_data)
            logger.info("Parsed response from robokassa %s", parsed_response)
            return parsed_response


def check(string, performer):
    if re.search(performer, string):
        return True
    else:
        return False


def check_bit_rate(file):
    f = mutagen.File(file)
    bit_rate = f.info.bitrate / 1000
    if bit_rate >= 320:
        return True
    else:
        return False


def get_dt(value):
    dt_obj = datetime.strptime(value, "%d.%m.%Y %H:%M")
    formatted_value = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_value


async def get_all_telegram_ids(session: AsyncSession) -> List[int]:
    result = await session.execute(select(User.telegram_id))
    telegram_ids = [row[0] for row in result.fetchall()]
    print(telegram_ids)
    return telegram_ids


def year_month(date_str):
    # extract string of year-month from date, eg: '2023-03'
    return str(date_str)[:7]
