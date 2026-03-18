from datetime import UTC, datetime

from tlvflow.domain.enums import VehicleStatus
from tlvflow.domain.rides import Ride
from tlvflow.persistence.active_users_repository import ActiveUsersRepository
from tlvflow.persistence.in_memory import StationRepository, VehicleRepository
from tlvflow.persistence.rides_repository import RidesRepository
from tlvflow.persistence.users_repository import UsersRepository


async def start_ride(
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

    # Validate the user exists
    user = users_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Check if the user already has an active ride
    if active_users_repo.get_ride_id(user_id) is not None:
        raise ValueError("User already has an active ride")

    # Validate the station exists and has vehicles
    station = station_repo.get_by_id(station_id)
    if not station:
        raise ValueError(f"Station {station_id} not found")

    if station.is_empty:
        raise ValueError(f"Station {station_id} has no available vehicles")

    # Checkout a vehicle from the station
    try:
        vehicle_id = station.checkout_vehicle().vehicle_id
    except Exception as e:
        raise ValueError(f"Failed to checkout vehicle: {str(e)}")

    ride = Ride(
        user_id=user_id,
        vehicle_id=vehicle_id,
        start_time=datetime.now(UTC),
        start_latitude=station.latitude,
        start_longitude=station.longitude,
    )

    rides_repo.add(ride)
    active_users_repo.set_active(user_id, ride.ride_id)

    return (ride.ride_id, vehicle_id)


async def end_ride(
    user_id: str,
    vehicle_id: str,
    rides_repo: RidesRepository,
    active_users_repo: ActiveUsersRepository,
    users_repo: UsersRepository,
    vehicle_repo: VehicleRepository,
) -> tuple[str, float]:
    """
    End an active ride for a user, calculate the fee, and release the vehicle.

    Args:
        user_id: The ID of the user ending the ride.
        vehicle_id: The ID of the vehicle being returned.
        rides_repo: Repository to fetch and update the ride.
        active_users_repo: Repository to check and remove the user's active status.
        users_repo: Repository to validate the user.
        vehicle_repo: Repository to update the vehicle's status.

    Returns:
        A tuple of (ride_id, fee).

    Raises:
        ValueError: If validation fails (user not found, no active ride, wrong vehicle).
    """

    # Validate the user exists
    user = users_repo.get_by_id(user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    # Get the user's active ride_id
    ride_id = active_users_repo.get_ride_id(user_id)
    if not ride_id:
        raise ValueError(f"User {user_id} does not have an active ride")

    # Fetch the actual Ride object
    ride = rides_repo.get_by_id(ride_id)
    if not ride:
        raise ValueError(f"Active ride {ride_id} not found")

    # Verify the vehicle ID matches the ongoing ride
    if ride.vehicle_id != vehicle_id:
        raise ValueError(
            f"Provided vehicle_id ({vehicle_id}) does not match the active ride"
        )

    # End the ride using the domain model method
    end_time = datetime.now(UTC)
    ride.end(at=end_time)

    # Calculate duration and fee
    duration_minutes = (end_time - ride.start_time).total_seconds() / 60.0
    placeholder_distance = 5.0  # As we have no real GPS tracking, we use a placeholder distance. In a real implementation, this would be calculated based on the start and end locations.
    fee = ride.calculate_fee(duration=duration_minutes, distance=placeholder_distance)

    # Update the vehicle status back to AVAILABLE
    vehicle = vehicle_repo.get_by_id(vehicle_id)
    if vehicle:
        vehicle.set_status(VehicleStatus.AVAILABLE)
        vehicle.rides_since_last_treated += 1

    # Remove the user from the active users list
    active_users_repo.clear(user_id)

    # Return the data required by RideEndResponse
    return ride.ride_id, fee
