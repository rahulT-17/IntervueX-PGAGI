from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RetrievalLog


async def log_retrieval(
    db: AsyncSession,
    session_id: int,
    query: str,
    chunks: list[dict],
) -> None:
    log = RetrievalLog(
        session_id=session_id,
        generated_query=query,
        retrieved_chunks=chunks,
    )
    db.add(log)
    await db.commit()