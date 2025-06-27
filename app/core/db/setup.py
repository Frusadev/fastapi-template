from sqlite3 import OperationalError

from sqlalchemy.ext.asyncio.engine import AsyncEngine, create_async_engine

from app.core.config.env import get_env
from app.core.logging.log import log_error, log_success

engine: AsyncEngine = create_async_engine(get_env("DB_STRING"))


async def setup_db():
    try:
        async with engine.connect():
            log_success("Connected to database!")
    except OperationalError as e:
        log_error(f"Error connecting to DB: {e}")


async def create_db_session():
    from sqlmodel.ext.asyncio.session import AsyncSession

    async with AsyncSession(engine) as session:
        yield session
