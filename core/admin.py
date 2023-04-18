import logging

from aiogram import types, Router, F, flags
from aiogram.filters.command import Command, CommandObject

from tools.ai_tools import OpenAI
from tools.utils import config, get_dt

logger = logging.getLogger("__name__")
openai = OpenAI()
router = Router()
router.message.filter(F.chat.type.in_({'private'}), F.from_user.id.in_(config.admins))
end_date = []


@router.message(Command(commands="online", ignore_case=True))
@flags.chat_action("typing")
async def online_cmd(message: types.Message, command: CommandObject):
    first_name = message.chat.first_name
    dt = get_dt(command.args)
    end_date.append(dt)
    text = f"Личность подтверждена! Уважаемый, {first_name}, включаю прием дэмок, время окончания прием демок {dt}"
    await message.reply(text)


@router.message(Command(commands="offline", ignore_case=True))
@flags.chat_action("typing")
async def offline_cmd(message: types.Message):
    first_name = message.chat.first_name
    end_date.clear()
    text = f"Личность подтверждена! Уважаемый, {first_name}, включаю прием дэмок"
    await message.reply(text)


@router.message(Command(commands="help"))
@flags.chat_action("typing")
async def info(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Для запуска приема демок напиши /online и укажи дату окончания приема демок\n" \
               "Например: /start 22.04.2023 23.59" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)


@router.message(Command(commands="money"))
@flags.chat_action("typing")
async def usage(message: types.Message):
    text = openai.get_money()
    await message.reply(text, parse_mode=None)
