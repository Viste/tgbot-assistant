import logging

from aiogram import types, Router, F, flags
from aiogram.filters.command import Command, CommandObject
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Calendar, StreamEmails
from tools.ai.ai_tools import OpenAI
from tools.utils import config, get_dt

logger = logging.getLogger(__name__)
ses = AsyncSession
openai = OpenAI(ses)
router = Router()
router.message.filter(F.chat.type.in_({'private'}), F.from_user.id.in_(config.admins))


@router.message(Command(commands="online", ignore_case=True))
@flags.chat_action("typing")
async def online_cmd(message: types.Message, command: CommandObject, session: AsyncSession):
    first_name = message.chat.first_name
    dt = get_dt(command.args)
    new_date = Calendar(end_time=dt)
    async with session.begin():
        session.add(new_date)
        await session.commit()
    text = f"Личность подтверждена! Уважаемый, {first_name}, включаю прием дэмок.\nВремя окончания приема демок {dt}"
    await message.reply(text)


@router.message(Command(commands="offline", ignore_case=True))
@flags.chat_action("typing")
async def offline_cmd(message: types.Message, session: AsyncSession):
    first_name = message.chat.first_name
    await session.execute(delete(Calendar))
    await session.execute(delete(StreamEmails))
    await session.commit()
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
               "Например: /online 22.04.2023 23:59" \
               "\n" \
               "Автор: @vistee"
        await message.reply(text, parse_mode=None)


@router.message(Command(commands="money"))
@flags.chat_action("typing")
async def usage(message: types.Message):
    text = openai.get_money()
    await message.reply(text, parse_mode=None)


@router.message(Command(commands="emails"))
@flags.chat_action("typing")
async def mails_get(message: types.Message, session: AsyncSession):
    stmt = select(StreamEmails.email)
    result = await session.execute(stmt)
    emails = result.fetchall()
    if emails:
        email_list = [email[0] for email in emails]
        all_emails_str = ", ".join(email_list)
        await message.reply(all_emails_str, parse_mode=None)
    else:
        await message.reply("Нет записей", parse_mode=None)
