from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from ska_oso_slt_services.utils.codec import SLTObject
from ska_oso_slt_services.utils.date_utils import get_datetime_for_timezone


class Metadata(SLTObject):
    """Represents metadata about other entities."""

    created_by: Optional[str] = None
    created_on: AwareDatetime = Field(
        default_factory=lambda: get_datetime_for_timezone("UTC")
    )
    last_modified_by: Optional[str] = None
    last_modified_on: AwareDatetime = Field(
        default_factory=lambda: get_datetime_for_timezone("UTC")
    )


class Operator(SLTObject):
    """
    Represents an operator in the SLT Shift Log Tool.

    :param name Optional[str]: The name of the operator.
    """

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None


class Media(SLTObject):
    """
    Represents media associated with a shift in the SLT Shift Log Tool.

    :param type Optional[str]: The type of media (e.g., image, video).
    :param path Optional[str]: The path to the media file.
    """

    file_extension: Optional[str] = None
    path: Optional[str] = None
    unique_id: Optional[str] = None


class ShiftLogImage(SLTObject):
    path: str
    timestamp: AwareDatetime = Field(
        default_factory=lambda: get_datetime_for_timezone("UTC")
    )


class ShiftLogComment(SLTObject):

    id: Optional[int] = None
    log_comment: Optional[str] = None
    operator_name: Optional[str] = None
    shift_id: Optional[str] = None
    image: Optional[ShiftLogImage] = None
    eb_id: Optional[str] = None
    metadata: Optional[Metadata] = None


class ShiftComment(SLTObject):

    id: Optional[int] = None
    comment: Optional[str] = None
    shift_id: Optional[str] = None
    image: Optional[ShiftLogImage] = None
    metadata: Optional[Metadata] = None


class ShiftLogs(SLTObject):
    """
    Represents logs associated with a shift in the SLT Shift Log Tool.

    :param info Optional[dict]: Information about the log.
    :param source Optional[str]: The source of the log.
    :param log_time Optional[datetime]: The time the log was created.
    """

    # model_config = ConfigDict(extra="forbid")

    info: Optional[dict] = None
    source: Optional[str] = None
    log_time: Optional[datetime] = None
    comments: Optional[List[ShiftLogComment]] = None


class ShiftBaseClass(SLTObject):
    # TODO Revisit this code later to check
    # how we make shift_id make compulsory.
    """
    :param shift_id Optional[int]: The unique identifier of the shift.
    :param shift_start Optional[datetime]: The start time of the shift.
    :param shift_end Optional[datetime]: The end time of the shift.
    :param shift_operator Optional[Operator]: The operator of the shift.
    :param annotations Optional[str]: Annotations for the shift.
    :param comments Optional[str]: Comments for the shift.
    """

    shift_id: Optional[str] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    shift_operator: Optional[str] = None
    annotations: Optional[str] = None
    comments: Optional[List[ShiftComment]] = None


class Shift(ShiftBaseClass):
    """
    Represents a shift in the SLT Shift Log Tool.


    :param shift_logs Optional[List[ShiftLogs]]: The logs associated with the shift.
    :param media Optional[List[Media]]: The media associated with the shift.
    :param metadata Optional[Metadat]: Metadata contains shift additional info
    like shift created_on, created_bye etc...
    """

    shift_logs: Optional[List[ShiftLogs]] = None
    media: Optional[List[Media]] = None
    metadata: Optional[Metadata] = None


class Filter(Enum):
    # add doc string for MatchType Enum
    """
    Enum representing the different types of matching available for filtering shifts.
    """
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    CONTAINS = "contains"


class SbiStatus(Enum):
    # TODO revisit this class later might be need to
    # add dependency of PDM or simle enter text.
    """
    Enum representing the different status values for
    an SBI entity in the SLT Shift Log Tool.
    :param CREATED: The SBI entity has been created.
    :param IN_PROGRESS: The SBI entity is in progress.
    :param COMPLETED: The SBI entity has been completed.
    :param CANCELLED: The SBI entity has been cancelled.
    """

    CREATED = "Created"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class SbiEntityStatus(BaseModel):
    """
    Represents the status of an SBI entity in the SLT Shift Log Tool.

    :param sbi_status Optional[SbiStatus]: The status of the SBI entity.
    """

    sbi_status: Optional[SbiStatus] = None


class MatchType(BaseModel):
    """
    Represents a query for filtering shifts based on text.
    :param match_type Optional[Filter]: The type of matching to perform.
    """

    match_type: Optional[Filter] = None
