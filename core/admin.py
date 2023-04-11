import logging
import datetime

from aiogram import types, Router, F
from aiogram.filters.command import Command

from tools.utils import config

logger = logging.getLogger("__name__")
router = Router()
date = {}


@router.message(Command(commands="online", ignore_case=True, magic=F.args.cast(int).as_("value")), F.from_user.id.in_(config.admins))
async def online(message: types.Message, value: datetime):
    print(f"{value = }")
    first_name = message.chat.first_name
    text = f"Личность подтверждена! Уважаемый, {first_name}, включаю прием дэмок, время окончания прием демок {value}"
    await message.reply(text)
