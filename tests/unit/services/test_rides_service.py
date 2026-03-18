"""Unit tests for rides_service start_ride and end_ride logic."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.stations import Station
from tlvflow.domain.users import User
from tlvflow.domain.vehicles import Bike
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.users_repository import UsersRepository
from tlvflow.services.rides_service import end_ride, start_ride


def _make_user(user_id: str = "user-1") -> User:
    return User.register(
        name="Test User",
        email=f"{user_id}@test.com",
        password="password123",
        payment_method_id="pm_1",
    )


def _make_station(
    station_id: int,
    *,
    vehicles: list[Bike] | None = None,
    capacity: int = 5,
) -> Station:
    return Station(
        station_id=station_id,
        name=f"Station_{station_id}",
        latitude=32.0 + station_id * 0.01,
        longitude=34.0 + station_id * 0.01,
        capacity=capacity,
        vehicles=list(vehicles) if vehicles else [],
    )


def _make_bike(
    vehicle_id: str,
    *,
    rides_since_last_treated: int = 0,
    status: VehicleStatus = VehicleStatus.AVAILABLE,
) -> Bike:
    bike = Bike(
        vehicle_id=vehicle_id,
        frame_number=f"F-{vehicle_id}",
        status=status,
    )
    bike.rides_since_last_treated = rides_since_last_treated
    return bike


# --- Start ride: nearest station selection ---


async def test_start_ride_uses_requested_station() -> None:
    """Start ride uses the given station_id (nearest/caller-selected station)."""
    users_repo = UsersRepository()
    user = _make_user("u1")
    users_repo.add(user)

    bike = _make_bike("v1")
    station1 = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station1)

    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    ride_id, vehicle_id = await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    assert vehicle_id == "v1"
    assert ride_id
    assert active_repo.get_ride_id(user.user_id) == ride_id
    ride = rides_repo.get_by_id(ride_id)
    assert ride is not None
    assert ride.start_latitude == station1.latitude
    assert ride.start_longitude == station1.longitude


async def test_start_ride_from_second_station_returns_vehicle_from_that_station() -> None:
    """When multiple stations exist, start_ride uses the requested station."""
    users_repo = UsersRepository()
    user = _make_user("u2")
    users_repo.add(user)

    bike1 = _make_bike("v1")
    bike2 = _make_bike("v2")
    station1 = _make_station(1, vehicles=[bike1])
    station2 = _make_station(2, vehicles=[bike2])
    bike1._station_id = 1
    bike2._station_id = 2
    station_repo = StationRepository()
    station_repo.add(station1)
    station_repo.add(station2)

    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike1)
    vehicle_repo.add(bike2)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    _, vehicle_id = await start_ride(
        user_id=user.user_id,
        station_id=2,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    assert vehicle_id == "v2"
    assert station2.is_empty
    assert len(station1.vehicles) == 1


# --- Start ride: vehicle eligibility ---


async def test_start_ride_with_eligible_vehicle_succeeds() -> None:
    """When station has an eligible vehicle (e.g. rides_since_last_treated <= 10), start succeeds."""
    users_repo = UsersRepository()
    user = _make_user("u3")
    users_repo.add(user)

    bike = _make_bike("v_ok", rides_since_last_treated=5)
    assert not bike.is_unrentable()
    station = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    ride_id, vehicle_id = await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    assert vehicle_id == "v_ok"
    assert ride_id


# --- Start ride: vehicle selection rule ---


async def test_start_ride_vehicle_selection_returns_vehicle_from_station() -> None:
    """Vehicle selection: the returned vehicle is one that was docked at the station (LIFO pop)."""
    users_repo = UsersRepository()
    user = _make_user("u4")
    users_repo.add(user)

    first = _make_bike("v_first")
    second = _make_bike("v_second")
    station = _make_station(1, vehicles=[first, second])
    first._station_id = 1
    second._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(first)
    vehicle_repo.add(second)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    _, vehicle_id = await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    assert vehicle_id in ("v_first", "v_second")
    assert len(station.vehicles) == 1


# --- End ride: payment and fee ---


async def test_end_ride_returns_calculated_fee() -> None:
    """End ride calculates fee (payment) from duration and distance and returns it."""
    users_repo = UsersRepository()
    user = _make_user("u5")
    users_repo.add(user)

    bike = _make_bike("v_pay")
    station = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    start = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    end = datetime(2026, 1, 1, 12, 10, tzinfo=UTC)

    with patch("tlvflow.services.rides_service.datetime") as mock_dt:
        mock_dt.now.return_value = start
        await start_ride(
            user_id=user.user_id,
            station_id=1,
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )

        ride_id = active_repo.get_ride_id(user.user_id)
        assert ride_id is not None
        ride = rides_repo.get_by_id(ride_id)
        assert ride is not None

        mock_dt.now.return_value = end
        returned_ride_id, fee = await end_ride(
            user_id=user.user_id,
            vehicle_id="v_pay",
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            users_repo=users_repo,
            vehicle_repo=vehicle_repo,
        )

    assert returned_ride_id == ride_id
    duration_minutes = 10.0
    placeholder_distance = 5.0
    expected_fee = duration_minutes * 0.5 + placeholder_distance * 0.2
    assert fee == expected_fee
    assert ride.fee == expected_fee


# --- End ride: rides_since_last_treated increment ---


async def test_end_ride_increments_rides_since_last_treated() -> None:
    """After end_ride, the vehicle's rides_since_last_treated is incremented by 1."""
    users_repo = UsersRepository()
    user = _make_user("u6")
    users_repo.add(user)

    bike = _make_bike("v_inc", rides_since_last_treated=3)
    station = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    assert bike.rides_since_last_treated == 3

    await end_ride(
        user_id=user.user_id,
        vehicle_id="v_inc",
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        users_repo=users_repo,
        vehicle_repo=vehicle_repo,
    )

    assert bike.rides_since_last_treated == 4
    assert vehicle_repo.get_by_id("v_inc").rides_since_last_treated == 4


