from __future__ import annotations

from typing import Any

from tlvflow.domain.users import AmateurUser, User
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


def get_active_users(repo: UsersRepository) -> list[dict[str, Any]]:
    return [
        _user_to_dict(user) for user in repo.get_all() if user.current_ride is not None
    ]


def _user_to_dict(user: User) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "name": user._name,
        "email": user.email,
        "payment_method_id": user.payment_method_id,
    }
