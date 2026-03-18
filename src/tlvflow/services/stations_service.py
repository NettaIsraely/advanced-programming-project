from __future__ import annotations

import asyncio
from collections import defaultdict

from tlvflow.domain.stations import Station
from tlvflow.domain.vehicles import Vehicle
from tlvflow.persistence.in_memory import StationRepository


def _distance_sq(station: Station, lon: float, lat: float) -> float:
    dx = station.longitude - lon
    dy = station.latitude - lat
    return dx * dx + dy * dy


async def find_nearest_station(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
) -> Station | None:
    """Return nearest station to (lon, lat). Async for API spec; logic is read-only."""
    stations = repo.get_all()
    if not stations:
        return None
    return min(stations, key=lambda s: _distance_sq(s, lon, lat))


async def find_nearest_station_with_eligible_vehicle(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
    station_locks: defaultdict[int, asyncio.Lock] | None = None,
) -> tuple[Station, Vehicle] | None:
    """Nearest station with eligible vehicle; returns (station, vehicle) with vehicle checked out. Uses station_locks when provided to avoid double-booking."""
    stations = repo.get_all()
    with_eligible = [s for s in stations if s.has_eligible_vehicle()]
    if not with_eligible:
        return None
    nearest = min(with_eligible, key=lambda s: _distance_sq(s, lon, lat))
    sid = nearest.station_id
    if station_locks is not None:
        async with station_locks[sid]:
            station = repo.get_by_id(sid)
            if station is None or not station.has_eligible_vehicle():
                return None
            vehicle = station.checkout_eligible_vehicle()
            return (station, vehicle)
    vehicle = nearest.checkout_eligible_vehicle()
    return (nearest, vehicle)


async def find_nearest_station_with_free_slot(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
) -> Station | None:
    """Nearest station (Euclidean) that has at least one free slot (not full)."""
    stations = repo.get_all()
    with_slot = [s for s in stations if not s.is_full]
    if not with_slot:
        return None
    return min(with_slot, key=lambda s: _distance_sq(s, lon, lat))


def station_to_dict(station: Station) -> dict[str, object]:
    return {
        "station_id": station.station_id,
        "name": station.name,
        "lat": station.latitude,
        "lon": station.longitude,
        "max_capacity": station.capacity,
        "available_slots": station.available_slots,
        "is_full": station.is_full,
        "is_empty": station.is_empty,
    }
