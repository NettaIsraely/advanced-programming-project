import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tlvflow.persistence.degraded_vehicles_repository import DegradedVehiclesRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.maintenance_repository import MaintenanceRepository
from tlvflow.services.vehicles_service import treat_vehicles

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vehicles"])


@router.post("/vehicle/treat")  # type: ignore[misc]
async def treat(request: Request) -> JSONResponse:
    """Treat all eligible vehicles and return their IDs."""
    vehicles_repo = getattr(request.app.state, "vehicle_repository", None)
    stations_repo = getattr(request.app.state, "station_repository", None)

    if vehicles_repo is None or not isinstance(vehicles_repo, VehicleRepository):
        logger.error("vehicle_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Vehicle repository not initialized"},
        )

    if stations_repo is None or not isinstance(stations_repo, StationRepository):
        logger.error("station_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Station repository not initialized"},
        )

    maintenance_repo = getattr(request.app.state, "maintenance_repository", None)
    if maintenance_repo is None or not isinstance(
        maintenance_repo, MaintenanceRepository
    ):
        logger.error("maintenance_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Maintenance repository not initialized"},
        )

    degraded_repo = getattr(request.app.state, "degraded_vehicles_repository", None)
    if degraded_repo is None or not isinstance(
        degraded_repo, DegradedVehiclesRepository
    ):
        logger.error("degraded_vehicles_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Degraded vehicles repository not initialized"},
        )

    treated_ids = treat_vehicles(
        vehicles_repo, stations_repo, maintenance_repo, degraded_repo
    )
    return JSONResponse(content={"treated_vehicles": treated_ids})
