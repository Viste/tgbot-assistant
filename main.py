import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.strategy import FSMStrategy
from aioredis.client import Redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from fluent.runtime import FluentLocalization, FluentResourceLoader
from middlewares.l10n import L10nMiddleware
from pathlib import Path

from core import setup_routers
from middlewares.database import DbSessionMiddleware
from tools.utils import config

redis_client = Redis(host=config.redis.host, port=config.redis.port, db=config.redis.db, decode_responses=True)
paper = Bot(token=config.token, parse_mode="HTML")

engine = create_async_engine(url=config.db_url, echo=True, echo_pool=False, pool_size=50, max_overflow=30,
                             pool_timeout=30, pool_recycle=3600)
session_maker = async_sessionmaker(engine, expire_on_commit=False)
db_middleware = DbSessionMiddleware(session_pool=session_maker)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    stream=sys.stdout,)

logger = logging.getLogger(__name__)


async def main():
    locales_dir = Path(__file__).parent.joinpath("locales")
    l10n_loader = FluentResourceLoader(str(locales_dir) + "/{locale}")
    l10n = FluentLocalization(["ru"], ["strings.ftl", "errors.ftl"], l10n_loader)

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.USER_IN_CHAT)
    router = setup_routers()
    worker.update.middleware(db_middleware)
    worker.update.middleware(L10nMiddleware(l10n))
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    logging.info("Starting bot")
    await worker.start_polling(paper, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.error("Bot stopped!")
