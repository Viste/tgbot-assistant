import logging

from aiogram import types, Router, F, flags
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Calendar, StreamEmails
from database.manager import UserManager
from tools.ai.ai_tools import OpenAI
from tools.utils import config, get_dt

router = Router()
router.message.filter(F.chat.type.in_({'private'}))

logger = logging.getLogger(__name__)


# def extract_id(message: types.Message) -> int:
#    entities = message.entities or message.caption_entities
#    logging.info("entities: %s", entities)
#    if not entities or entities[-1].type != "hashtag":
#        raise ValueError("Не удалось извлечь ID для ответа!")
#    hashtag = entities[-1].extract_from(message.text or message.caption)
#    logging.info("hashtag: %s", int(hashtag[3:]))
#    if len(hashtag) < 4 or not hashtag[3:].isdigit():
#        raise ValueError("Некорректный ID для ответа!")
#
#    return int(hashtag[3:])


# @router.message(Command(commands=["get", "who"]), F.from_user.id.in_(config.admin_chat_id), F.reply_to_message)
# async def get_user_info(message: types.Message, bot: Bot, l10n: FluentLocalization):
#    def get_full_name(chat: types.Chat):
#        if not chat.first_name:
#            return ""
#        if not chat.last_name:
#            return chat.first_name
#        return f"{chat.first_name} {chat.last_name}"

#    try:
#        user_id = extract_id(message.reply_to_message)
#    except ValueError as ex:
#        return await message.reply(str(ex))

#    try:
#        user = await bot.get_chat(user_id)
#    except TelegramAPIError as ex:
#        await message.reply(l10n.format_value(msg_id="cannot-get-user-info-error", args={"error": ex.message}))
#        return

#    u = f"@{user.username}" if user.username else l10n.format_value("no")
#    await message.reply(l10n.format_value(msg_id="user-info", args={"name": get_full_name(user),
#                                                                    "id": user.id, "username": u}))


# @router.message(F.reply_to_message, F.from_user.id.in_(config.admin_chat_id))
# async def reply_to_user(message: types.Message, l10n: FluentLocalization):
#    try:
#        user_id = extract_id(message.reply_to_message)
#    except ValueError as ex:
#        return await message.reply(str(ex))

#    try:
#        await message.copy_to(user_id)
#    except TelegramAPIError as ex:
#        await message.reply(
#            l10n.format_value(
#                msg_id="cannot-answer-to-user-error",
#                args={"error": ex.message})
#        )


@router.message(Command(commands="online", ignore_case=True), F.from_user.id.in_(config.admins))
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


@router.message(Command(commands="offline", ignore_case=True), F.from_user.id.in_(config.admins))
@flags.chat_action("typing")
async def offline_cmd(message: types.Message, session: AsyncSession):
    first_name = message.chat.first_name
    await session.execute(delete(Calendar))
    await session.execute(delete(StreamEmails))
    await session.commit()
    text = f"Личность подтверждена! Уважаемый, {first_name}, выключаю прием дэмок"
    await message.reply(text)


@router.message(F.from_user.id.in_(config.admins), Command(commands="help"))
@flags.chat_action("typing")
async def info(message: types.Message):
    uid = message.from_user.id
    if uid in config.banned_user_ids:
        text = "не хочу с тобой разговаривать"
        await message.reply(text, parse_mode=None)
    else:
        text = "Для запуска приема демок напиши /online и укажи дату окончания приема демок\n" \
               "Например: /online 22.04.2023 23:59\n" \
               "Не забудь потом написать /offline" \
               "\n" \
               "© PPRFNK Tech Team"
        await message.reply(text, parse_mode=None)


@router.message(Command(commands="money"), F.from_user.id.in_(config.admins))
@flags.chat_action("typing")
async def usage(message: types.Message):
    openai = OpenAI()
    text = openai.get_money()
    await message.reply(text, parse_mode=None)


@router.message(Command(commands="emails"), F.from_user.id.in_(config.admins))
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


@router.message(Command(commands="stream", ignore_case=True), F.from_user.id.in_(config.admins))
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
    kb.add(InlineKeyboardButton(text="DNB Курс - только девушки! 🤖🤖🤖", callback_data="girls"))
    kb.adjust(2)

    await message.reply("Надо чат выбрать:", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(Command(commands="getmail", ignore_case=True), F.from_user.id.in_(config.admins))
@flags.chat_action("typing")
async def stream_cmd(message: types.Message, state: FSMContext):
    await state.update_data(chatid=message.chat.id)
    kb = InlineKeyboardBuilder()
    kb.add(InlineKeyboardButton(text="Нейропанк Академия", callback_data="course_academy"))
    kb.add(InlineKeyboardButton(text="PRO (КОНТЕНТ ПО ПОДПИСКЕ)", callback_data="course_np_pro"))
    kb.add(InlineKeyboardButton(text="ЛИКВИД КУРС", callback_data="course_liquid"))
    kb.add(InlineKeyboardButton(text="НАЧАЛЬНЫЙ #1 - от 0 до паладина!", callback_data="course_np_basic"))
    kb.add(InlineKeyboardButton(text="SUPER PRO#1 (DNB)", callback_data="course_super_pro"))
    kb.add(InlineKeyboardButton(text="НЕЙРОФАНК КУРС ", callback_data="course_neuro"))
    kb.add(InlineKeyboardButton(text="NERV3 Продуктивность Level 99 #1", callback_data="course_nerve"))
    kb.add(InlineKeyboardButton(text="DNB Курс - только девушки! 🤖🤖🤖", callback_data="course_girls"))
    kb.adjust(2)

    await message.reply("С какого курса тебе дать почты?", reply_markup=kb.as_markup(resize_keyboard=True))


@router.message(Command(commands=['delete_email'], ignore_case=True), F.from_user.id.in_(config.admins))
async def delete_email_command(message: types.Message, session: AsyncSession):
    manager = UserManager(session)
    args_text = message.text.partition(' ')[2]
    args = args_text.split(', ')
    if len(args) != 2:
        await message.reply("Пожалуйста, укажите название курса, как в телеграм и электронную почту для удаления в формате: /delete_email Курс Название, email@gmail.com")
        return

    course_name, email = args
    success = await UserManager.delete_email_from_course(manager, course_name=course_name, email=email)
    if success:
        await message.reply(f"Электронная почта {email} успешно удалена из курса {course_name}.")
    else:
        await message.reply("Не удалось удалить электронную почту. Проверьте правильность введенных данных.")
