import logging
from aiogram import Router, F
from aiogram.types import Message
from fluent.runtime import FluentLocalization

from tools.utils import config

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.reply_to_message, F.chat.id_in_(config.admin_chat_id), F.poll)
async def unsupported_admin_reply_types(message: Message, l10n: FluentLocalization):
    await message.reply(l10n.format_value("cannot-reply-with-this-type-error"))
