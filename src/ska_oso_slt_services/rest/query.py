import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from dateutil.parser import ParserError, parse


@dataclass
class QueryParams:
    """
    QueryParams is an abstract class
    """


class MatchType(Enum):
    EQUALS = "equals"
    STARTS_WITH = "starts_with"
    CONTAINS = "contains"


@dataclass
class UserQuery(QueryParams):
    user: str = None
    shift_id: str = None
    match_type: MatchType = MatchType.EQUALS


@dataclass
class DateQuery(QueryParams):
    """
    Query that matches between date ranges
    """

    # can replace with StrEnum with Python 3.11
    class QueryType(Enum):
        CREATED_BETWEEN = "created_between"
        MODIFIED_BETWEEN = "modified_between"

    query_type: QueryType
    start: Optional[datetime.datetime] = None
    end: Optional[datetime.datetime] = None


class QueryParamsFactory:
    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        # Remove keys with None value
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        kwargs = convert_datetime_params(kwargs)

        def params_in_kwargs(allowed_fields: set) -> bool:
            """
            Currently the query functionality only supports a single type of QueryParam.
            This method checks that the allowed fields are present in the kwargs and
            that no other fields are also present, raising an error for the user if
            they are.
            """
            if any(k in kwargs for k in allowed_fields):
                query_fields = {
                    "user",
                    "created_before",
                    "created_after",
                    "last_modified_before",
                    "last_modified_after",
                    "shift_id",
                }

                if any([k in (query_fields - allowed_fields) for k in kwargs.keys()]):
                    raise ValueError(
                        "Different query types are not currently supported - for"
                        " example, cannot combine date created query or entity query"
                        " with a user query"
                    )

                return True
            return False

        if params_in_kwargs({"user"}) or params_in_kwargs({"shift_id"}):
            user = kwargs.get("user")
            shift_id = kwargs.get("shift_id")

            if kwargs.get("match_type"):
                return UserQuery(
                    user=user,
                    shift_id=shift_id,
                    match_type=MatchType(kwargs["match_type"]),
                )
            else:
                return UserQuery(user=user, shift_id=shift_id)

        elif params_in_kwargs({"created_before", "created_after"}):
            return DateQuery(
                DateQuery.QueryType.CREATED_BETWEEN,
                kwargs.get("created_after"),
                kwargs.get("created_before"),
            )

        elif params_in_kwargs({"last_modified_before", "last_modified_after"}):
            return DateQuery(
                DateQuery.QueryType.MODIFIED_BETWEEN,
                kwargs.get("last_modified_after"),
                kwargs.get("last_modified_before"),
            )
        raise ValueError(
            "Parameters are missing or not currently supported for querying."
        )


def convert_datetime_params(kwargs: dict) -> dict:
    """
    Converts the string datetime values in the input into Python datetime

    :returns: A new dict instance with the datetime string fields replaced
              by datetime objects
    :raises: ParserError if the string cannot be parsed
    """

    date_fields = [
        "created_before",
        "created_after",
        "last_modified_before",
        "last_modified_after",
    ]

    try:
        return {
            key: parse(value) if key in date_fields and kwargs.get(key) else value
            for key, value in kwargs.items()
        }
    except ParserError as err:
        raise ValueError(f"'{err.args[1]}' cannot be parsed as a datetime.") from err
