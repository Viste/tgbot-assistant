import json
import os
import re
from datetime import datetime

import mutagen


class JSONObject:
    def __init__(self, dic):
        vars(self).update(dic)


cfg_file = open(os.path.join(os.path.dirname(__file__), 'config.json'), 'r', encoding='utf8')
config = json.loads(cfg_file.read(), object_hook=JSONObject)
pattern = re.compile("^(?!ID\s+?|iD\s+?|Айди\s+?|АЙДИ\s+?|аЙДИ\s+?|айДи\s+?|АЙди\s+?|Id\s+?|id\s+?)([\w\W\s]+?\s+?)-\s+?([\w\W\s]+?)\.mp3$")
email_patt = re.compile("^\w+?@\w+?\.\w{2,12$")


def trim_name(text: str) -> str:
    if text.startswith("@cyberpaperbot"):
        text = text.strip("@cyberpaperbot")
    return text.strip("\n")


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
