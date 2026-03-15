import logging

from fastapi import APIRouter

from tlvflow.api.schemas import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)  # type: ignore[misc]
async def health() -> HealthResponse:
    """Health check endpoint."""
    logger.debug("Health check requested")
    return HealthResponse(status="ok")
