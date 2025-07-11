from fastapi import APIRouter
from .endpoints import router as endpoints_router

router = APIRouter(
    prefix="/frontend",
    tags=["frontend"]
)

router.include_router(endpoints_router) 