"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from tlvflow.api.routes import router as api_router
from tlvflow.logging import setup_logging
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.state_store import StateStore

setup_logging()
logger = logging.getLogger(__name__)

# Path to vehicles.csv relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
VEHICLES_CSV = PROJECT_ROOT / "data" / "vehicles.csv"
STATIONS_CSV = PROJECT_ROOT / "data" / "stations.csv"
STATE_JSON = PROJECT_ROOT / "data" / "state.json"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Application starting")

    state_store = StateStore(path=STATE_JSON)
    snapshot = state_store.load()

    vehicle_repo = VehicleRepository()
    station_repo = StationRepository()

    if snapshot:
        logger.info("Loading application state from %s", STATE_JSON)
        vehicle_repo.restore(snapshot.get("vehicles", {}))
        station_repo.restore(snapshot.get("stations", {}), vehicle_repo=vehicle_repo)
    else:
        vehicle_count = vehicle_repo.load_from_csv(VEHICLES_CSV)
        logger.info("Loaded %d vehicles into memory", vehicle_count)

        station_count = station_repo.load_from_csv(STATIONS_CSV)
        logger.info("Loaded %d stations into memory", station_count)

    app.state.vehicle_repository = vehicle_repo
    app.state.station_repository = station_repo
    app.state.state_store = state_store

    try:
        yield
    finally:
        logger.info("Application shutting down; saving state to %s", STATE_JSON)
        state_store.save(
            {
                "vehicles": vehicle_repo.snapshot(),
                "stations": station_repo.snapshot(),
            }
        )


app = FastAPI(title="TLVFlow API", lifespan=lifespan)
app.include_router(api_router)
