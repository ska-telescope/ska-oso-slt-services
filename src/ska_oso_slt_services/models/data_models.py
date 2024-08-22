from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class Operator(BaseModel):
    """
    Represents an operator in the SLT Shift Log Tool.

    :param name Optional[str]: The name of the operator.
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None


class Media(BaseModel):
    """
    Represents media associated with a shift in the SLT Shift Log Tool.

    :param type Optional[str]: The type of media (e.g., image, video).
    :param path Optional[str]: The path to the media file.
    """

    model_config = ConfigDict(extra="forbid")

    type: Optional[str] = None
    path: Optional[str] = None


class ShiftLogs(BaseModel):
    """
    Represents logs associated with a shift in the SLT Shift Log Tool.

    :param info Optional[dict]: Information about the log.
    :param source Optional[str]: The source of the log.
    :param log_time Optional[datetime]: The time the log was created.
    """

    model_config = ConfigDict(extra="forbid")

    info: Optional[dict] = None
    source: Optional[str] = None
    log_time: Optional[datetime] = None


class Shift(BaseModel):
    """
    Represents a shift in the SLT Shift Log Tool.

    :param sid Optional[int]: The unique identifier of the shift.
    :param shift_start Optional[datetime]: The start time of the shift.
    :param shift_end Optional[datetime]: The end time of the shift.
    :param shift_operator Optional[Operator]: The operator of the shift.
    :param shift_logs Optional[List[ShiftLogs]]: The logs associated with the shift.
    :param media Optional[List[Media]]: The media associated with the shift.
    :param annotations Optional[str]: Annotations for the shift.
    :param comments Optional[str]: Comments for the shift.
    :param created_by Optional[str]: The user who created the shift.
    :param created_time Optional[datetime]: The time the shift was created.
    :param last_modified_by Optional[str]: The user who last modified the shift.
    :param last_modified_time Optional[datetime]: The time the shift was last modified.
    """

    model_config = ConfigDict(extra="forbid")

    sid: Optional[int] = None
    shift_id: Optional[str] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    shift_operator: Optional[Operator] = None
    shift_logs: Optional[List[ShiftLogs]] = None
    media: Optional[List[Media]] = None
    annotations: Optional[str] = None
    comments: Optional[str] = None
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None
    last_modified_by: Optional[str] = None
    last_modified_time: Optional[datetime] = None
