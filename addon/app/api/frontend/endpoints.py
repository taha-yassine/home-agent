from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db
from ...models.conversation import ConversationList
from ...models.trace import Span
from ...services.conversation import ConversationService
from ...services.trace import TraceService

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

