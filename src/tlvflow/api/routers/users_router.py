import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from tlvflow.api.schemas import (
    RegisterRequest,
    RegisterResponse,
    UpgradeRequest,
    UpgradeResponse,
)
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.users_repository import UsersRepository
from tlvflow.services.users_service import (
    get_active_users,
    register_user,
    upgrade_user_to_pro,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
)  # type: ignore[misc]
async def register(request: Request, body: RegisterRequest) -> RegisterResponse:
    """Register a new AmateurUser and return their generated user_id."""

    repo = getattr(request.app.state, "users_repository", None)
    if repo is None or not isinstance(repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        raise RuntimeError("Users repository not initialized")

    try:
        user_id = await register_user(
            repo,
            name=body.name,
            email=body.email,
            password=body.password,
            payment_method_id=body.payment_method_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "email already registered":
            raise HTTPException(status_code=409, detail=msg)

        if msg == "email must be a valid email address":
            raise HTTPException(status_code=422, detail=msg)

        raise HTTPException(status_code=400, detail=msg)

    return RegisterResponse(user_id=user_id)


@router.post(
    "/user/upgrade",
    response_model=UpgradeResponse,
    status_code=200,
)  # type: ignore[misc]
async def upgrade(request: Request, body: UpgradeRequest) -> UpgradeResponse:
    """Upgrade a regular user to Pro. Provide license_number and license_expiry; optionally license_image_url (picture of driver's license)."""
    repo = getattr(request.app.state, "users_repository", None)
    if repo is None or not isinstance(repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        raise RuntimeError("Users repository not initialized")

    try:
        license_expiry = datetime.fromisoformat(
            body.license_expiry.replace("Z", "+00:00")
        )
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="license_expiry must be an ISO 8601 date or datetime string",
        )

    try:
        user_id = upgrade_user_to_pro(
            repo,
            user_id=body.user_id,
            license_number=body.license_number,
            license_expiry=license_expiry,
            license_image_url=body.license_image_url,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "User not found":
            raise HTTPException(status_code=404, detail=msg)
        if msg == "User is already a Pro user":
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

    return UpgradeResponse(user_id=user_id)


@router.get("/rides/active-users")  # type: ignore[misc]
async def active_users(request: Request) -> JSONResponse:
    """Return all users who currently have an active ride."""
    active_users_repo = getattr(request.app.state, "active_users_repository", None)
    if active_users_repo is None or not isinstance(
        active_users_repo, ActiveUsersRepository
    ):
        logger.error("active_users_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Active users repository not initialized"},
        )

    users_repo = getattr(request.app.state, "users_repository", None)
    if users_repo is None or not isinstance(users_repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Users repository not initialized"},
        )

    users = get_active_users(active_users_repo, users_repo)
    return JSONResponse(content={"users": users})
