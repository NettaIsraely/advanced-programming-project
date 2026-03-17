import logging

from fastapi import APIRouter, HTTPException, Request

from tlvflow.api.schemas import (
    RideEndRequest,
    RideEndResponse,
    RideStartRequest,
    RideStartResponse,
)
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.users_repository import UsersRepository
from tlvflow.services.rides_service import end_ride, start_ride

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rides"])


@router.post("/rides/start", response_model=RideStartResponse, status_code=201)  # type: ignore[misc]
async def start(request: Request, body: RideStartRequest) -> RideStartResponse:
    """Start a new ride for a user from a specific station."""

    # Fetching repos
    rides_repo = getattr(request.app.state, "rides_repository", None)
    active_users_repo = getattr(request.app.state, "active_users_repository", None)
    station_repo = getattr(request.app.state, "station_repository", None)
    users_repo = getattr(request.app.state, "users_repository", None)

    # Validate repos
    if rides_repo is None or not isinstance(rides_repo, RidesRepository):
        logger.error("rides_repository not initialized on app.state")
        raise HTTPException(status_code=500, detail="Rides repository not initialized")

    if active_users_repo is None or not isinstance(
        active_users_repo, ActiveUsersRepository
    ):
        logger.error("active_users_repository not initialized on app.state")
        raise HTTPException(
            status_code=500, detail="Active users repository not initialized"
        )

    if station_repo is None or not isinstance(station_repo, StationRepository):
        logger.error("station_repository not initialized on app.state")
        raise HTTPException(
            status_code=500, detail="Station repository not initialized"
        )

    if users_repo is None or not isinstance(users_repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        raise HTTPException(status_code=500, detail="Users repository not initialized")

    try:
        ride_id, vehicle_id = start_ride(
            user_id=body.user_id,
            station_id=body.station_id,
            rides_repo=rides_repo,
            active_users_repo=active_users_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )
    except ValueError as exc:
        msg = str(exc)
        if "already has an active ride" in msg:
            raise HTTPException(status_code=409, detail=msg)
        if "not found" in msg:
            raise HTTPException(status_code=404, detail=msg)

        raise HTTPException(status_code=400, detail=msg)

    return RideStartResponse(
        ride_id=ride_id, vehicle_id=vehicle_id, station_id=body.station_id
    )


@router.post(
    "/rides/end",
    response_model=RideEndResponse,
    status_code=200,
)  # type: ignore[misc]
async def end(request: Request, body: RideEndRequest) -> RideEndResponse:
    """End an active ride, calculate the fee, and release the vehicle."""

    # Fetch repositories from app state
    rides_repo = getattr(request.app.state, "rides_repository", None)
    active_users_repo = getattr(request.app.state, "active_users_repository", None)
    users_repo = getattr(request.app.state, "users_repository", None)
    vehicle_repo = getattr(request.app.state, "vehicle_repository", None)

    # Strict type-checking and initialization validation
    if rides_repo is None or not isinstance(rides_repo, RidesRepository):
        logger.error("rides_repository not initialized on app.state")
        raise HTTPException(status_code=500, detail="Rides repository not initialized")

    if active_users_repo is None or not isinstance(
        active_users_repo, ActiveUsersRepository
    ):
        logger.error("active_users_repository not initialized on app.state")
        raise HTTPException(
            status_code=500, detail="Active users repository not initialized"
        )

    if users_repo is None or not isinstance(users_repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        raise HTTPException(status_code=500, detail="Users repository not initialized")

    if vehicle_repo is None or not isinstance(vehicle_repo, VehicleRepository):
        logger.error("vehicle_repository not initialized on app.state")
        raise HTTPException(
            status_code=500, detail="Vehicle repository not initialized"
        )

    try:
        ride_id, fee = end_ride(
            user_id=body.user_id,
            vehicle_id=body.vehicle_id,
            rides_repo=rides_repo,
            active_users_repo=active_users_repo,
            users_repo=users_repo,
            vehicle_repo=vehicle_repo,
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg or "does not have an active ride" in msg:
            raise HTTPException(status_code=404, detail=msg)

        raise HTTPException(status_code=400, detail=msg)

    return RideEndResponse(ride_id=ride_id, fee=fee)
