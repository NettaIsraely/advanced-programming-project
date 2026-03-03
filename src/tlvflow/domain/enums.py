from enum import Enum

class VehicleStatus(Enum):
    """Enumeration for vehicle status."""

    AVAILABLE = "available"
    IN_USE = "in_use"
    AWAITING_REPORT_REVIEW = "awaiting_report_review"
    DEGRADED = "degraded"

class ReportStatus(Enum):
    """Enumeration for vehicle report status."""
    
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"

class RideStatus(Enum):
    """Enumeration for ride status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
