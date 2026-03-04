from __future__ import annotations

from typing import Any

from tlvflow.domain.users import AmateurUser, User
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.users_repository import UsersRepository


def register_user(
    repo: UsersRepository,
    name: str,
    email: str,
    password: str,
    payment_method_id: str,
) -> str:
    if repo.get_by_email(email) is not None:
        raise ValueError("email already registered")
    user = AmateurUser.register(
        name=name,
        email=email,
        password=password,
        payment_method_id=payment_method_id,
    )
    repo.add(user)
    return user.user_id


def get_active_users(
    active_users_repo: ActiveUsersRepository,
    users_repo: UsersRepository,
) -> list[dict[str, Any]]:
    result = []
    for user_id in active_users_repo.get_active_user_ids():
        user = users_repo.get_by_id(user_id)
        if user is not None:
            result.append(_user_to_dict(user))
    return result


def _user_to_dict(user: User) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "name": user._name,
        "email": user.email,
        "payment_method_id": user.payment_method_id,
    }
