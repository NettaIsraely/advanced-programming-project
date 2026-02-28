"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from tlvflow.api.routes import router
from tlvflow.logging import setup_logging
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository

setup_logging()
logger = logging.getLogger(__name__)

# Path to vehicles.csv relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VEHICLES_CSV = PROJECT_ROOT / "data" / "vehicles.csv"
STATIONS_CSV = PROJECT_ROOT / "data" / "stations.csv"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Application starting")

    vehicle_repo = VehicleRepository()
    count = vehicle_repo.load_from_csv(VEHICLES_CSV)
    app.state.vehicle_repository = vehicle_repo
    logger.info("Loaded %d vehicles into memory", count)

    station_repo = StationRepository()
    station_count = station_repo.load_from_csv(STATIONS_CSV)
    app.state.station_repository = station_repo
    logger.info("Loaded %d stations into memory", station_count)
    yield
    logger.info("Application shutting down")


app = FastAPI(title="TLVFlow API", lifespan=lifespan)
app.include_router(router)
