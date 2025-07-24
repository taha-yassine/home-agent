import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db
from ...models import (
    Connection,
    ConnectionCreate,
    ConnectionUpdate,
    ConversationList,
    Span,
)
from ...services import (
    ConversationService,
    ConnectionService,
    TraceService,
)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.get("/conversations", response_model=ConversationList)
async def get_conversations(
    db: AsyncSession = Depends(get_db),
) -> ConversationList:
    """Get all conversations."""
    return await ConversationService.get_conversations(db)


@router.get("/traces/{trace_id}/spans", response_model=list[Span])
async def get_spans(
    trace_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[Span]:
    """Get all spans for a given trace."""
    return await TraceService.get_spans_by_trace_id(db, trace_id)


@router.get("/connections", response_model=list[Connection])
async def get_connections(db: AsyncSession = Depends(get_db)) -> list[Connection]:
    """Get all connections."""
    return await ConnectionService.get_connections(db, mask_key=True)


@router.post("/connections", response_model=Connection)
async def create_connection(
    connection_create: ConnectionCreate, db: AsyncSession = Depends(get_db)
) -> Connection:
    """Create a new connection."""
    return await ConnectionService.create_connection(db, connection_create)


@router.put("/connections/{connection_id}", response_model=Connection)
async def update_connection(
    connection_id: int,
    connection_update: ConnectionUpdate,
    db: AsyncSession = Depends(get_db),
) -> Connection:
    """Update a connection."""
    return await ConnectionService.update_connection(db, connection_id, connection_update)


@router.delete("/connections/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    """Delete a connection."""
    await ConnectionService.delete_connection(db, connection_id)


@router.put("/connections/{connection_id}/active", response_model=Connection)
async def set_active_connection(
    connection_id: int, db: AsyncSession = Depends(get_db)
) -> Connection:
    """Set a connection as active."""
    return await ConnectionService.set_active_connection(db, connection_id)


@router.get("/models")
async def get_models(db: AsyncSession = Depends(get_db)):
    """Get all models from the active connection."""
    active_connection = await ConnectionService.get_active_connection(db)
    if not active_connection:
        raise HTTPException(status_code=404, detail="No active connection found")

    # TODO: Use a common client for all connections initialized at startup
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{active_connection.url}/models")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=500, detail=f"Error connecting to connection: {exc}"
            )
        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=exc.response.status_code, detail=exc.response.text
            )

