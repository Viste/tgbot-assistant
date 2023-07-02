import logging

from aiogram import types, Router, F, flags, Bot
from aiogram.filters.command import Command, CommandObject
from aiogram.exceptions import TelegramAPIError
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from fluent.runtime import FluentLocalization

from database.models import Calendar, StreamEmails
from tools.ai.ai_tools import OpenAI
from tools.utils import config, get_dt

logger = logging.getLogger(__name__)
openai = OpenAI()
router = Router()
router.message.filter(F.chat.type.in_({'private'}))


def extract_id(message: types.Message) -> int:
    entities = message.entities or message.caption_entities
    if not entities or entities[-1].type != "hashtag":
        raise ValueError("Не удалось извлечь ID для ответа!")
    hashtag = entities[-1].extract_from(message.text or message.caption)
    if len(hashtag) < 4 or not hashtag[3:].isdigit():
        raise ValueError("Некорректный ID для ответа!")

    return int(hashtag[3:])


@router.message(Command(commands=["get", "who"]), F.chat.id.in_(config.admin_chat_id), F.reply_to_message)
async def get_user_info(message: types.Message, bot: Bot, l10n: FluentLocalization):
    def get_full_name(chat: types.Chat):
        if not chat.first_name:
            return ""
        if not chat.last_name:
            return chat.first_name
        return f"{chat.first_name} {chat.last_name}"

    try:
        user_id = extract_id(message.reply_to_message)
    except ValueError as ex:
        return await message.reply(str(ex))

    try:
        user = await bot.get_chat(user_id)
    except TelegramAPIError as ex:
        await message.reply(l10n.format_value(msg_id="cannot-get-user-info-error", args={"error": ex.message}))
        return

    u = f"@{user.username}" if user.username else l10n.format_value("no")
    await message.reply(l10n.format_value(msg_id="user-info", args={"name": get_full_name(user),
                                                                    "id": user.id, "username": u}))


@router.message(F.reply_to_message, F.chat.id.in_(config.admin_chat_id))
async def reply_to_user(message: types.Message, l10n: FluentLocalization):
    try:
        user_id = extract_id(message.reply_to_message)
    except ValueError as ex:
        return await message.reply(str(ex))

    try:
        await message.copy_to(user_id)
    except TelegramAPIError as ex:
        await message.reply(
            l10n.format_value(
                msg_id="cannot-answer-to-user-error",
                args={"error": ex.message})
        )


@router.message(Command(commands="online", ignore_case=True), F.chat.id.in_(config.admins))
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


@router.message(Command(commands="offline", ignore_case=True), F.chat.id.in_(config.admins))
@flags.chat_action("typing")
async def offline_cmd(message: types.Message, session: AsyncSession):
    first_name = message.chat.first_name
    await session.execute(delete(Calendar))
    await session.execute(delete(StreamEmails))
    await session.commit()
    text = f"Личность подтверждена! Уважаемый, {first_name}, включаю прием дэмок"
    await message.reply(text)


@router.message(Command(commands="help"), F.chat.id.in_(config.admins))
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


@router.message(Command(commands="money"), F.chat.id.in_(config.admins))
@flags.chat_action("typing")
async def usage(message: types.Message):
    text = openai.get_money()
    await message.reply(text, parse_mode=None)


@router.message(Command(commands="emails"), F.chat.id.in_(config.admins))
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
