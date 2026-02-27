"""
Unit tests for tlvflow.domain.vehicles (Vehicle/Bike/EBike/Scooter).
"""

from __future__ import annotations

import pytest

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.vehicles import Bike, EBike, Scooter, Vehicle


# Vehicle is abstract-ish via the is_electric property. We create a minimal
# concrete subclass that DOES NOT override is_electric, to ensure the base property raises.
class _BadVehicle(Vehicle):
    pass


# Minimal report object used to trigger the "user reported maintenance needed"
# branch. It only needs a _vehicle_id attribute.
class _Report:
    def __init__(self, vehicle_id: str):
        self._vehicle_id = vehicle_id


# Report-like object that does NOT have _vehicle_id, to ensure the
# hasattr(report, "_vehicle_id") guard works and does not trigger maintenance.
class _ReportWithoutVehicleId:
    def __init__(self):
        self.some_other_field = "x"


# Verify Vehicle.__init__ initializes fields correctly and check_status()
# returns what was passed in, including a non-default status.
def test_vehicle_init_and_check_status_sets_expected_state() -> None:
    v = Bike(vehicle_id="V1", frame_number="F1", status=VehicleStatus.DEGRADED)

    assert v._vehicle_id == "V1"
    assert v._frame_number == "F1"
    assert v.ride_count == 0
    assert v.has_helmet is False
    assert v._last_maintenance_ride_count == 0
    assert v.check_status() == VehicleStatus.DEGRADED


# Ensure the base Vehicle.is_electric property raises NotImplementedError
# when not implemented by a subclass.
def test_vehicle_is_electric_base_property_raises() -> None:
    v = _BadVehicle(vehicle_id="V2", frame_number="F2")
    with pytest.raises(NotImplementedError):
        _ = v.is_electric


# Verify Bike's is_electric is False and EBike/Scooter is True.
def test_is_electric_property_per_type() -> None:
    assert Bike("B1", "FB1").is_electric is False
    assert EBike("E1", "FE1").is_electric is True
    assert Scooter("S1", "FS1").is_electric is True


# Cover the "10+ rides since last maintenance" branch in Vehicle.check_maintenance_needed.
def test_maintenance_needed_when_ten_or_more_rides_since_last_maintenance() -> None:
    b = Bike("B2", "FB2")
    b.ride_count = 10
    b._last_maintenance_ride_count = 0

    assert b.check_maintenance_needed() is True


# Cover the "reports is None or empty" path where maintenance is NOT needed.
def test_maintenance_not_needed_when_under_threshold_and_no_reports() -> None:
    b = Bike("B3", "FB3")
    b.ride_count = 9
    b._last_maintenance_ride_count = 0

    assert b.check_maintenance_needed() is False
    assert b.check_maintenance_needed([]) is False


# Cover the report loop branch that triggers maintenance when a report matches _vehicle_id.
def test_maintenance_needed_when_matching_report_exists() -> None:
    b = Bike("B4", "FB4")
    b.ride_count = 1
    b._last_maintenance_ride_count = 0

    reports = [_Report("OTHER"), _Report("B4")]
    assert b.check_maintenance_needed(reports) is True


# Cover the report loop branch where reports are present but do NOT match,
# including an object without _vehicle_id (hasattr guard).
def test_maintenance_not_needed_when_reports_do_not_match_or_missing_attr() -> None:
    b = Bike("B5", "FB5")
    b.ride_count = 1
    b._last_maintenance_ride_count = 0

    reports = [_Report("OTHER"), _ReportWithoutVehicleId()]
    assert b.check_maintenance_needed(reports) is False


# Cover complete_maintenance(), ensuring it updates _last_maintenance_ride_count
# and therefore affects subsequent maintenance checks.
def test_complete_maintenance_resets_maintenance_counter() -> None:
    b = Bike("B6", "FB6")
    b.ride_count = 12
    assert b.check_maintenance_needed() is True

    b.complete_maintenance()
    assert b._last_maintenance_ride_count == 12
    assert b.check_maintenance_needed() is False

    b.ride_count = 21  # 9 rides since last maintenance
    assert b.check_maintenance_needed() is False

    b.ride_count = 22  # 10 rides since last maintenance
    assert b.check_maintenance_needed() is True


# Cover EBike battery validation: values below 0 and above 100 should raise ValueError.
@pytest.mark.parametrize("battery_level", [-1, 101])
def test_ebike_invalid_battery_level_raises(battery_level: int) -> None:
    with pytest.raises(ValueError):
        EBike("E2", "FE2", battery_level=battery_level)


# Cover Scooter battery validation: values below 0 and above 100 should raise ValueError.
@pytest.mark.parametrize("battery_level", [-50, 150])
def test_scooter_invalid_battery_level_raises(battery_level: int) -> None:
    with pytest.raises(ValueError):
        Scooter("S2", "FS2", battery_level=battery_level)


# Cover EBike.check_maintenance_needed battery-based condition:
# if base maintenance is False but battery < 20, it should still return True.
def test_ebike_maintenance_needed_when_battery_low_even_if_base_false() -> None:
    e = EBike("E3", "FE3", battery_level=19)
    e.ride_count = 0
    e._last_maintenance_ride_count = 0

    assert e.check_maintenance_needed() is True


# Cover EBike.check_maintenance_needed where base maintenance is True,
# ensuring it returns True regardless of battery level.
def test_ebike_maintenance_needed_when_base_true_even_if_battery_ok() -> None:
    e = EBike("E4", "FE4", battery_level=100)
    e.ride_count = 10
    e._last_maintenance_ride_count = 0

    assert e.check_maintenance_needed() is True


# Cover EBike.check_maintenance_needed where both base maintenance is False
# and battery is NOT low, so result should be False.
def test_ebike_maintenance_not_needed_when_base_false_and_battery_ok() -> None:
    e = EBike("E5", "FE5", battery_level=20)
    e.ride_count = 3
    e._last_maintenance_ride_count = 0

    assert e.check_maintenance_needed() is False


# Mirror the EBike battery logic tests for Scooter: low battery triggers maintenance.
def test_scooter_maintenance_needed_when_battery_low_even_if_base_false() -> None:
    s = Scooter("S3", "FS3", battery_level=0)
    s.ride_count = 0
    s._last_maintenance_ride_count = 0

    assert s.check_maintenance_needed() is True


# Scooter returns True when base maintenance is True, regardless of battery.
def test_scooter_maintenance_needed_when_base_true_even_if_battery_ok() -> None:
    s = Scooter("S4", "FS4", battery_level=100)
    s.ride_count = 10
    s._last_maintenance_ride_count = 0

    assert s.check_maintenance_needed() is True


# Scooter returns False when base maintenance is False and battery is not low.
def test_scooter_maintenance_not_needed_when_base_false_and_battery_ok() -> None:
    s = Scooter("S5", "FS5", battery_level=20)
    s.ride_count = 2
    s._last_maintenance_ride_count = 0

    assert s.check_maintenance_needed() is False
