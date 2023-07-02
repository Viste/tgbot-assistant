import logging
from contextlib import suppress

from aiogram import Router, F, types
from aiogram.filters import Command
from fluent.runtime import FluentLocalization

from core.helpers.tools import banned, shadowbanned, update_config
from tools.utils import config
logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type.in_({'private'}))


@router.message(Command(commands=["ban"]), F.reply_to_message, F.from_user.id.in_(config.admin_chat_id))
async def cmd_ban(message: types.Message, l10n: FluentLocalization):
    try:
        entities = message.entities or message.caption_entities
        logging.info("entities: %s", entities)
        if not entities or entities[-1].type != "hashtag":
            raise ValueError("Не удалось извлечь ID для ответа!")
        hashtag = entities[-1].extract_from(message.text or message.caption)
        logging.info("hashtag: %s", int(hashtag[3:]))
        if len(hashtag) < 4 or not hashtag[3:].isdigit():
            raise ValueError("Некорректный ID для ответа!")

        user_id = int(hashtag[3:])
        logging.info("BAN EXTRACTED")
        banned.add(int(user_id))
        update_config()
        await message.reply(l10n.format_value(msg_id="user-banned", args={"id": user_id}))
    except ValueError as ex:
        return await message.reply(str(ex))


@router.message(Command(commands=["shadowban"]), F.reply_to_message, F.from_user.id.in_(config.admin_chat_id))
async def cmd_shadowban(message: types.Message, l10n: FluentLocalization):
    try:
        entities = message.entities or message.caption_entities
        logging.info("entities: %s", entities)
        if not entities or entities[-1].type != "hashtag":
            raise ValueError("Не удалось извлечь ID для ответа!")
        hashtag = entities[-1].extract_from(message.text or message.caption)
        logging.info("hashtag: %s", int(hashtag[3:]))
        if len(hashtag) < 4 or not hashtag[3:].isdigit():
            raise ValueError("Некорректный ID для ответа!")

        user_id = int(hashtag[3:])
        shadowbanned.add(int(user_id))
        update_config()
        await message.reply(l10n.format_value(msg_id="user-shadowbanned", args={"id": user_id}))
    except ValueError as ex:
        return await message.reply(str(ex))


@router.message(Command(commands=["unban"]), F.reply_to_message, F.from_user.id.in_(config.admin_chat_id))
async def cmd_unban(message: types.Message, l10n: FluentLocalization):
    try:
        entities = message.entities or message.caption_entities
        logging.info("entities: %s", entities)
        if not entities or entities[-1].type != "hashtag":
            raise ValueError("Не удалось извлечь ID для ответа!")
        hashtag = entities[-1].extract_from(message.text or message.caption)
        logging.info("hashtag: %s", int(hashtag[3:]))
        if len(hashtag) < 4 or not hashtag[3:].isdigit():
            raise ValueError("Некорректный ID для ответа!")

        user_id = int(hashtag[3:])
    except ValueError as ex:
        return await message.reply(str(ex))
    user_id = int(user_id)
    with suppress(KeyError):
        banned.remove(user_id)
    with suppress(KeyError):
        shadowbanned.remove(user_id)
    update_config()
    await message.reply(l10n.format_value(msg_id="user-unbanned", args={"id": user_id}))


@router.message(Command(commands=["list_banned"]))
async def cmd_list_banned(message: types.Message, l10n: FluentLocalization):
    has_bans = len(banned) > 0 or len(shadowbanned) > 0
    if not has_bans:
        await message.answer(l10n.format_value("no-banned"))
        return
    result = []
    if len(banned) > 0:
        result.append(l10n.format_value("list-banned-title"))
        for item in banned:
            result.append(f"• #id{item}")
    if len(shadowbanned) > 0:
        result.append('\n{}'.format(l10n.format_value("list-shadowbanned-title")))
        for item in shadowbanned:
            result.append(f"• #id{item}")

    await message.answer("\n".join(result))
