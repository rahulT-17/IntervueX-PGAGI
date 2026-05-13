from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.base import Base, engine
from app import models  # ensures models are imported so metadata is registered


async def init_db(db_engine: AsyncEngine = engine) -> None:
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)