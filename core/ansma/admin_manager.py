from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import Message, Chat
from fluent.runtime import FluentLocalization

from tools.utils import config

router = Router()
router.message.filter(F.chat.id == config.admin_chat_id)


def extract_id(message: Message) -> int:
    entities = message.entities or message.caption_entities
    if not entities or entities[-1].type != "hashtag":
        raise ValueError("Не удалось извлечь ID для ответа!")
    hashtag = entities[-1].extract_from(message.text or message.caption)
    if len(hashtag) < 4 or not hashtag[3:].isdigit():
        raise ValueError("Некорректный ID для ответа!")

    return int(hashtag[3:])


@router.message(Command(commands=["get", "who"]), F.reply_to_message)
async def get_user_info(message: Message, bot: Bot, l10n: FluentLocalization):
    def get_full_name(chat: Chat):
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
        await message.reply(
            l10n.format_value(
                msg_id="cannot-get-user-info-error",
                args={"error": ex.message})
        )
        return

    u = f"@{user.username}" if user.username else l10n.format_value("no")
    await message.reply(
        l10n.format_value(
            msg_id="user-info",
            args={
                "name": get_full_name(user),
                "id": user.id,
                "username": u
            }
        )
    )


@router.message(F.reply_to_message)
async def reply_to_user(message: Message, l10n: FluentLocalization):
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
