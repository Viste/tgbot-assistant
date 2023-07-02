import logging
from asyncio import create_task, sleep

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import ContentType
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from fluent.runtime import FluentLocalization

from core.helpers.tools import banned, shadowbanned
from tools.utils import config
from tools.states import AnsMa
from filters.media import SupportedMediaFilter

logger = logging.getLogger(__name__)
router = Router()


async def _send_expiring_notification(message: Message, l10n: FluentLocalization):
    msg = await message.reply(l10n.format_value("sent-confirmation"))
    if config.remove_sent_confirmation:
        await sleep(5.0)
        await msg.delete()


@router.message(Command(commands=["start"]))
async def cmd_start(message: Message, l10n: FluentLocalization, state: FSMContext):
    await state.set_state(AnsMa.get)
    await message.answer(l10n.format_value("intro"))


@router.message(F.text, AnsMa.get)
async def text_message(message: Message, bot: Bot, l10n: FluentLocalization):
    if len(message.text) > 4000:
        return await message.reply(l10n.format_value("too-long-text-error"))

    if message.from_user.id in banned:
        await message.answer(l10n.format_value("you-were-banned-error"))
    elif message.from_user.id in shadowbanned:
        return
    else:
        await bot.send_message(config.admin_chat_id, message.html_text + f"\n\n#id{message.from_user.id}",
                               parse_mode="HTML")
        create_task(_send_expiring_notification(message, l10n))


@router.message(SupportedMediaFilter(), AnsMa.get)
async def supported_media(message: Message, l10n: FluentLocalization):
    if message.caption and len(message.caption) > 1000:
        return await message.reply(l10n.format_value("too-long-caption-error"))
    if message.from_user.id in banned:
        await message.answer(l10n.format_value("you-were-banned-error"))
    elif message.from_user.id in shadowbanned:
        return
    else:
        await message.copy_to(config.admin_chat_id, caption=((message.caption or "") +
                                                             f"\n\n#id{message.from_user.id}"), parse_mode="HTML")
        create_task(_send_expiring_notification(message, l10n))


@router.message(AnsMa.get)
async def unsupported_types(message: Message, l10n: FluentLocalization):
    if message.content_type not in (ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER,
                                    ContentType.VIDEO_CHAT_STARTED, ContentType.VIDEO_CHAT_ENDED,
                                    ContentType.VIDEO_CHAT_PARTICIPANTS_INVITED, ContentType.SUCCESSFUL_PAYMENT,
                                    ContentType.MESSAGE_AUTO_DELETE_TIMER_CHANGED, ContentType.NEW_CHAT_PHOTO,
                                    ContentType.DELETE_CHAT_PHOTO, "proximity_alert_triggered",
                                    ContentType.NEW_CHAT_TITLE, ContentType.PINNED_MESSAGE):
        await message.reply(l10n.format_value("unsupported-message-type-error"))


@router.message(Command(commands="help"))
async def info_user(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("help"))