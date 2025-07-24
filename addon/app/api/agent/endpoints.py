from fastapi import APIRouter, Depends, Request
from typing import List
import httpx
from openai import AsyncOpenAI
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from agents import Tool
from ...models import ConversationRequest, ConversationResponse
from ...services import ConversationService
from ...dependencies import get_sync_db, get_db

def get_openai_client(request: Request) -> AsyncOpenAI:
    return request.state.openai_client

def get_hass_client(request: Request) -> httpx.AsyncClient:
    return request.state.hass_client

def get_tools(request: Request) -> List[Tool]:
    return request.state.tools

def get_model_id(request: Request) -> str:
    return request.state.model_id

router = APIRouter()

@router.post("/conversation", response_model=ConversationResponse)
async def process_conversation(
    conversation_request: ConversationRequest,
    hass_client: httpx.AsyncClient = Depends(get_hass_client),
    tools: List[Tool] = Depends(get_tools),
    db: AsyncSession = Depends(get_db),
    db_engine: Engine = Depends(get_sync_db),
):
    """Process a conversation with the agent."""
    return await ConversationService.process_conversation(
        conversation_request=conversation_request,
        hass_client=hass_client,
        tools=tools,
        db=db,
        db_engine=db_engine,
    ) 