# --- End ride: vehicle status and active user cleared ---


async def test_end_ride_sets_vehicle_available_and_clears_active_user() -> None:
    """End ride sets vehicle status to AVAILABLE and removes user from active users."""
    users_repo = UsersRepository()
    user = _make_user("u7")
    users_repo.add(user)

    bike = _make_bike("v_avail")
    station = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    await end_ride(
        user_id=user.user_id,
        vehicle_id="v_avail",
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        users_repo=users_repo,
        vehicle_repo=vehicle_repo,
    )

    assert vehicle_repo.get_by_id("v_avail").check_status() == VehicleStatus.AVAILABLE
    assert active_repo.get_ride_id(user.user_id) is None


# --- Edge case: no eligible vehicles (station empty) ---


async def test_start_ride_station_empty_raises() -> None:
    """When station has no available vehicles, start_ride raises ValueError."""
    users_repo = UsersRepository()
    user = _make_user("u8")
    users_repo.add(user)

    station = _make_station(1, vehicles=[])
    station_repo = StationRepository()
    station_repo.add(station)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    with pytest.raises(ValueError, match="has no available vehicles"):
        await start_ride(
            user_id=user.user_id,
            station_id=1,
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )


# --- Edge case: all stations full (no vehicles at requested station) ---


async def test_start_ride_station_not_found_raises() -> None:
    """When station_id does not exist, start_ride raises ValueError."""
    users_repo = UsersRepository()
    user = _make_user("u9")
    users_repo.add(user)

    station_repo = StationRepository()
    station_repo.add(_make_station(1, vehicles=[_make_bike("v1")]))

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    with pytest.raises(ValueError, match="Station 99 not found"):
        await start_ride(
            user_id=user.user_id,
            station_id=99,
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )


# --- Edge case: user already on ride ---


async def test_start_ride_user_already_on_ride_raises() -> None:
    """When user already has an active ride, start_ride raises ValueError."""
    users_repo = UsersRepository()
    user = _make_user("u10")
    users_repo.add(user)

    bike1 = _make_bike("v_a")
    bike2 = _make_bike("v_b")
    station1 = _make_station(1, vehicles=[bike1])
    station2 = _make_station(2, vehicles=[bike2])
    bike1._station_id = 1
    bike2._station_id = 2
    station_repo = StationRepository()
    station_repo.add(station1)
    station_repo.add(station2)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike1)
    vehicle_repo.add(bike2)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    with pytest.raises(ValueError, match="already has an active ride"):
        await start_ride(
            user_id=user.user_id,
            station_id=2,
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )


# --- End ride edge: nonexistent user, no active ride, wrong vehicle ---


async def test_end_ride_nonexistent_user_raises() -> None:
    """End ride with unknown user_id raises ValueError."""
    users_repo = UsersRepository()
    vehicle_repo = VehicleRepository()
    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    with pytest.raises(ValueError, match="not found"):
        await end_ride(
            user_id="nonexistent",
            vehicle_id="v1",
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            users_repo=users_repo,
            vehicle_repo=vehicle_repo,
        )


async def test_end_ride_user_has_no_active_ride_raises() -> None:
    """End ride when user has no active ride raises ValueError."""
    users_repo = UsersRepository()
    user = _make_user("u11")
    users_repo.add(user)
    vehicle_repo = VehicleRepository()
    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    with pytest.raises(ValueError, match="does not have an active ride"):
        await end_ride(
            user_id=user.user_id,
            vehicle_id="v_any",
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            users_repo=users_repo,
            vehicle_repo=vehicle_repo,
        )


async def test_end_ride_wrong_vehicle_id_raises() -> None:
    """End ride with vehicle_id that does not match the active ride raises ValueError."""
    users_repo = UsersRepository()
    user = _make_user("u12")
    users_repo.add(user)

    bike = _make_bike("v_correct")
    station = _make_station(1, vehicles=[bike])
    bike._station_id = 1
    station_repo = StationRepository()
    station_repo.add(station)
    vehicle_repo = VehicleRepository()
    vehicle_repo.add(bike)

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()

    await start_ride(
        user_id=user.user_id,
        station_id=1,
        rides_repo=rides_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
        users_repo=users_repo,
    )

    with pytest.raises(ValueError, match="does not match the active ride"):
        await end_ride(
            user_id=user.user_id,
            vehicle_id="v_wrong",
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            users_repo=users_repo,
            vehicle_repo=vehicle_repo,
        )


# --- Start ride: nonexistent user ---


async def test_start_ride_nonexistent_user_raises() -> None:
    """Start ride with unknown user_id raises ValueError."""
    station_repo = StationRepository()
    station_repo.add(_make_station(1, vehicles=[_make_bike("v1")]))

    rides_repo = RidesRepository()
    active_repo = ActiveUsersRepository()
    users_repo = UsersRepository()

    with pytest.raises(ValueError, match="User .* not found"):
        await start_ride(
            user_id="no-such-user",
            station_id=1,
            rides_repo=rides_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
            users_repo=users_repo,
        )
