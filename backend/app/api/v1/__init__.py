from fastapi import APIRouter
from app.api.v1.schemes import router as schemes_router
from app.api.v1.matching import router as matching_router
from app.api.v1.users import router as users_router
from app.api.v1.admin import router as admin_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(schemes_router, prefix="/schemes", tags=["Schemes"])
api_router.include_router(matching_router, prefix="/matching", tags=["AI Scheme Matching"])
api_router.include_router(users_router, prefix="/users", tags=["Entrepreneurs"])
api_router.include_router(admin_router, tags=["Admin & Operations"])


@api_router.get("/status", tags=["Status"])
async def check_api_status():
    return {
        "status": "online",
        "version": "v1",
        "description": "AI-Driven Scheme Matching Engine API"
    }
