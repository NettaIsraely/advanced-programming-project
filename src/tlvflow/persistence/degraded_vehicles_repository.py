"""In-memory store for user-reported degraded vehicles.

When a vehicle is added, it is removed from station inventory.
When removed (after treatment), the vehicle is reassigned to a random station.
"""

from __future__ import annotations

import random
from typing import Any

from tlvflow.domain.vehicles import Vehicle
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository


class DegradedVehiclesRepository:
    """In-memory repository for degraded (user-reported) vehicles.

    add(vehicle): stores the vehicle and removes it from whichever station has it.
    remove(vehicle_id): removes from store and docks the vehicle at a random station
    with capacity.
    """

    def __init__(
        self,
        *,
        station_repo: StationRepository,
        vehicle_repo: VehicleRepository,
    ) -> None:
        self._vehicles: dict[str, Vehicle] = {}
        self._station_repo = station_repo
        self._vehicle_repo = vehicle_repo

    def add(self, vehicle: Vehicle) -> None:
        """Add vehicle to degraded set and remove it from station inventory."""
        vid = vehicle._vehicle_id
        for station in self._station_repo.get_all():
            for v in station.vehicles:
                if v._vehicle_id == vid:
                    station.undock(vehicle)
                    break
            else:
                continue
            break
        self._vehicles[vid] = vehicle

    def remove(self, vehicle_id: str) -> Vehicle | None:
        """Remove vehicle from degraded set and reassign to a random station.

        Returns the vehicle if it was found and reassigned, None otherwise.
        Raises ValueError if no station has available capacity.
        """
        if not isinstance(vehicle_id, str) or not vehicle_id.strip():
            return None
        vehicle = self._vehicles.pop(vehicle_id.strip(), None)
        if vehicle is None:
            return None
        stations_with_slots = [s for s in self._station_repo.get_all() if not s.is_full]
        if not stations_with_slots:
            self._vehicles[vehicle_id.strip()] = vehicle
            raise ValueError("No station with available capacity for reassignment")
        station = random.choice(stations_with_slots)
        station.dock(vehicle)
        return vehicle

    def get_all(self) -> list[Vehicle]:
        """Return all degraded vehicles."""
        return list(self._vehicles.values())

    def get_by_id(self, vehicle_id: str) -> Vehicle | None:
        """Return a degraded vehicle by id, or None."""
        if not isinstance(vehicle_id, str) or not vehicle_id.strip():
            return None
        return self._vehicles.get(vehicle_id.strip())

    def clear(self) -> None:
        """Clear the degraded set. Does not reassign vehicles to stations."""
        self._vehicles.clear()

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable snapshot (vehicle ids only)."""
        return {"vehicle_ids": list(self._vehicles.keys())}

    def restore(
        self,
        snapshot: dict[str, Any],
    ) -> None:
        """Restore from snapshot: each listed vehicle is removed from station and added here."""
        self._vehicles.clear()
        vehicle_ids = snapshot.get("vehicle_ids", [])
        if not isinstance(vehicle_ids, list):
            return
        for vid in vehicle_ids:
            if not isinstance(vid, str) or not vid.strip():
                continue
            vehicle = self._vehicle_repo.get_by_id(vid.strip())
            if vehicle is not None:
                self.add(vehicle)
