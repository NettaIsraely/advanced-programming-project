from __future__ import annotations

import random
from datetime import datetime

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.maintenance_event import MaintenanceEvent
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.repositories.interfaces import MaintenanceRepositoryProtocol


def treat_vehicles(
    vehicles_repo: VehicleRepository,
    stations_repo: StationRepository,
    maintenance_repo: MaintenanceRepositoryProtocol,
) -> list[str]:
    treated_ids: list[str] = []

    for vehicle in vehicles_repo.get_all():
        is_degraded = vehicle.check_status() == VehicleStatus.DEGRADED
        is_high_ride = vehicle.is_treatment_eligible()

        if not is_degraded and not is_high_ride:
            continue

        vehicle.complete_maintenance()
        vehicle.set_status(VehicleStatus.AVAILABLE)

        event = MaintenanceEvent(
            vehicle_id=vehicle._vehicle_id,
            report_id="",
            open_time=datetime.now(),
        )
        event.close_event()
        maintenance_repo.add(event)

        if is_degraded:
            all_stations = stations_repo.get_all()

            current_station = None
            for station in all_stations:
                if vehicle in station.vehicles:
                    current_station = station
                    break

            candidates = [
                s for s in all_stations if not s.is_full and s is not current_station
            ]

            if candidates:
                new_station = random.choice(candidates)
                if current_station is not None:
                    current_station.undock(vehicle)
                new_station.dock(vehicle)

        treated_ids.append(vehicle._vehicle_id)

    return treated_ids
