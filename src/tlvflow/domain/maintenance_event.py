from datetime import datetime
from uuid import uuid4

from tlvflow.domain.enums import EventStatus


class MaintenanceEvent:
    def __init__(
        self,
        vehicle_id: str,
        report_id: str,
        open_time: datetime,
        close_time: datetime,
    ):
        # Protected attributes
        self._event_id = uuid4().hex
        self._vehicle_id = vehicle_id
        self._report_id = report_id

        # Private attributes
        self.__open_time = open_time
        self.__close_time = close_time
        self.__status = EventStatus.OPEN

    def close_event(self) -> None:
        """
        Public method to close the maintenance event.
        """
        self.maintenance_event_status = EventStatus.CLOSED
