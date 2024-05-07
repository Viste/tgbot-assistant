import asyncio
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand
from aioredis.client import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization, FluentResourceLoader

from app import app
from core import setup_routers
from database.databasemanager import DatabaseManager
from database.models import NeuropunkPro
from middlewares.database import DbSessionMiddleware
from middlewares.l10n import L10nMiddleware
from tools.dependencies import container
from tools.shared import session_maker
from tools.utils import config as conf
from tools.utils import np_pro_chat, load_config

redis_client = Redis(host=conf.redis.host, port=conf.redis.port, db=conf.redis.db, decode_responses=True)
db_middleware = DbSessionMiddleware(session_pool=session_maker)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                    stream=sys.stdout)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    commands = [BotCommand(command="course", description="Купить PRO курс/Zoom по подписке"),
                BotCommand(command="help", description="Помощь"),
                BotCommand(command="academy", description="Получения контента с общего потока нейропанк академии"),
                BotCommand(command="reg", description="Регистрация на бесплатном курсе FL21!!! РАБОТАЕТ ТОЛЬКО В СПЕЦ РАЗДЕЛЕ КУРСА!!!!"),]
    await bot.set_my_commands(commands)


async def check_subscriptions_and_unban():
    async with session_maker() as session:
        manager = DatabaseManager(session)
        connect = await load_config(session_maker)
        paper = Bot(token=connect.token)
        chat_member_ids = await manager.get_all_chat_member_telegram_ids()

        for telegram_id in chat_member_ids:
            try:
                # Проверяем, является ли пользователь участником чата
                member = await paper.get_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
                logger.info('Get Chat Member result: %s', member.status)
                if member.status == ChatMemberStatus.MEMBER:
                    # Проверяем статус подписки
                    is_subscription_active = await manager.is_subscription_active(telegram_id, NeuropunkPro)
                    user = await manager.get_user(telegram_id, NeuropunkPro)
                    logger.info("Info about User. Who: %s, %s Sub. end: %s", user.telegram_id, user.telegram_username, user.subscription_end)

                    if user and user.subscription_end:
                        days_until_subscription_end = (user.subscription_end - datetime.utcnow()).days
                        # Уведомляем пользователя за 7 дней до окончания подписки
                        if days_until_subscription_end <= 7:
                            try:
                                await paper.send_message(chat_id=telegram_id, text=f"Не забудьте продлить подписку на курс НЕЙРОПАНК PRO (КОНТЕНТ ПО ПОДПИСКЕ) by Paperclip!\nОсталось дней до конца подписки {days_until_subscription_end}!\n Дата окончания: {user.subscription_end}.")
                                logger.info(f"Notified user {telegram_id} about subscription ending in 7 days")
                            except TelegramForbiddenError as e:
                                logger.error(f"Failed to start conversation member for user {telegram_id}: {e}")
                                continue  # Продолжаем обработку следующих пользователей

                    if is_subscription_active is False:
                        # Если подписка истекла сегодня
                        if user is None or (user.subscription_end and datetime.utcnow() >= user.subscription_end):
                            try:
                                await paper.unban_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
                            except Exception as e:
                                logger.info(f"Kick user {telegram_id} failed because {e} in chat -1001814931266")
                                continue
                            try:
                                await paper.send_message(chat_id=telegram_id, text="Ваша подписка на Нейропанк Про закончилась. Вы были удалены из чата.")
                            except TelegramForbiddenError as e:
                                logger.error(f"Failed to start conversation member for user {telegram_id}: {e}")
                                continue
                            await manager.delete_neuropunk_pro_user(telegram_id)
                            logger.info(f"Kicked user {telegram_id} from chat -1001814931266")
            except TelegramBadRequest as e:
                logger.error(f"Failed to get chat member for user {telegram_id}: {e}")
                continue


def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


async def main():
    locales_dir = Path(__file__).parent.joinpath("locales")
    l10n_loader = FluentResourceLoader(str(locales_dir) + "/{locale}")
    l10n = FluentLocalization(["ru"], ["strings.ftl", "errors.ftl"], l10n_loader)
    config = await load_config(session_maker)
    container.add('config', config)
    paper = Bot(token=config.token)

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT, events_isolation=SimpleEventIsolation())
    router = setup_routers()
    worker.update.middleware(db_middleware)
    worker.update.middleware(L10nMiddleware(l10n))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(paper)
    logger.info("Starting bot")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions_and_unban, 'interval', hours=12)

    scheduler.start()
    await worker.start_polling(paper, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
