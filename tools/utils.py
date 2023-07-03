import json
import os
import re
from datetime import datetime
from typing import List

import mutagen
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class JSONObject:
    def __init__(self, dic):
        vars(self).update(dic)


cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
config = json.loads(cfg_file.read(), object_hook=JSONObject)
email_patt = re.compile("^(\w+?|\w+?\.\w+?|\w+?\.\w+?\.\w+?)@\w+?\.\w{2,12}$")


def split_into_chunks(text: str, chunk_size: int = 4096) -> list[str]:
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]


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
