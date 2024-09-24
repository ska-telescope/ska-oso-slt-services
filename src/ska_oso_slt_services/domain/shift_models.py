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

    type: Optional[str] = None
    path: Optional[str] = None


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


class Shift(SLTObject):
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

    shift_id: Optional[str] = None
    shift_start: AwareDatetime = Field(
        default_factory=lambda: get_datetime_for_timezone("UTC")
    )
    shift_end: Optional[datetime] = None
    shift_operator: Optional[str] = None
    shift_logs: Optional[List[ShiftLogs]] = None
    media: Optional[List[Media]] = None
    annotations: Optional[str] = None
    comments: Optional[str] = None
    metadata: Optional[Metadata] = None


class QueryType(Enum):
    """
    Enum representing the different types of queries available for filtering shifts.
    """

    CREATED_BETWEEN = "created_between"
    MODIFIED_BETWEEN = "modified_between"


class MatchType(Enum):
    # add doc string for MatchType Enum
    """
    Enum representing the different types of matching available for filtering shifts.
    """
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    CONTAINS = "contains"


class DateQuery(BaseModel):
    """
    Represents a query for filtering shifts based on date range.
    :param shift_start Optional[datetime]: The start time of the shift.
    :param shift_end Optional[datetime]: The end time of the shift.
    :param query_type QueryType: The type of query to perform.
    """

    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    query_type: QueryType = QueryType.CREATED_BETWEEN


class UserQuery(BaseModel):
    """
    Represents a query for filtering shifts based on user.
    :param shift_operator Optional[str]: The operator of the shift.
    :param match_type MatchType: The type of matching to perform.
    :param comments Optional[str]: Comments for the shift.
    :param shift_id: Optional[str] = None

    """

    comments: Optional[str] = None
    shift_operator: Optional[str] = None
    shift_id: Optional[str] = None
    match_type: MatchType = MatchType.EQUALS
