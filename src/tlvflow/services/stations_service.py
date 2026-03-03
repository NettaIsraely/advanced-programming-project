from __future__ import annotations

from tlvflow.domain.stations import Station
from tlvflow.persistence.in_memory import StationRepository


def find_nearest_station(
    repo: StationRepository,
    *,
    lon: float,
    lat: float,
) -> Station | None:
    stations = repo.get_all()
    if not stations:
        return None

    def distance_sq(station: Station) -> float:
        # Euclidean distance in (lon, lat) space (same approach your spec mentions).
        dx = station.longitude - lon
        dy = station.latitude - lat
        return dx * dx + dy * dy

    return min(stations, key=distance_sq)


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
