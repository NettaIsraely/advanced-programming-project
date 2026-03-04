from datetime import datetime
from uuid import UUID

import pytest

from tlvflow.domain.enums import EventStatus
from tlvflow.domain.maintenance_event import MaintenanceEvent


class TestMaintenanceEvent:

    @pytest.fixture
    def sample_data(self):
        return {
            "vehicle_id": "1234",
            "report_id": "ABCD",
            "open_time": datetime(2023, 10, 1, 10, 0, 0),
        }

    @pytest.fixture
    def event(self, sample_data):
        return MaintenanceEvent(**sample_data)

    def test_initialization(self, event, sample_data):
        """Verify that the object initializes with correct values and defaults."""
        # Testing protected attributes
        assert event._vehicle_id == sample_data["vehicle_id"]
        assert event._report_id == sample_data["report_id"]
        assert event._closed_time is None

        # Testing auto-generated hex ID (validating it's a valid hex string)
        assert len(event._event_id) == 32
        UUID(event._event_id)  # Should not raise ValueError

        # Testing private attributes (Name Mangling)
        assert event._MaintenanceEvent__open_time == sample_data["open_time"]
        assert event._MaintenanceEvent__status == EventStatus.OPEN

    def test_close_event_updates_status(self, event):
        """Verify that closing an event changes status and sets a timestamp."""
        assert event._MaintenanceEvent__status == EventStatus.OPEN
        assert event._closed_time is None

        event.close_event()

        assert event._MaintenanceEvent__status == EventStatus.CLOSED
        assert isinstance(event._closed_time, datetime)
        # Ensure the timestamp is very recent (within 1 second)
        assert (datetime.now() - event._closed_time).total_seconds() < 1

    def test_close_event_twice(self, event):
        """Verify that calling close_event multiple times still results in CLOSED state."""
        event.close_event()
        first_close = event._closed_time

        event.close_event()

        assert event._MaintenanceEvent__status == EventStatus.CLOSED
        # The timestamp will update again based on your current method logic
        assert event._closed_time >= first_close
