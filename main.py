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
from aiogram.types import BotCommand
from aioredis.client import Redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fluent.runtime import FluentLocalization, FluentResourceLoader
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core import setup_routers
from database.manager import Manager
from database.models import NeuropunkPro
from middlewares.basic import BasicMiddleware
from middlewares.database import DbSessionMiddleware
from middlewares.l10n import L10nMiddleware
from tools.dependencies import container
from tools.utils import config as conf
from tools.utils import np_pro_chat, load_config

redis_client = Redis(host=conf.redis.host, port=conf.redis.port, db=conf.redis.db, decode_responses=True)
engine = create_async_engine(url=conf.db_url, echo=True, echo_pool=False, pool_size=50, max_overflow=30,
                             pool_timeout=30, pool_recycle=3600)
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

async def check_subscriptions_and_unban():
    async with session_maker() as session:
        manager = Manager(session)
        con = await load_config(session_maker)
        paper = Bot(token=con.token)
        chat_member_ids = await manager.get_all_chat_member_telegram_ids()

        for telegram_id in chat_member_ids:
            # Проверяем, является ли пользователь участником чата
            member = await paper.get_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
            logger.info('Get Chat Member result: %s', member.status)
            if member.status == ChatMemberStatus.MEMBER:
                # Проверяем статус подписки
                is_subscription_active = await manager.is_subscription_active(telegram_id, NeuropunkPro)
                if not is_subscription_active:
                    user = await manager.get_user(telegram_id, NeuropunkPro)
                    logger.info("Info about User: %s", user)
                    # Если пользователь не найден в таблице или подписка истекла более чем на 2 дня
                    if user is None or (user.subscription_end and datetime.utcnow() - user.subscription_end > timedelta(days=2)):
                        await paper.unban_chat_member(chat_id=np_pro_chat, user_id=telegram_id)
                        logger.info(f"Unbanned user {telegram_id} in chat -1001814931266")


async def task_wrapper():
    async with session_maker() as session:
        manager = Manager(session)
        await manager.remove_duplicate_chat_members()


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
    router.message.middleware(BasicMiddleware(session_maker))
    worker.update.middleware(db_middleware)
    worker.update.middleware(L10nMiddleware(l10n))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    await set_bot_commands(paper)
    # await set_bot_admin_commands(paper)
    logger.info("Starting bot")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_subscriptions_and_unban, 'interval', hours=12)
    scheduler.add_job(task_wrapper, 'interval', minutes=45)

    scheduler.start()
    await worker.start_polling(paper, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
