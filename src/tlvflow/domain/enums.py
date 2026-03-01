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
    IN_USE = "in_use"
    VERIFIED = "verified"
    REJECTED = "rejected"