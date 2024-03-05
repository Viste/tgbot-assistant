import logging

from aiogram import types, Router, F, flags
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluent.runtime import FluentLocalization
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.helpers.tools import private_filter
from database.models import Calendar, StreamEmails
from tools.utils import config, get_dt

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command(commands="online", ignore_case=True), F.from_user.id.in_(config.admins), private_filter)
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


@router.message(Command(commands="offline", ignore_case=True), F.from_user.id.in_(config.admins), private_filter)
@flags.chat_action("typing")
async def offline_cmd(message: types.Message, session: AsyncSession):
    first_name = message.chat.first_name
    await session.execute(delete(Calendar))
    await session.execute(delete(StreamEmails))
    await session.commit()
    text = f"Личность подтверждена! Уважаемый, {first_name}, выключаю прием дэмок"
    await message.reply(text)


@router.message(F.from_user.id.in_(config.admins), Command(commands="help"), private_filter)
@flags.chat_action("typing")
async def info(message: types.Message, l10n: FluentLocalization):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = l10n.format_value("you-were-banned-error")
        await message.reply(text, parse_mode=None)
    else:
        text = l10n.format_value("admin-help")
        await message.reply(text, parse_mode=None)


@router.message(Command(commands="emails"), F.from_user.id.in_(config.admins), private_filter)
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


@router.message(Command(commands="stream", ignore_case=True), F.from_user.id.in_(config.admins), private_filter)
@flags.chat_action("typing")
async def stream_cmd(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Нейропанк Академия", callback_data="academy_chat"))
    kb.add(InlineKeyboardButton(text="PRO (КОНТЕНТ ПО ПОДПИСКЕ)", callback_data="np_pro"))
    kb.add(InlineKeyboardButton(text="ЛИКВИД КУРС", callback_data="liquid_chat"))
    kb.add(InlineKeyboardButton(text="НАЧАЛЬНЫЙ #1 - от 0 до паладина!", callback_data="np_basic"))
    kb.add(InlineKeyboardButton(text="SUPER PRO#1 (DNB)", callback_data="super_pro"))
    kb.add(InlineKeyboardButton(text="НЕЙРОФАНК КУРС ", callback_data="neuro"))
    kb.add(InlineKeyboardButton(text="NERV3 Продуктивность Level 99 #1", callback_data="nerve"))
    kb.add(InlineKeyboardButton(text="DNB Курс - только девушки!", callback_data="girls"))
    kb.adjust(2)

    await message.reply("Надо чат выбрать:", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(Command(commands="get_active_emails", ignore_case=True), F.from_user.id.in_(config.admins), private_filter)
@flags.chat_action("typing")
async def stream_cmd(message: types.Message, state: FSMContext):
    await state.update_data(chatid=message.chat.id)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="PRO (КОНТЕНТ ПО ПОДПИСКЕ)", callback_data="course_np_pro"))
    kb.adjust(2)

    await message.reply("С какого курса тебе дать почты? он пока один ахахах", reply_markup=kb.as_markup(resize_keyboard=True))
