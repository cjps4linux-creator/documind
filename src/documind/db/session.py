from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from documind.db.engine import engine
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autocommit=False, autoflush=False)
async def get_async_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
