from fastapi import APIRouter
from app.api.v1.endpoints import crawler, analysis, monitoring

api_router = APIRouter()

api_router.include_router(crawler.router, prefix="/crawler", tags=["crawler"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
