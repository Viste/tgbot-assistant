from aiogram import Router
from aiogram.types import Message
from fluent.runtime import FluentLocalization


router = Router()


@router.edited_message()
async def edited_message_warning(message: Message, l10n: FluentLocalization):
    await message.reply(l10n.format_value("cannot-update-edited-error"))
