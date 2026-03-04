"""Integration tests for the GET /rides/active-users endpoint."""

from fastapi.testclient import TestClient

from tlvflow.api.app import app
from tlvflow.domain.users import AmateurUser
from tlvflow.persistence.users_repository import UsersRepository


def test_active_users_returns_correct_user_during_active_ride() -> None:
    user = AmateurUser.register(
        name="Bob",
        email="bob@example.com",
        password="password123",
        payment_method_id="pm_bob",
    )
    user.start_ride("vehicle_1")
    user.set_current_ride(object())

    with TestClient(app) as client:
        repo = UsersRepository()
        repo.add(user)
        client.app.state.users_repository = repo

        resp = client.get("/rides/active-users")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) == 1
    active = data["users"][0]
    assert active["user_id"] == user.user_id
    assert active["email"] == "bob@example.com"
    assert active["name"] == "Bob"
    assert active["payment_method_id"] == "pm_bob"


def test_active_users_returns_empty_list_when_no_active_rides() -> None:
    user = AmateurUser.register(
        name="Carol",
        email="carol@example.com",
        password="password123",
        payment_method_id="pm_carol",
    )

    with TestClient(app) as client:
        repo = UsersRepository()
        repo.add(user)
        client.app.state.users_repository = repo

        resp = client.get("/rides/active-users")

    assert resp.status_code == 200
    assert resp.json()["users"] == []


def test_active_users_removes_user_after_ride_ends() -> None:
    user = AmateurUser.register(
        name="Dan",
        email="dan@example.com",
        password="password123",
        payment_method_id="pm_dan",
    )
    user.start_ride("vehicle_2")
    user.set_current_ride(object())

    with TestClient(app) as client:
        repo = UsersRepository()
        repo.add(user)
        client.app.state.users_repository = repo

        active_resp = client.get("/rides/active-users")
        assert len(active_resp.json()["users"]) == 1

        user.end_ride("station_1")

        ended_resp = client.get("/rides/active-users")

    assert ended_resp.status_code == 200
    assert ended_resp.json()["users"] == []
