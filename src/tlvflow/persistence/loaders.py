"""Load vehicle data from CSV files."""

import csv
import logging
from pathlib import Path

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.vehicles import Bike, EBike, Scooter, Vehicle

logger = logging.getLogger(__name__)

# Expected CSV columns: vehicle_id, station_id, vehicle_type, status,
# rides_since_last_treated, last_treated_date
VEHICLE_ID = "vehicle_id"
STATION_ID = "station_id"
FRAME_NUMBER = "frame_number"  # fallback if not in CSV
VEHICLE_TYPE = "vehicle_type"
STATUS = "status"
RIDES_SINCE_LAST_TREATED = "rides_since_last_treated"
HAS_CHILD_SEAT = "has_child_seat"
BATTERY_LEVEL = "battery_level"

# Map CSV vehicle_type to internal type
TYPE_MAP = {"bicycle": "bike", "electric_bicycle": "ebike", "scooter": "scooter"}
VALID_TYPES = {"bike", "ebike", "scooter"}
VALID_STATUSES = {s.value for s in VehicleStatus}


def _parse_status(value: str) -> VehicleStatus:
    """Parse status string to VehicleStatus enum."""
    normalized = value.strip().lower()
    if normalized not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {value}. Must be one of {VALID_STATUSES}")
    return VehicleStatus(normalized)


def _parse_bool(value: str) -> bool:
    """Parse string to bool."""
    return value.strip().lower() in ("true", "1", "yes")


def _parse_int(value: str, default: int = 0) -> int:
    """Parse string to int with default."""
    stripped = value.strip()
    if not stripped:
        return default
    return int(stripped)


def load_vehicles_from_csv(path: str | Path) -> list[Vehicle]:
    """
    Load vehicles from a CSV file into memory.

    Expected CSV format (with header):
        vehicle_id,station_id,vehicle_type,status,rides_since_last_treated,last_treated_date

    - vehicle_type: bicycle | electric_bicycle | scooter
      (mapped to bike | ebike | scooter)
    - status: available | in_use | awaiting_report_review | degraded
    - rides_since_last_treated: number of rides since last maintenance

    Args:
        path: Path to the CSV file.

    Returns:
        List of Vehicle instances (Bike, EBike, or Scooter).
    """
    path = Path(path)
    if not path.exists():
        logger.warning("Vehicles CSV not found at %s", path)
        return []

    vehicles: list[Vehicle] = []

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []

        for row_num, row in enumerate(reader, start=2):  # 2 = header + 1
            try:
                vehicle_id = row.get(VEHICLE_ID, "").strip()
                frame_number = (
                    row.get(FRAME_NUMBER, "").strip() or f"FRAME-{vehicle_id}"
                )
                raw_type = row.get(VEHICLE_TYPE, "").strip().lower()
                vehicle_type = TYPE_MAP.get(raw_type, raw_type)
                status_str = row.get(STATUS, "available").strip() or "available"
                rides_since = _parse_int(row.get(RIDES_SINCE_LAST_TREATED, "0"), 0)

                if not vehicle_id:
                    logger.warning("Row %d: missing vehicle_id, skipping", row_num)
                    continue

                if vehicle_type not in VALID_TYPES:
                    logger.warning(
                        "Row %d: invalid vehicle_type '%s', skipping",
                        row_num,
                        raw_type,
                    )
                    continue

                status = _parse_status(status_str)

                vehicle: Vehicle
                if vehicle_type == "bike":
                    has_child_seat = _parse_bool(row.get(HAS_CHILD_SEAT, "false"))
                    vehicle = Bike(
                        vehicle_id=vehicle_id,
                        frame_number=frame_number,
                        has_child_seat=has_child_seat,
                        status=status,
                    )
                elif vehicle_type == "ebike":
                    battery_level = _parse_int(row.get(BATTERY_LEVEL, "100"), 100)
                    battery_level = max(0, min(100, battery_level))
                    vehicle = EBike(
                        vehicle_id=vehicle_id,
                        frame_number=frame_number,
                        battery_level=battery_level,
                        status=status,
                    )
                else:  # scooter
                    battery_level = _parse_int(row.get(BATTERY_LEVEL, "100"), 100)
                    battery_level = max(0, min(100, battery_level))
                    vehicle = Scooter(
                        vehicle_id=vehicle_id,
                        frame_number=frame_number,
                        battery_level=battery_level,
                        status=status,
                    )

                vehicle.ride_count = rides_since
                vehicle._last_maintenance_ride_count = 0
                vehicles.append(vehicle)

            except (ValueError, KeyError) as e:
                logger.warning("Row %d: parse error (%s), skipping", row_num, e)
                continue

    logger.info("Loaded %d vehicles from %s", len(vehicles), path)
    return vehicles
