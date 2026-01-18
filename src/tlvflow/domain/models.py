from abc import ABC, abstractmethod
from tlvflow.domain.enums import VehicleStatus


class Vehicle(ABC):
    """Abstract base class representing a vehicle in the system."""
    
    # Protected attributes (using single underscore convention in Python)
    _vehicle_id: str
    _frame_number: str
    
    # Private attribute (using double underscore)
    __status: VehicleStatus
    
    # Public attributes
    ride_count: int
    has_helmet: bool
    
    def __init__(self, vehicle_id: str, frame_number: str, status: VehicleStatus = VehicleStatus.AVAILABLE):
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
    
    def check_maintenance_needed(self) -> bool:
        """
        Check if the vehicle needs maintenance.
        
        Returns:
            bool: True if maintenance is needed, False otherwise
        """
        # Abstract method - to be implemented by subclasses
        return False
    
    def check_status(self) -> VehicleStatus:
        """
        Check the current status of the vehicle.
        
        Returns:
            VehicleStatus: The current status of the vehicle
        """
        return self.__status
    
    # Property getters for protected attributes
    @property
    def vehicle_id(self) -> str:
        """Get the vehicle ID."""
        return self._vehicle_id
    
    @property
    def frame_number(self) -> str:
        """Get the frame number."""
        return self._frame_number
    
    @property
    def status(self) -> VehicleStatus:
        """Get the vehicle status."""
        return self.__status
    
    @status.setter
    def status(self, value: VehicleStatus) -> None:
        """Set the vehicle status."""
        self.__status = value
