from aiogram import Router, F
from aiogram.types import ContentType, Message
from fluent.runtime import FluentLocalization

from tools.utils import config

router = Router()
router.message.filter(F.chat.id == config.admin_chat_id)


@router.message(~F.reply_to_message)
async def has_no_reply(message: Message, l10n: FluentLocalization):
    if message.content_type not in (ContentType.NEW_CHAT_MEMBERS, ContentType.LEFT_CHAT_MEMBER):
        await message.reply(l10n.format_value("no-reply-error"))
