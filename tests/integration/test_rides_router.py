"""Integration tests for ride endpoints: register -> start ride -> end ride."""

from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from tlvflow.api.app import app
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.degraded_vehicles_repository import (
    DegradedVehiclesRepository,
)
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.users_repository import UsersRepository
from tlvflow.services.link_vehicles import link_vehicles_to_stations

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATIONS_CSV = PROJECT_ROOT / "data" / "stations.csv"
VEHICLES_CSV = PROJECT_ROOT / "data" / "vehicles.csv"


def _register_payload(email: str = "alice@example.com") -> dict:
    return {
        "name": "Alice",
        "email": email,
        "password": "securepass1",
        "payment_method_id": "pm_alice",
    }


def _make_client() -> TestClient:
    """Create a TestClient with app state populated (stations, vehicles, users, rides)."""
    vehicle_repo = VehicleRepository()
    station_repo = StationRepository()
    vehicle_repo.load_from_csv(VEHICLES_CSV)
    station_repo.load_from_csv(STATIONS_CSV)
    degraded_repo = DegradedVehiclesRepository()
    link_vehicles_to_stations(vehicle_repo, station_repo, degraded_repo)

    client = TestClient(app)
    client.app.state.users_repository = UsersRepository()
    client.app.state.rides_repository = RidesRepository()
    client.app.state.active_users_repository = ActiveUsersRepository()
    client.app.state.station_repository = station_repo
    client.app.state.vehicle_repository = vehicle_repo
    return client


def test_e2e_register_start_ride_end_ride() -> None:
    """End-to-end: register -> start ride -> end ride returns 201, 201, 200 with ride_id and fee."""
    with _make_client() as client:
        reg = client.post(
            "/register", json=_register_payload(f"e2e-{uuid4().hex}@example.com")
        )
        assert reg.status_code == 201
        user_id = reg.json()["user_id"]

        start = client.post(
            "/rides/start",
            json={"user_id": user_id, "station_id": 1},
        )
        assert start.status_code == 201
        start_data = start.json()
        assert "ride_id" in start_data
        assert "vehicle_id" in start_data
        ride_id = start_data["ride_id"]
        vehicle_id = start_data["vehicle_id"]

        end = client.post(
            "/rides/end",
            json={
                "user_id": user_id,
                "vehicle_id": vehicle_id,
                "station_id": 1,
            },
        )
        assert end.status_code == 200
        end_data = end.json()
        assert end_data["ride_id"] == ride_id
        assert "fee" in end_data
        assert isinstance(end_data["fee"], int | float)


def test_start_ride_user_already_on_ride_returns_409() -> None:
    """Starting a second ride without ending the first returns 409."""
    with _make_client() as client:
        reg = client.post(
            "/register", json=_register_payload(f"already-{uuid4().hex}@example.com")
        )
        assert reg.status_code == 201
        user_id = reg.json()["user_id"]

        client.post("/rides/start", json={"user_id": user_id, "station_id": 1})
        second = client.post(
            "/rides/start",
            json={"user_id": user_id, "station_id": 2},
        )

    assert second.status_code == 409


def test_start_ride_nonexistent_user_returns_404() -> None:
    """Starting a ride with a user_id that does not exist returns 404."""
    with _make_client() as client:
        resp = client.post(
            "/rides/start",
            json={"user_id": "nonexistent-user-id", "station_id": 1},
        )
    assert resp.status_code == 404


def test_end_ride_nonexistent_user_returns_404() -> None:
    """Ending a ride with a user_id that does not exist returns 404."""
    with _make_client() as client:
        resp = client.post(
            "/rides/end",
            json={
                "user_id": "nonexistent-user-id",
                "vehicle_id": "V000001",
                "station_id": 1,
            },
        )
    assert resp.status_code == 404


def test_end_ride_user_has_no_active_ride_returns_404() -> None:
    """Ending a ride when the user has no active ride (invalid ride_id context) returns 404."""
    with _make_client() as client:
        reg = client.post(
            "/register", json=_register_payload(f"noactive-{uuid4().hex}@example.com")
        )
        assert reg.status_code == 201
        user_id = reg.json()["user_id"]

        resp = client.post(
            "/rides/end",
            json={
                "user_id": user_id,
                "vehicle_id": "V000001",
                "station_id": 1,
            },
        )
    assert resp.status_code == 404
