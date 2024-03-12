import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aiogram.types import BotCommand, BotCommandScopeChat
from aioredis.client import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization, FluentResourceLoader
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core import setup_routers
from database.manager import UserManager
from middlewares.basic import BasicMiddleware
from middlewares.database import DbSessionMiddleware
from middlewares.l10n import L10nMiddleware
from tools.utils import config, np_pro_chat

redis_client = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db, decode_responses=True)
engine = create_async_engine(url=config.db_url, echo=True, echo_pool=False, pool_size=50, max_overflow=30,
                             pool_timeout=30, pool_recycle=3600)
paper = Bot(token=config.token, parse_mode="HTML")
session_maker = async_sessionmaker(engine, expire_on_commit=False)
db_middleware = DbSessionMiddleware(session_pool=session_maker)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
                    stream=sys.stdout)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    commands = [BotCommand(command="course_register", description="Купить PRO курс по подписке"),
                BotCommand(command="help", description="Помощь"),
                BotCommand(command="demo", description="Прислать демку"), ]
    await bot.set_my_commands(commands)


async def set_bot_admin_commands(bot: Bot):
    commands = [BotCommand(command="online", description="+ дата включить прием демок"),
                BotCommand(command="offline", description="Выключить прием демок"),
                BotCommand(command="stream", description="Переключить чат стрима"),
                BotCommand(command="/get_active_emails", description="получить список адресов мужиков с подпиской"), ]
    for admin in config.admins:
        await bot.set_my_commands(commands, scope=BotCommandScopeChat(chat_id=admin))


async def check_subscriptions_and_unban():
    async with session_maker() as session:
        user_manager = UserManager(session)
        chat_member_ids = await user_manager.get_all_chat_member_telegram_ids()

        for telegram_id in chat_member_ids:
            # Проверяем, является ли пользователь участником чата
            member = await paper.get_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
            logger.info('Get Chat Member result: %s', member.status)
            if member.status == ChatMemberStatus.MEMBER:
                # Проверяем статус подписки
                is_subscription_active = await user_manager.is_subscription_active(telegram_id)
                if not is_subscription_active:
                    user = await user_manager.get_course_user(telegram_id)
                    if user and user.subscription_end and datetime.utcnow() - user.subscription_end > timedelta(days=2):
                        await paper.unban_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
                        logger.info(f"Unbanned user {telegram_id} in chat -1001814931266")


async def task_wrapper():
    async with session_maker() as session:
        user_manager = UserManager(session)
        await user_manager.remove_duplicate_chat_members()


async def main():
    locales_dir = Path(__file__).parent.joinpath("locales")
    l10n_loader = FluentResourceLoader(str(locales_dir) + "/{locale}")
    l10n = FluentLocalization(["ru"], ["strings.ftl", "errors.ftl"], l10n_loader)

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT, events_isolation=SimpleEventIsolation())
    router = setup_routers()
    router.message.middleware(BasicMiddleware(session_maker))
    worker.update.middleware(db_middleware)
    worker.update.middleware(L10nMiddleware(l10n))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(paper)
    await set_bot_admin_commands(paper)
    logger.info("Starting bot")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions_and_unban, 'interval', minutes=10)
    scheduler.add_job(task_wrapper, 'interval', minutes=30)

    scheduler.start()
    await worker.start_polling(paper, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
