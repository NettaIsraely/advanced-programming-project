import base64
import hashlib
import hmac
import re
import secrets
from abc import ABC
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from tlvflow.domain.enums import RideStatus, VehicleStatus

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class User:
    """Base user in the system.

    Users are split into Pro and Amateur accounts. Amateur users can ride
    non-electric vehicles (bikes), while Pro users can ride any vehicle.
    """

    # Protected attributes
    _user_id: str
    _name: str
    _email: str
    _password_hash: str
    _payment_method_id: str

    # Ride tracking
    _ride_history: list[Any]
    _current_ride: Any | None

    # Password hashing parameters
    _PWD_ALGO = "pbkdf2_sha256"
    _PWD_ITERATIONS = 210_000
    _SALT_BYTES = 16
    _DKLEN = 32

    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        password_hash: str,
        payment_method_id: str,
    ) -> None:
        self._user_id = self._validate_user_id(user_id)
        self._name = self._validate_name(name)
        self._email = self._validate_email(email)
        self._password_hash = self._validate_password_hash(password_hash)
        self._payment_method_id = self._validate_payment_method_id(payment_method_id)

        self._ride_history = []
        self._current_ride = None

    # ----------------------------
    # Construction / authentication
    # ----------------------------
    @classmethod
    def register(
        cls,
        name: str,
        email: str,
        password: str,
        payment_method_id: str,
        *,
        user_id: str | None = None,
        license_number: str | None = None,
        license_expiry: datetime | None = None,
    ) -> "User":
        """Factory method used by the /register flow.

        Returns an instance with a generated user_id (uuid4 hex) unless provided.
        """
        uid = user_id or uuid4().hex
        pwd_hash = cls._hash_password(password)
        return cls(
            user_id=uid,
            name=name,
            email=email,
            password_hash=pwd_hash,
            payment_method_id=payment_method_id,
        )

    def login(self, password: str) -> bool:
        """Verify password against stored hash."""
        return self._verify_password(password, self._password_hash)

    # ----------------------------
    # Ride-related domain behavior
    # ----------------------------
    def start_ride(self, ride: Any) -> None:
        """Mark a ride as active for this user.

        Enforces the rule: a user cannot be on more than one active ride.
        """
        if self._current_ride is not None:
            raise ValueError("User already has an active ride")
        self._current_ride = ride

    def end_ride(self, ride: Any) -> None:
        """Finalize an active ride and append it to history."""
        if self._current_ride is None:
            raise ValueError("User has no active ride to end")
        if ride is not self._current_ride:
            raise ValueError("Ride mismatch: cannot end a different ride")
        self._ride_history.append(ride)
        self._current_ride = None

    def view_ride_history(self) -> tuple[Any, ...]:
        """Return an immutable snapshot of ride history."""
        return tuple(self._ride_history)

    def report_vehicle_issue(
        self,
        *,
        ride_id: str,
        vehicle_id: str,
        image_url: str | None = None,
        description: str = "",
    ) -> dict[str, str]:
        """Create a report payload for the service layer."""
        if not ride_id:
            raise ValueError("ride_id is required")
        if not vehicle_id:
            raise ValueError("vehicle_id is required")

        payload: dict[str, str] = {"ride_id": ride_id, "vehicle_id": vehicle_id}
        if image_url:
            payload["image_url"] = image_url
        if description:
            payload["description"] = description
        return payload

    # ----------------------------
    # Permissions
    # ----------------------------
    def can_rent(self, vehicle: "Vehicle") -> bool:
        """Amateur default: only non-electric bikes."""
        return isinstance(vehicle, Bike)

    # ----------------------------
    # Read-only properties
    # ----------------------------
    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def email(self) -> str:
        return self._email

    @property
    def payment_method_id(self) -> str:
        return self._payment_method_id

    @property
    def current_ride(self) -> Any | None:
        return self._current_ride

    # ----------------------------
    # Validation helpers
    # ----------------------------
    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")
        return user_id

    @staticmethod
    def _validate_name(name: str) -> str:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        return name.strip()

    @staticmethod
    def _validate_email(email: str) -> str:
        if not isinstance(email, str) or not _EMAIL_RE.match(email.strip()):
            raise ValueError("email must be a valid email address")
        return email.strip().lower()

    @staticmethod
    def _validate_payment_method_id(payment_method_id: str) -> str:
        if not isinstance(payment_method_id, str) or not payment_method_id.strip():
            raise ValueError("payment_method_id must be a non-empty string")
        return payment_method_id.strip()

    @classmethod
    def _validate_password_hash(cls, password_hash: str) -> str:
        if not isinstance(password_hash, str) or not password_hash.strip():
            raise ValueError("password_hash must be a non-empty string")
        # Accept only our own format: algo$iters$salt$hash
        parts = password_hash.split("$")
        if len(parts) != 4 or parts[0] != cls._PWD_ALGO:
            raise ValueError("password_hash has an invalid format")
        return password_hash

    # ----------------------------
    # Password hashing (stdlib)
    # ----------------------------
    @classmethod
    def _hash_password(cls, password: str) -> str:
        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("password must be a string with at least 8 characters")

        salt = secrets.token_bytes(cls._SALT_BYTES)
        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            cls._PWD_ITERATIONS,
            dklen=cls._DKLEN,
        )

        salt_b64 = base64.urlsafe_b64encode(salt).decode("ascii").rstrip("=")
        dk_b64 = base64.urlsafe_b64encode(dk).decode("ascii").rstrip("=")
        return f"{cls._PWD_ALGO}${cls._PWD_ITERATIONS}${salt_b64}${dk_b64}"

    @classmethod
    def _verify_password(cls, password: str, stored_hash: str) -> bool:
        try:
            algo, iters_s, salt_b64, dk_b64 = stored_hash.split("$", 3)
            if algo != cls._PWD_ALGO:
                return False
            iters = int(iters_s)
        except Exception:
            return False

        # Restore padding for base64 decode
        def _pad(s: str) -> str:
            return s + "=" * (-len(s) % 4)

        try:
            salt = base64.urlsafe_b64decode(_pad(salt_b64))
            expected = base64.urlsafe_b64decode(_pad(dk_b64))
        except Exception:
            return False

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iters,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)


