import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.users_repository import UsersRepository
from tlvflow.services.users_service import get_active_users, register_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


class RegisterRequest(BaseModel):  # type: ignore[misc]
    name: str
    email: str
    password: str
    payment_method_id: str


@router.post("/register")  # type: ignore[misc]
async def register(request: Request, body: RegisterRequest) -> JSONResponse:
    """Register a new user and return their generated user_id."""
    repo = getattr(request.app.state, "users_repository", None)
    if repo is None or not isinstance(repo, UsersRepository):
        logger.error("users_repository not initialized on app.state")
        return JSONResponse(
            status_code=500,
            content={"detail": "Users repository not initialized"},
        )

    try:
        user_id = register_user(
            repo,
            name=body.name,
            email=body.email,
            password=body.password,
            payment_method_id=body.payment_method_id,
        )
    except ValueError as exc:
        msg = str(exc)
        if msg == "email already registered":
            return JSONResponse(status_code=409, content={"detail": msg})
        return JSONResponse(status_code=422, content={"detail": msg})

    return JSONResponse(status_code=201, content={"user_id": user_id})


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
