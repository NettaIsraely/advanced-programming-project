from __future__ import annotations

from tlvflow.domain.stations import Station
from tlvflow.domain.vehicles import Vehicle
from tlvflow.persistence.in_memory import StationRepository


def _distance_sq(station: Station, lon: float, lat: float) -> float:
    dx = station.longitude - lon
    dy = station.latitude - lat
    return dx * dx + dy * dy


def find_nearest_station(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
) -> Station | None:
    stations = repo.get_all()
    if not stations:
        return None
    return min(stations, key=lambda s: _distance_sq(s, lon, lat))


def find_nearest_station_with_eligible_vehicle(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
) -> tuple[Station, Vehicle] | None:
    """Nearest station (Euclidean) that has at least one eligible vehicle. Returns (station, vehicle) with vehicle already checked out."""
    stations = repo.get_all()
    with_eligible = [s for s in stations if s.has_eligible_vehicle()]
    if not with_eligible:
        return None
    nearest = min(with_eligible, key=lambda s: _distance_sq(s, lon, lat))
    vehicle = nearest.checkout_eligible_vehicle()
    return (nearest, vehicle)


def find_nearest_station_with_free_slot(
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
