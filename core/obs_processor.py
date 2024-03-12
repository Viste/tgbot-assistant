import html
import logging

from aiogram import types, F, Router, Bot

from core.helpers.obs import ClientOBS
from core.helpers.tools import basic_chat_filter
from filters.activity import IsActiveChatFilter
from tools.utils import config

router = Router()
logger = logging.getLogger(__name__)


@router.message(IsActiveChatFilter(), basic_chat_filter, F.content_type.in_({'text', 'animation', 'sticker', 'photo'}))
async def process_obs_content(message: types.Message, bot: Bot) -> None:
    logger.info("%s", message)
    nickname = message.from_user.full_name
    content = None

    if message.content_type == 'text':
        content = html.escape(message.text)
    elif message.content_type in ['animation', 'sticker', 'photo']:
        content_id = None
        if message.content_type == 'photo':
            content_id = message.photo[-1].file_id
        elif message.content_type == 'animation':
            content_id = message.animation.file_id
        elif message.content_type == 'sticker':
            content_id = message.sticker.thumbnail.file_id

        if content_id:
            file_info = await bot.get_file(content_id)
            content = f"https://api.telegram.org/file/bot{config.token}/{file_info.file_path}"

    if content:
        async with ClientOBS() as client:
            await client.send_request(nickname, content)