class ProUser(User):
    """A user that can ride electric and non-electric vehicles (all vehicles)."""

    _license_number: str
    _license_expiry: datetime

    def __init__(
        self,
        user_id: str,
        name: str,
        email: str,
        password_hash: str,
        payment_method_id: str,
        *,
        license_number: str,
        license_expiry: datetime,
    ) -> None:
        super().__init__(
            user_id=user_id,
            name=name,
            email=email,
            password_hash=password_hash,
            payment_method_id=payment_method_id,
        )
        self._license_number = self._validate_license_number(license_number)
        self._license_expiry = self._validate_license_expiry(license_expiry)

    @classmethod
    def register(
        cls,
        name: str,
        email: str,
        password: str,
        payment_method_id: str,
        *,
        user_id: str | None = None,
        license_number: str | None = None,
        license_expiry: datetime | None = None,
    ) -> "ProUser":
        if not license_number:
            raise ValueError("license_number is required for ProUser")
        if license_expiry is None:
            raise ValueError("license_expiry is required for ProUser")
        uid = user_id or uuid4().hex
        pwd_hash = cls._hash_password(password)
        return cls(
            user_id=uid,
            name=name,
            email=email,
            password_hash=pwd_hash,
            payment_method_id=payment_method_id,
            license_number=license_number,
            license_expiry=license_expiry,
        )

    def validate_license(self, *, at: datetime | None = None) -> bool:
        """Return True if license is not expired at the given time (UTC)."""
        now = at or datetime.now(UTC)
        # Normalize naive datetimes as UTC
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        exp = self._license_expiry
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=UTC)
        return exp >= now

    def can_rent(self, vehicle: "Vehicle") -> bool:
        return self.validate_license()

    @staticmethod
    def _validate_license_number(license_number: str) -> str:
        if not isinstance(license_number, str) or not license_number.strip():
            raise ValueError("license_number must be a non-empty string")
        return license_number.strip()

    @staticmethod
    def _validate_license_expiry(license_expiry: datetime) -> datetime:
        if not isinstance(license_expiry, datetime):
            raise ValueError("license_expiry must be a datetime")
        return license_expiry


class AmateurUser(User):
    """Default user type (bike-only)."""

    pass


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


