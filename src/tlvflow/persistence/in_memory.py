"""In-memory vehicle storage with CSV loading."""

from pathlib import Path

from tlvflow.domain.vehicles import Vehicle
from tlvflow.persistence.loaders import load_vehicles_from_csv


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
