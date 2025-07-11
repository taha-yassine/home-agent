from fastapi import APIRouter
from .agent.router import router as agent_router
from .frontend.router import router as frontend_router

router = APIRouter(prefix="/api")

router.include_router(agent_router)
router.include_router(frontend_router) 