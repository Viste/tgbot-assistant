from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from tools.utils import config

engine = create_async_engine(url=config.db_url, echo=True, echo_pool=False, pool_size=50, max_overflow=30,
                             pool_timeout=30, pool_recycle=3600)
session_maker = async_sessionmaker(engine, expire_on_commit=False)