class Ride:
    """A ride: a user's use of a vehicle from start to end."""

    # Protected attributes (#)
    _ride_id: str
    _user_id: str
    _vehicle_id: str

    # Private attributes (-)
    __start_time: datetime
    __end_time: datetime | None
    __start_latitude: float
    __start_longitude: float
    __end_latitude: float
    __end_longitude: float
    __distance: float
    __fee: float
    __status: RideStatus

    def __init__(
        self,
        ride_id: str,
        user_id: str,
        vehicle_id: str,
        start_time: datetime,
        *,
        end_time: datetime | None = None,
        start_latitude: float = 0.0,
        start_longitude: float = 0.0,
        end_latitude: float = 0.0,
        end_longitude: float = 0.0,
        distance: float = 0.0,
        fee: float = 0.0,
    ) -> None:
        """
        Initialize a Ride instance.

        Args:
            ride_id: Unique identifier for the ride
            user_id: ID of the user taking the ride
            vehicle_id: ID of the vehicle used
            start_time: When the ride started (UTC)
            end_time: When the ride ended (UTC), or None if in progress
            start_latitude: Start location latitude
            start_longitude: Start location longitude
            end_latitude: End location latitude
            end_longitude: End location longitude
            distance: Distance travelled
            fee: Ride fee
        """
        self._ride_id = self._validate_ride_id(ride_id)
        self._user_id = self._validate_user_id(user_id)
        self._vehicle_id = self._validate_vehicle_id(vehicle_id)
        self.__start_time = self._validate_datetime(start_time, "start_time")
        self.__end_time = (
            self._validate_datetime(end_time, "end_time")
            if end_time is not None
            else None
        )
        self.__start_latitude = self._validate_float(start_latitude, "start_latitude")
        self.__start_longitude = self._validate_float(
            start_longitude, "start_longitude"
        )
        self.__end_latitude = self._validate_float(end_latitude, "end_latitude")
        self.__end_longitude = self._validate_float(end_longitude, "end_longitude")
        self.__distance = self._validate_float(distance, "distance")
        self.__fee = self._validate_float(fee, "fee")
        self.__status = (
            RideStatus.COMPLETED
            if self.__end_time is not None
            else RideStatus.IN_PROGRESS
        )

    def calculate_fee(self, duration: float, distance: float) -> float:
        """Calculate the ride fee from duration and distance. Returns the fee amount."""
        # Placeholder: override or extend for real pricing logic
        self.__distance = distance
        self.__fee = duration * 0.5 + distance * 0.2  # example formula
        return self.__fee

    def _process_payment(self) -> None:
        """Process payment for the ride (protected)."""
        # Placeholder: integrate with payment system
        pass

    def _log_ride(self) -> None:
        """Log the ride for history/analytics (protected)."""
        # Placeholder: persist or emit ride record
        pass

    def __handle_tracking_error(self) -> None:
        """Handle tracking/location error (private)."""
        # Placeholder: error handling for GPS/tracking
        pass

    def end(self, at: datetime | None = None) -> None:
        """Mark the ride as completed at the given time (UTC)."""
        if self.__end_time is not None:
            raise ValueError("Ride is already ended")
        now = at or datetime.now(UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        if now < self.__start_time:
            raise ValueError("end_time cannot be before start_time")
        self.__end_time = now
        self.__status = RideStatus.COMPLETED

    def status(self) -> RideStatus:
        """Return the current status of the ride."""
        return self.__status

    def is_active(self) -> bool:
        """Return True if the ride is in progress."""
        return self.__end_time is None

    @staticmethod
    def _validate_ride_id(ride_id: str) -> str:
        if not isinstance(ride_id, str) or not ride_id.strip():
            raise ValueError("ride_id must be a non-empty string")
        return ride_id.strip()

    @staticmethod
    def _validate_user_id(user_id: str) -> str:
        if not isinstance(user_id, str) or not user_id.strip():
            raise ValueError("user_id must be a non-empty string")
        return user_id.strip()

    @staticmethod
    def _validate_vehicle_id(vehicle_id: str) -> str:
        if not isinstance(vehicle_id, str) or not vehicle_id.strip():
            raise ValueError("vehicle_id must be a non-empty string")
        return vehicle_id.strip()

    @staticmethod
    def _validate_datetime(value: datetime, name: str) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{name} must be a datetime")
        return value

    @staticmethod
    def _validate_float(value: float, name: str) -> float:
        if not isinstance(value, int | float):
            raise ValueError(f"{name} must be a number")
        return float(value)
