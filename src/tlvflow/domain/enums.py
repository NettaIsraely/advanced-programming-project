from enum import Enum


class VehicleStatus(Enum):
    """Enumeration for vehicle status."""

    AVAILABLE = "available"
    IN_USE = "in_use"
    AWAITING_REPORT_REVIEW = "awaiting_report_review"
    DEGRADED = "degraded"
