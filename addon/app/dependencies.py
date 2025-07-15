from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from collections.abc import AsyncGenerator
from sqlalchemy import Engine


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session."""
    db = request.state.db
    async with db() as session:
        yield session 


def get_sync_db(request: Request) -> Engine:
    """Dependency to get a sync database session."""
    return request.state.db_sync_engine