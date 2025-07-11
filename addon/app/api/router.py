from fastapi import APIRouter
from .agent.router import router as agent_router

router = APIRouter(prefix="/api")

router.include_router(agent_router)