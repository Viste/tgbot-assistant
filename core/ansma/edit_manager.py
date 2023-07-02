import logging

from aiogram import Router
from aiogram.types import Message
from fluent.runtime import FluentLocalization

logger = logging.getLogger(__name__)

router = Router()


@router.edited_message()
async def edited_message_warning(message: Message, l10n: FluentLocalization):
    await message.reply(l10n.format_value("cannot-update-edited-error"))
