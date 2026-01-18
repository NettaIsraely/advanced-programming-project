from abc import ABC
from typing import Any

from tlvflow.domain.enums import VehicleStatus


class Vehicle(ABC):
    """Abstract base class representing a vehicle in the system."""

    # Protected attributes
    _vehicle_id: str
    _frame_number: str

    # Private attribute
    __status: VehicleStatus

    # Public attributes
    ride_count: int
    has_helmet: bool

    # Protected attribute for tracking maintenance
    _last_maintenance_ride_count: int

    def __init__(
        self,
        vehicle_id: str,
        frame_number: str,
        status: VehicleStatus = VehicleStatus.AVAILABLE,
    ):
        """
        Initialize a Vehicle instance.

        Args:
            vehicle_id: Unique identifier for the vehicle
            frame_number: Frame/chassis number of the vehicle
            status: Current status of the vehicle (default: AVAILABLE)
        """
        self._vehicle_id = vehicle_id
        self._frame_number = frame_number
        self.__status = status
        self.ride_count = 0
        self.has_helmet = False
        self._last_maintenance_ride_count = 0

    def check_maintenance_needed(self, reports: list[Any] | None = None) -> bool:
        """
        Check if the vehicle needs maintenance.

        Maintenance is needed if:
        - 10 or more rides have been done since last maintenance, OR
        - A user has reported maintenance needed (via VehicleReport)

        Args:
            reports: Optional list of VehicleReport instances to check for user reports

        Returns:
            bool: True if maintenance is needed, False otherwise
        """
        # Check if 10+ rides since last maintenance
        rides_since_maintenance = self.ride_count - self._last_maintenance_ride_count
        if rides_since_maintenance >= 10:
            return True

        # Check if there are any reports for this vehicle
        if reports:
            # Assuming VehicleReport has a vehicle_id attribute
            # that matches self._vehicle_id
            for report in reports:
                if (
                    hasattr(report, "_vehicle_id")
                    and report._vehicle_id == self._vehicle_id
                ):
                    return True

        return False

    def complete_maintenance(self) -> None:
        """
        Mark maintenance as complete, resetting the maintenance tracking.
        """
        self._last_maintenance_ride_count = self.ride_count

    def check_status(self) -> VehicleStatus:
        """
        Check the current status of the vehicle.

        Returns:
            VehicleStatus: The current status of the vehicle
        """
        return self.__status


class Bike(Vehicle):
    """Bike subclass representing a regular bicycle."""

    has_child_seat: bool

    def __init__(
        self,
        vehicle_id: str,
        frame_number: str,
        has_child_seat: bool = False,
        status: VehicleStatus = VehicleStatus.AVAILABLE,
    ):
        """
        Initialize a Bike instance.

        Args:
            vehicle_id: Unique identifier for the bike
            frame_number: Frame number of the bike
            has_child_seat: Whether the bike has a child seat (default: False)
            status: Current status of the bike (default: AVAILABLE)
        """
        super().__init__(vehicle_id, frame_number, status)
        self.has_child_seat = has_child_seat

    def check_maintenance_needed(self, reports: list[Any] | None = None) -> bool:
        """
        Check if the bike needs maintenance.

        Args:
            reports: Optional list of VehicleReport instances to check for user reports

        Returns:
            bool: True if maintenance is needed (10+ rides since last
                maintenance or user reported), False otherwise
        """
        return super().check_maintenance_needed(reports)


class EBike(Vehicle):
    """EBike subclass representing an electric bicycle."""

    battery_level: int

    def __init__(
        self,
        vehicle_id: str,
        frame_number: str,
        battery_level: int = 100,
        status: VehicleStatus = VehicleStatus.AVAILABLE,
    ):
        """
        Initialize an EBike instance.

        Args:
            vehicle_id: Unique identifier for the e-bike
            frame_number: Frame number of the e-bike
            battery_level: Battery level percentage (0-100, default: 100)
            status: Current status of the e-bike (default: AVAILABLE)
        """
        super().__init__(vehicle_id, frame_number, status)
        if not 0 <= battery_level <= 100:
            raise ValueError("Battery level must be between 0 and 100")
        self.battery_level = battery_level

    def check_maintenance_needed(self, reports: list[Any] | None = None) -> bool:
        """
        Check if the e-bike needs maintenance.

        Args:
            reports: Optional list of VehicleReport instances to check for user reports

        Returns:
            bool: True if maintenance is needed (10+ rides since last
                maintenance, user reported, or low battery), False otherwise
        """
        # Check base maintenance conditions (rides or user report)
        base_maintenance = super().check_maintenance_needed(reports)
        # Also check battery level
        return base_maintenance or self.battery_level < 20


class Scooter(Vehicle):
    """Scooter subclass representing an electric scooter."""

    battery_level: int

    def __init__(
        self,
        vehicle_id: str,
        frame_number: str,
        battery_level: int = 100,
        status: VehicleStatus = VehicleStatus.AVAILABLE,
    ):
        """
        Initialize a Scooter instance.

        Args:
            vehicle_id: Unique identifier for the scooter
            frame_number: Frame number of the scooter
            battery_level: Battery level percentage (0-100, default: 100)
            status: Current status of the scooter (default: AVAILABLE)
        """
        super().__init__(vehicle_id, frame_number, status)
        if not 0 <= battery_level <= 100:
            raise ValueError("Battery level must be between 0 and 100")
        self.battery_level = battery_level

    def check_maintenance_needed(self, reports: list[Any] | None = None) -> bool:
        """
        Check if the scooter needs maintenance.

        Args:
            reports: Optional list of VehicleReport instances to check for user reports

        Returns:
            bool: True if maintenance is needed (10+ rides since last
                maintenance, user reported, or low battery), False otherwise
        """
        # Check base maintenance conditions (rides or user report)
        base_maintenance = super().check_maintenance_needed(reports)
        # Also check battery level
        return base_maintenance or self.battery_level < 20
