from fastapi import APIRouter

from tlvflow.api.routers.health_router import router as health_router
from tlvflow.api.routers.stations_router import router as stations_router

router = APIRouter()
router.include_router(health_router)
router.include_router(stations_router)
