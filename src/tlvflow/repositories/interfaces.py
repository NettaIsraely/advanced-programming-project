from __future__ import annotations

from typing import Protocol

from tlvflow.domain.users import User


class UsersRepositoryProtocol(Protocol):
    def get_by_id(self, user_id: str) -> User | None: ...

    def get_by_email(self, email: str) -> User | None: ...

    def add(self, user: User) -> None: ...
