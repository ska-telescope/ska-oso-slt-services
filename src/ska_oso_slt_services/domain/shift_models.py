from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from ska_oso_pdm.entity_status_history import SBIStatus

from ska_oso_slt_services.common.codec import SLTObject
from ska_oso_slt_services.common.date_utils import get_datetime_for_timezone


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

    path: Optional[str] = None
    unique_id: Optional[str] = None
    timestamp: AwareDatetime = Field(
        default_factory=lambda: get_datetime_for_timezone("UTC")
    )


class ShiftLogComment(SLTObject):
    """
    Represents a comment associated with a shift in the SLT Shift Log Tool.

    :param id Optional[int]: The unique identifier of the comment.
    :param log_comment Optional[str]: The text of the comment.
    :param operator_name Optional[str]: The name of the operator who made the comment.
    :param shift_id Optional[str]: The unique identifier of the shift
     the comment belongs to.
    :param image Optional[List[Media]]: The image associated with the comment.
    :param eb_id Optional[str]: The unique identifier of the EB associated
     with the comment.
    :param metadata Optional[Metadata]: Metadata contains shift additional info
     like shift created_on, created_bye etc...
    """

    id: Optional[int] = None
    log_comment: Optional[str] = None
    operator_name: Optional[str] = None
    shift_id: Optional[str] = None
    image: Optional[List[Media]] = None
    eb_id: Optional[str] = None
    metadata: Optional[Metadata] = None


class ShiftComment(SLTObject):
    """
    Represents a comment associated with a shift in the SShift.

    :param id Optional[int]: The unique identifier of the comment.
    :param comment Optional[str]: The text of the comment.
    :param operator_name Optional[str]: The name of the operator who made the comment.
    :param shift_id Optional[str]: The unique identifier of the shift the comment
     belongs to.
    :param image Optional[List[Media]]: The image associated with the comment.
    :param metadata Optional[Metadata]: Metadata contains shift additional info
    like shift created_on, created_bye etc...
    """

    id: Optional[int] = None
    comment: Optional[str] = None
    operator_name: Optional[str] = None
    shift_id: Optional[str] = None
    image: Optional[List[Media]] = None
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
    :param shift_id Optional[str]: The unique identifier of the shift.
    :param shift_start Optional[datetime]: The start time of the shift.
    :param shift_end Optional[datetime]: The end time of the shift.
    :param shift_operator Optional[str]: The operator of the shift.
    :param annotations Optional[str]: Annotations for the shift.
    :param comments Optional[List[ShiftComment]]: List of comments for the shift.
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


class SbiEntityStatus(BaseModel):
    """
    Represents the status of an SBI entity in the SLT Shift Log Tool.

    :param sbi_status Optional[SBDStatus]: The status of the SBI entity.
    """

    sbi_status: Optional[SBIStatus] = None


class MatchType(BaseModel):
    """
    Represents a query for filtering shifts based on text.
    :param match_type Optional[Filter]: The type of matching to perform.
    """

    match_type: Optional[Filter] = None
