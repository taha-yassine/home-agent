from fastapi import APIRouter, Depends, Request
from typing import List
import httpx
from openai import AsyncOpenAI

from agents import Tool
from ...models import ConversationRequest, ConversationResponse
from ...services import ConversationService

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
    openai_client: AsyncOpenAI = Depends(get_openai_client),
    hass_client: httpx.AsyncClient = Depends(get_hass_client),
    tools: List[Tool] = Depends(get_tools),
    model_id: str = Depends(get_model_id),
):
    """Process a conversation with the agent."""
    return await ConversationService.process_conversation(
        conversation_request=conversation_request,
        openai_client=openai_client,
        hass_client=hass_client,
        tools=tools,
        model_id=model_id,
    ) 