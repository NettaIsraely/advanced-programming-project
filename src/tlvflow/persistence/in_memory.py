"""In-memory storage repositories with CSV loading."""

from pathlib import Path

from tlvflow.domain.stations import Station
from tlvflow.domain.vehicles import Vehicle
from tlvflow.persistence.loaders import load_stations_from_csv, load_vehicles_from_csv


class VehicleRepository:
    """In-memory repository for vehicles, optionally loaded from CSV."""

    def __init__(self) -> None:
        self._vehicles: dict[str, Vehicle] = {}

    def load_from_csv(self, path: str | Path) -> int:
        """
        Load vehicles from a CSV file into memory.

        Args:
            path: Path to the CSV file.

        Returns:
            Number of vehicles loaded.
        """
        vehicles = load_vehicles_from_csv(path)
        for v in vehicles:
            self._vehicles[v._vehicle_id] = v
        return len(vehicles)

    def get_all(self) -> list[Vehicle]:
        """Return all vehicles in memory."""
        return list(self._vehicles.values())

    def get_by_id(self, vehicle_id: str) -> Vehicle | None:
        """Return a vehicle by ID, or None if not found."""
        return self._vehicles.get(vehicle_id)

    def add(self, vehicle: Vehicle) -> None:
        """Add or replace a vehicle."""
        self._vehicles[vehicle._vehicle_id] = vehicle

    def clear(self) -> None:
        """Remove all vehicles from memory."""
        self._vehicles.clear()


class StationRepository:
    """In-memory repository for stations, optionally loaded from CSV."""

    def __init__(self) -> None:
        self._stations: dict[int, Station] = {}

    def load_from_csv(self, path: str | Path) -> int:
        """
        Load stations from a CSV file into memory.

        Args:
            path: Path to the CSV file.

        Returns:
            Number of stations loaded.
        """
        stations = load_stations_from_csv(path)
        for s in stations:
            self._stations[s.station_id] = s
        return len(stations)

    def get_all(self) -> list[Station]:
        """Return all stations in memory."""
        return list(self._stations.values())

    def get_by_id(self, station_id: int) -> Station | None:
        """Return a station by ID, or None if not found."""
        return self._stations.get(station_id)

    def add(self, station: Station) -> None:
        """Add or replace a station."""
        self._stations[station.station_id] = station

    def clear(self) -> None:
        """Remove all stations from memory."""
        self._stations.clear()
