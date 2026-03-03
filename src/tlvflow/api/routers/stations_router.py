import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from tlvflow.persistence.in_memory import StationRepository
from tlvflow.services.stations_service import find_nearest_station, station_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stations"])


@router.get("/stations/nearest")  # type: ignore[misc]
async def nearest_station(
    request: Request,
    lon: float = Query(..., ge=-180.0, le=180.0),
    lat: float = Query(..., ge=-90.0, le=90.0),
) -> JSONResponse:
    """
    Return the nearest station to (lon, lat) with basic metadata.

    Stations are loaded into memory at startup and stored under:
    app.state.station_repository
    """
    repo = getattr(request.app.state, "station_repository", None)
    if repo is None or not isinstance(repo, StationRepository):
        logger.error("station_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Station repository not initialized"},
        )

    station = find_nearest_station(repo, lon=lon, lat=lat)
    if station is None:
        return JSONResponse(
            status_code=404, content={"detail": "No stations available"}
        )

    return JSONResponse(content=station_to_dict(station))
