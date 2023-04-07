import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.redis import RedisStorage

from core import setup_routers
from tools.utils import config
from aioredis.client import Redis

redis_client = Redis.from_url(config.redis_url)
paper = Bot(token=config.token, parse_mode="HTML")


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        stream=sys.stdout,
    )

    storage = RedisStorage(redis=redis_client)
    worker = Dispatcher(storage=storage, fsm_strategy=FSMStrategy.GLOBAL_USER)
    router = setup_routers()
    worker.include_router(router)
    useful_updates = worker.resolve_used_update_types()
    logging.info("Starting bot")
    await worker.start_polling(paper, allowed_updates=useful_updates, handle_signals=True)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
