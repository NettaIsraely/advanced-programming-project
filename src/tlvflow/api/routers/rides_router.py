import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from tlvflow.persistence.rides_repository import RidesRepository

logger = logging.getLogger(__name__)

router = APIRouter(tags=["rides"])


@router.post("rides/start")  # type: ignore[misc]
async def start(request: Request) -> JSONResponse:
    rides_repo = getattr(request.app.state, "rides_repository", None)

    if rides_repo is None or not isinstance(rides_repo, RidesRepository):
        logger.error("rides_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Rides repository not initialized"},
        )
