from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from collections.abc import AsyncGenerator
from sqlalchemy import Engine
from openai import AsyncOpenAI
import httpx
from typing import List
from agents import Tool


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get an async database session."""
    db = request.state.db
    async with db() as session:
        yield session 


def get_sync_db(request: Request) -> Engine:
    """Dependency to get a sync database session."""
    return request.state.db_sync_engine


def get_openai_client(request: Request) -> AsyncOpenAI:
    return request.state.openai_client


def get_hass_client(request: Request) -> httpx.AsyncClient:
    return request.state.hass_client


def get_tools(request: Request) -> List[Tool]:
    return request.state.tools


def get_agent_session_engine(request: Request) -> AsyncEngine:
    return request.state.agent_session_engine