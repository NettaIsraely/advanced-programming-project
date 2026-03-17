from datetime import UTC, datetime

from tlvflow.domain.rides import Ride
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.in_memory import StationRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.users_repository import UsersRepository


def start_ride(
    user_id: str,
    station_id: int,
    rides_repo: RidesRepository,
    active_users_repo: ActiveUsersRepository,
    station_repo: StationRepository,
    users_repo: UsersRepository,
) -> tuple[str, str]:
    """
    Start a new ride for a user from a given station.

    Args:
        user_id: The ID of the user starting the ride.
        station_id: The ID of the station they are taking the vehicle from.
        rides_repo: Repository to save the new ride.
        active_users_repo: Repository to track users currently on a ride.
        station_repo: Repository to fetch station and vehicle data.
        users_repo: Repository to validate the user.

    Returns:
        A tuple of (ride_id, vehicle_id).

    Raises:
        ValueError: If validation fails (user not found, station empty, etc.)
    """

    # 1. Validate the user exists
    user = users_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    # 2. Check if the user already has an active ride
    if active_users_repo.get_ride_id(user_id) is not None:
        raise ValueError("User already has an active ride")

    # 3. Validate the station exists and has vehicles
    station = station_repo.get_by_id(station_id)
    if not station:
        raise ValueError(f"Station {station_id} not found")

    vehicle_id = "vehicle_id_placeholder"  # TODO: Get an actual available vehicle ID from the station

    if station.is_empty:
        raise ValueError(f"Station {station_id} has no available vehicles")

    ride = Ride(
        user_id=user_id,
        vehicle_id=vehicle_id,
        start_time=datetime.now(UTC),
        start_latitude=station.latitude,
        start_longitude=station.longitude,
    )

    return (ride.ride_id, vehicle_id)
