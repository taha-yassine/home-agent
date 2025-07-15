from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...dependencies import get_db
from ...models.conversation import ConversationList
from ...services.conversation import ConversationService

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
