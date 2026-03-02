from datetime import datetime
from tlvflow.domain.enums import ReportStatus
import re
from uuid import uuid4

class VehicleReport:
    def __init__(self, user_id: str, vehicle_id: str, 
                 submission_time: datetime, image_url: str, 
                 description: str):
        
        # Protected attributes
        self._report_id: str = uuid4().hex
        self._user_id: str = user_id
        self._vehicle_id: str = vehicle_id
        
        # Private attributes
        self.__submission_time: datetime = submission_time
        self.__image_url: str = image_url
        self.__description: str = description
        self.__status: ReportStatus = ReportStatus.SUBMITTED

    def verify_damage(self):
        mock_ai_validation_result=True # As we do not have the tools to review the photo and analyse a vehicle's damage, a mock of such a test's result
        img_url_pattern = r'^https?://.*\.(?:png|jpg|jpeg|gif|bmp)$' # Review a valid image URL structure
        if re.match(img_url_pattern, self.__image_url, re.IGNORECASE) is None or not mock_ai_validation_result:
            self.__status=ReportStatus.REJECTED
            return False
        self.__status=ReportStatus.VERIFIED
        return True

    def submit_report(self):
        self.__status=ReportStatus.SUBMITTED

    def _create_maintenance_event(self):
        #TODO - implement after creating maintance event class
        pass