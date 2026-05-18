from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from .core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Automatically derive synchronous PostgreSQL URL from the async connection URL if it has been updated
db_url_sync = settings.DATABASE_URL_SYNC
if settings.DATABASE_URL != "postgresql+asyncpg://postgres:postgres@localhost:5432/clinic_db":
    if db_url_sync == "postgresql://postgres:postgres@localhost:5432/clinic_db" or not db_url_sync:
        db_url_sync = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://").replace("postgres+asyncpg://", "postgres://")

sync_engine = create_engine(db_url_sync, echo=settings.DEBUG)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)