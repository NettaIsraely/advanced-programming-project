from datetime import datetime
from tlvflow.domain.enums import ReportStatus

class VehicleReport:
    def __init__(self, report_id: str, user_id: str, vehicle_id: str, 
                 submission_time: datetime, image_url: str, 
                 description: str, status: ReportStatus):
        
        # Protected attributes
        self._report_id: str = report_id
        self._user_id: str = user_id
        self._vehicle_id: str = vehicle_id
        
        # Private attributes
        self.__submission_time: datetime = submission_time
        self.__image_url: str = image_url
        self.__description: str = description
        self.__status: ReportStatus = status

    def verify_damage(self):
        pass

    def submit_report(self):
        pass

    def _create_maintenance_event(self):
        pass