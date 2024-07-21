from typing import Optional
from datetime import datetime
from ska_oso_slt_services.pydantic_data_models.base_data_models import BaseModelWithTimestamp
# from base_data_models import BaseModelWithTimestamp


class ODASLT(BaseModelWithTimestamp):
    comments: Optional[str] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    annotation: Optional[str] = None


class ODASLTLogs(BaseModelWithTimestamp):
    slt_ref: Optional[int] = None
    info: Optional[dict] = None
    source: Optional[str] = None


class ODASLTImages(BaseModelWithTimestamp):
    slt_ref: Optional[int] = None
    image_path: Optional[list[str]] = None
