"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from tlvflow.api.routes import router as api_router
from tlvflow.logging import setup_logging
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.state_store import StateStore
from tlvflow.persistence.users_repository import UsersRepository

setup_logging()
logger = logging.getLogger(__name__)

# Paths relative to project root
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
    users_repo = UsersRepository()
    active_users_repo = ActiveUsersRepository()
    rides_repo = RidesRepository()

    if snapshot:
        logger.info("Loading application state from %s", STATE_JSON)
        vehicle_repo.restore(snapshot.get("vehicles", {}))
        station_repo.restore(snapshot.get("stations", {}), vehicle_repo=vehicle_repo)
        users_repo.restore(snapshot.get("users", {}))
        active_users_repo.restore(snapshot.get("active_users", {}))
        rides_repo.restore(snapshot.get("rides", {}))
    else:
        vehicle_count = vehicle_repo.load_from_csv(VEHICLES_CSV)
        logger.info("Loaded %d vehicles into memory", vehicle_count)

        station_count = station_repo.load_from_csv(STATIONS_CSV)
        logger.info("Loaded %d stations into memory", station_count)

    app.state.vehicle_repository = vehicle_repo
    app.state.station_repository = station_repo
    app.state.users_repository = users_repo
    app.state.active_users_repository = active_users_repo
    app.state.state_store = state_store
    app.state.rides_repository = rides_repo

    try:
        yield
    finally:
        logger.info("Application shutting down; saving state to %s", STATE_JSON)
        state_store.save(
            {
                "vehicles": vehicle_repo.snapshot(),
                "stations": station_repo.snapshot(),
                "users": users_repo.snapshot(),
                "active_users": active_users_repo.snapshot(),
                "rides": rides_repo.snapshot(),
            }
        )


app = FastAPI(title="TLVFlow API", lifespan=lifespan)
app.include_router(api_router)
