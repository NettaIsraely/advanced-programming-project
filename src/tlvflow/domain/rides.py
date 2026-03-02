"""Ride domain model."""

from uuid import UUID, uuid4


class Ride:
    """A ride in the system."""

    _ride_id: UUID

    def __init__(self, ride_id: UUID | str | None = None) -> None:
        """
        Initialize a Ride instance.

        Args:
            ride_id: Unique identifier (UUID). If None, a new UUID is generated.
        """
        if ride_id is None:
            self._ride_id = uuid4()
        elif isinstance(ride_id, UUID):
            self._ride_id = ride_id
        else:
            self._ride_id = self._parse_uuid(ride_id)

    @staticmethod
    def _parse_uuid(value: str) -> UUID:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("ride_id must be a non-empty string or UUID")
        try:
            return UUID(value.strip())
        except ValueError as e:
            raise ValueError("ride_id must be a valid UUID") from e

    @property
    def ride_id(self) -> UUID:
        """Return the ride's UUID."""
        return self._ride_id
