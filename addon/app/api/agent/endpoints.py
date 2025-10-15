from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from typing import List
import httpx
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession

from agents import Tool
from ...models import ConversationRequest, ConversationResponse
from ...services import ConversationService
from ...dependencies import get_sync_db, get_db, get_hass_client, get_tools, get_agent_session_engine


router = APIRouter()

@router.post("/conversation")
async def process_conversation(
    conversation_request: ConversationRequest,
    stream: bool = Query(False),
    hass_client: httpx.AsyncClient = Depends(get_hass_client),
    tools: List[Tool] = Depends(get_tools),
    db: AsyncSession = Depends(get_db),
    db_engine: Engine = Depends(get_sync_db),
    session_engine: AsyncEngine = Depends(get_agent_session_engine),
):
    """Process a conversation with the agent. If stream=true, respond via SSE."""

    if stream:
        async def event_generator():
            async for chunk in ConversationService.process_conversation(
                conversation_request=conversation_request,
                hass_client=hass_client,
                tools=tools,
                db=db,
                db_engine=db_engine,
                session_engine=session_engine,
            ):
                yield chunk

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    # Non-streaming
    final_text = ""
    async for chunk in ConversationService.process_conversation(
        conversation_request=conversation_request,
        hass_client=hass_client,
        tools=tools,
        db=db,
        db_engine=db_engine,
        session_engine=session_engine,
    ):
        final_text += chunk

    return ConversationResponse(response=final_text)