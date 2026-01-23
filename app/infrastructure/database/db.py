from config.config import get_config

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

config = get_config()

engine = create_async_engine(url=config.postgres.url, echo=True)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
