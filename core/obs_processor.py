import html
import logging

from aiogram import types, F, Router, Bot
from fluent.runtime import FluentLocalization

from tools.utils import config
from core.helpers.tools import reply_if_banned, ChatState
from core.helpers.obs import ClientOBS


router = Router()
logger = logging.getLogger(__name__)
router.message.filter(F.chat.type.in_({'group', 'supergroup'}))
state = ChatState()


@router.message(F.content_type.in_({'text'}))
async def process_obs_text(message: types.Message, l10n: FluentLocalization) -> None:
    logging.info("State chat %s", state.active_chat)
    uid = message.from_user.id
    nickname = message.from_user.first_name + " " + (message.from_user.last_name if message.from_user.last_name else "")
    if await reply_if_banned(message, uid, l10n):
        return
    if message.chat.is_forum is True:
        if message.chat.id != state.active_chat or message.message_thread_id != state.thread_id:
            return
        else:
            logging.info("%s", message)
            text = html.escape(message.text)
            async with ClientOBS() as client:
                await client.send_request(nickname, text)
    else:
        if message.chat.id == state.active_chat:
            logging.info("%s", message)
            text = html.escape(message.text)
            async with ClientOBS() as client:
                await client.send_request(nickname, text)
        else:
            return


@router.message(F.content_type.in_({'animation'}))
async def process_obs_gif(message: types.Message, l10n: FluentLocalization, bot: Bot) -> None:
    logging.info("%s", message)
    uid = message.from_user.id
    nickname = message.from_user.first_name + " " + (message.from_user.last_name if message.from_user.last_name else "")
    if await reply_if_banned(message, uid, l10n):
        return
    if message.chat.is_forum is True:
        if message.chat.id != state.active_chat or message.message_thread_id != state.thread_id:
            return
        else:
            logging.info("%s", message)
            file_id = message.animation.file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
    else:
        if message.chat.id == state.active_chat:
            logging.info("%s", message)
            file_id = message.animation.file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
        else:
            return


@router.message(F.content_type.in_({'sticker'}))
async def process_obs_sticker(message: types.Message, l10n: FluentLocalization, bot: Bot) -> None:
    uid = message.from_user.id
    nickname = message.from_user.first_name + " " + (message.from_user.last_name if message.from_user.last_name else "")
    if await reply_if_banned(message, uid, l10n):
        return
    if message.chat.is_forum is True:
        if message.chat.id != state.active_chat or message.message_thread_id != state.thread_id:
            return
        else:
            logging.info("%s", message)
            file_id = message.sticker.thumbnail.file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
    else:
        if message.chat.id == state.active_chat:
            logging.info("%s", message)
            file_id = message.sticker.thumbnail.file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
        else:
            return


@router.message(F.content_type.in_({'photo'}))
async def process_obs_image(message: types.Message, l10n: FluentLocalization, bot: Bot) -> None:
    uid = message.from_user.id
    nickname = message.from_user.first_name + " " + (message.from_user.last_name if message.from_user.last_name else "")
    if await reply_if_banned(message, uid, l10n):
        return
    if message.chat.is_forum is True:
        if message.chat.id != state.active_chat or message.message_thread_id != state.thread_id:
            return
        else:
            logging.info("%s", message)
            file_id = message.photo[-1].file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
    else:
        if message.chat.id == state.active_chat:
            logging.info("%s", message)
            file_id = message.photo[-1].file_id
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"
            async with ClientOBS() as client:
                await client.send_request(nickname, file_url)
        else:
            return
