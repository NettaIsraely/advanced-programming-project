"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from tlvflow.api.routes import router
from tlvflow.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown events."""
    logger.info("Application starting")
    yield
    logger.info("Application shutting down")


app = FastAPI(title="TLVFlow API", lifespan=lifespan)
app.include_router(router)
