"""Unit tests for DegradedVehiclesRepository."""

from __future__ import annotations

import pytest

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.stations import Station
from tlvflow.domain.vehicles import Bike
from tlvflow.persistence.degraded_vehicles_repository import (
    DegradedVehiclesRepository,
)
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository


def make_repos():
    """Vehicle repo with one bike; station repo with one station holding that bike."""
    vehicle_repo = VehicleRepository()
    bike = Bike(
        vehicle_id="v1",
        frame_number="F1",
        status=VehicleStatus.DEGRADED,
    )
    vehicle_repo.add(bike)

    station_repo = StationRepository()
    station = Station(
        station_id=1,
        name="Central",
        latitude=32.0,
        longitude=34.8,
        capacity=5,
    )
    station.dock(bike)
    station_repo.add(station)

    degraded_repo = DegradedVehiclesRepository(
        station_repo=station_repo,
        vehicle_repo=vehicle_repo,
    )
    return vehicle_repo, station_repo, degraded_repo, bike, station


def test_add_removes_vehicle_from_station() -> None:
    vehicle_repo, station_repo, degraded_repo, bike, station = make_repos()
    assert station.vehicles == (bike,)

    degraded_repo.add(bike)

    assert station.vehicles == ()
    assert degraded_repo.get_all() == [bike]
    assert degraded_repo.get_by_id("v1") is bike


def test_remove_reassigns_to_random_station() -> None:
    vehicle_repo, station_repo, degraded_repo, bike, station = make_repos()
    degraded_repo.add(bike)
    assert station.vehicles == ()

    out = degraded_repo.remove("v1")

    assert out is bike
    assert degraded_repo.get_by_id("v1") is None
    assert degraded_repo.get_all() == []
    assert len(station.vehicles) == 1 and station.vehicles[0] is bike


def test_remove_invalid_id_returns_none() -> None:
    _, _, degraded_repo, bike, _ = make_repos()
    degraded_repo.add(bike)

    assert degraded_repo.remove("") is None
    assert degraded_repo.remove("  ") is None
    assert degraded_repo.remove("v99") is None
    assert degraded_repo.get_all() == [bike]


def test_remove_when_no_station_capacity_raises() -> None:
    vehicle_repo = VehicleRepository()
    bike1 = Bike("v1", "F1", status=VehicleStatus.DEGRADED)
    bike2 = Bike("v2", "F2", status=VehicleStatus.AVAILABLE)
    bike3 = Bike("v3", "F3", status=VehicleStatus.DEGRADED)
    vehicle_repo.add(bike1)
    vehicle_repo.add(bike2)
    vehicle_repo.add(bike3)

    station_repo = StationRepository()
    s1 = Station(1, "A", 32.0, 34.8, capacity=1)
    s2 = Station(2, "B", 32.1, 34.9, capacity=1)
    s1.dock(bike1)
    s2.dock(bike2)
    station_repo.add(s1)
    station_repo.add(s2)

    degraded_repo = DegradedVehiclesRepository(
        station_repo=station_repo,
        vehicle_repo=vehicle_repo,
    )
    degraded_repo._vehicles["v3"] = bike3
    assert s1.vehicles == (bike1,)
    assert s2.vehicles == (bike2,)

    with pytest.raises(ValueError, match="No station with available capacity"):
        degraded_repo.remove("v3")

    assert degraded_repo.get_by_id("v3") is bike3


def test_clear() -> None:
    _, _, degraded_repo, bike, station = make_repos()
    degraded_repo.add(bike)
    degraded_repo.clear()
    assert degraded_repo.get_all() == []
    assert degraded_repo.get_by_id("v1") is None
    assert station.vehicles == ()


def test_snapshot_and_restore_round_trip() -> None:
    vehicle_repo, station_repo, degraded_repo, bike, station = make_repos()
    degraded_repo.add(bike)
    snapshot = degraded_repo.snapshot()
    assert snapshot == {"vehicle_ids": ["v1"]}

    degraded_repo.clear()
    assert degraded_repo.get_all() == []
    station.dock(bike)

    degraded_repo.restore(snapshot)
    assert len(degraded_repo.get_all()) == 1
    assert degraded_repo.get_by_id("v1") is bike
    assert station.vehicles == ()
