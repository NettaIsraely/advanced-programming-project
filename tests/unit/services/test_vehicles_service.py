"""Unit tests for vehicles_service: report_degraded_vehicle."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.rides import Ride
from tlvflow.domain.stations import Station
from tlvflow.domain.vehicles import Bike
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.degraded_vehicles_repository import DegradedVehiclesRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.services.vehicles_service import report_degraded_vehicle


def _make_bike(vid: str) -> Bike:
    return Bike(vehicle_id=vid, frame_number=f"F-{vid}", status=VehicleStatus.AVAILABLE)


def _make_station(sid: int, bikes: list[Bike] | None = None) -> Station:
    return Station(
        station_id=sid,
        name=f"Station_{sid}",
        latitude=32.0,
        longitude=34.0,
        capacity=10,
        vehicles=bikes or [],
    )


# --- report during active ride ---


async def test_report_degraded_during_active_ride() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()
    station_repo = StationRepository()

    bike = _make_bike("v1")
    vehicles_repo.add(bike)

    ride = Ride(user_id="u1", vehicle_id="v1", start_time=datetime.now(UTC))
    rides_repo.add(ride)
    active_repo.set_active("u1", ride.ride_id)

    await report_degraded_vehicle(
        user_id="u1",
        vehicle_id="v1",
        rides_repo=rides_repo,
        vehicles_repo=vehicles_repo,
        degraded_repo=degraded_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
    )

    assert ride.end_time is not None
    assert ride.fee == 0.0
    assert active_repo.get_ride_id("u1") is None
    assert len(degraded_repo.get_all()) == 1
    assert vehicles_repo.get_by_id("v1") is None


async def test_report_degraded_vehicle_not_found_during_active_ride() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()

    ride = Ride(user_id="u1", vehicle_id="v_missing", start_time=datetime.now(UTC))
    rides_repo.add(ride)
    active_repo.set_active("u1", ride.ride_id)

    with pytest.raises(LookupError, match="vehicle not found"):
        await report_degraded_vehicle(
            user_id="u1",
            vehicle_id="v_missing",
            rides_repo=rides_repo,
            vehicles_repo=vehicles_repo,
            degraded_repo=degraded_repo,
            active_users_repo=active_repo,
        )


# --- report from last completed ride ---


async def test_report_degraded_from_last_completed_ride() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()
    station_repo = StationRepository()

    bike = _make_bike("v2")
    vehicles_repo.add(bike)
    station = _make_station(1, [bike])
    station_repo.add(station)

    ride = Ride(user_id="u1", vehicle_id="v2", start_time=datetime.now(UTC))
    ride.end()
    rides_repo.add(ride)

    await report_degraded_vehicle(
        user_id="u1",
        vehicle_id="v2",
        rides_repo=rides_repo,
        vehicles_repo=vehicles_repo,
        degraded_repo=degraded_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
    )

    assert bike.check_status() == VehicleStatus.DEGRADED
    assert len(degraded_repo.get_all()) == 1
    assert vehicles_repo.get_by_id("v2") is None
    assert bike not in station.vehicles


async def test_report_degraded_no_completed_rides_raises() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()

    with pytest.raises(ValueError, match="no active ride"):
        await report_degraded_vehicle(
            user_id="u1",
            vehicle_id="v1",
            rides_repo=rides_repo,
            vehicles_repo=vehicles_repo,
            degraded_repo=degraded_repo,
            active_users_repo=active_repo,
        )


async def test_report_degraded_wrong_vehicle_from_last_ride_raises() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()

    ride = Ride(user_id="u1", vehicle_id="v_other", start_time=datetime.now(UTC))
    ride.end()
    rides_repo.add(ride)

    with pytest.raises(ValueError, match="no active ride"):
        await report_degraded_vehicle(
            user_id="u1",
            vehicle_id="v_wrong",
            rides_repo=rides_repo,
            vehicles_repo=vehicles_repo,
            degraded_repo=degraded_repo,
            active_users_repo=active_repo,
        )


async def test_report_degraded_no_station_repo_raises() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()

    ride = Ride(user_id="u1", vehicle_id="v1", start_time=datetime.now(UTC))
    ride.end()
    rides_repo.add(ride)

    bike = _make_bike("v1")
    vehicles_repo.add(bike)

    with pytest.raises(ValueError, match="station repository required"):
        await report_degraded_vehicle(
            user_id="u1",
            vehicle_id="v1",
            rides_repo=rides_repo,
            vehicles_repo=vehicles_repo,
            degraded_repo=degraded_repo,
            active_users_repo=active_repo,
            station_repo=None,
        )


async def test_report_degraded_vehicle_not_found_completed_ride() -> None:
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()
    station_repo = StationRepository()

    ride = Ride(user_id="u1", vehicle_id="v_gone", start_time=datetime.now(UTC))
    ride.end()
    rides_repo.add(ride)

    with pytest.raises(LookupError, match="vehicle not found"):
        await report_degraded_vehicle(
            user_id="u1",
            vehicle_id="v_gone",
            rides_repo=rides_repo,
            vehicles_repo=vehicles_repo,
            degraded_repo=degraded_repo,
            active_users_repo=active_repo,
            station_repo=station_repo,
        )


async def test_report_degraded_vehicle_not_at_any_station() -> None:
    """Vehicle exists but not docked at any station -- still gets marked degraded."""
    rides_repo = RidesRepository()
    vehicles_repo = VehicleRepository()
    degraded_repo = DegradedVehiclesRepository()
    active_repo = ActiveUsersRepository()
    station_repo = StationRepository()
    station_repo.add(_make_station(1))

    bike = _make_bike("v_free")
    vehicles_repo.add(bike)

    ride = Ride(user_id="u1", vehicle_id="v_free", start_time=datetime.now(UTC))
    ride.end()
    rides_repo.add(ride)

    await report_degraded_vehicle(
        user_id="u1",
        vehicle_id="v_free",
        rides_repo=rides_repo,
        vehicles_repo=vehicles_repo,
        degraded_repo=degraded_repo,
        active_users_repo=active_repo,
        station_repo=station_repo,
    )

    assert bike.check_status() == VehicleStatus.DEGRADED
    assert len(degraded_repo.get_all()) == 1
