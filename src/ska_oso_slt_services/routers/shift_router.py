import logging
import traceback
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Response

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresConnection
from ska_oso_slt_services.models.data_models import DateQuery, Shift, UserQuery
from ska_oso_slt_services.repositories.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)
from pydantic import ValidationError

shift_repository = PostgresShiftRepository
connection_pool = PostgresConnection().get_connection()


router = APIRouter(prefix="/api/v1")


def error_handler(api_fn: Callable[[str], Response]) -> Callable[[str], Response]:
    """
    A decorator function to catch general errors and wrap in the correct HTTP
    response

    :param api_fn: A function which accepts an entity identifier and returns
    an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError as err:

            return {"detail": str(err.args[0])}, HTTPStatus.NOT_FOUND

        except (ValueError, ValidationError) as e:
            LOGGER.exception(
                "ValueError occurred when adding entity, likely some semantic"
                " validation failed"
            )

            return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

        except Exception as e:  # pylint: disable=broad-exception-caught
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper


@router.get("/shift", tags=["shifts"])
async def get_shift(shift_id: Optional[str] = None):
    """
    Retrieve a list of shifts filtered by the specified start and end times.

    :param shift_start Optional[str]: The start time to filter shifts in ISO format.
     If None, no start time filter is applied.
    :param shift_end Optional[str]: The end time to filter shifts in ISO format. If
    None, no end time filter is applied.
    :returns: A list of Shift objects in JSON format and an HTTP status code.
    """

    shift_service = ShiftService()
    shifts = shift_service.get_shift(shift_id=shift_id)
    return shifts, HTTPStatus.OK


@router.get("/shifts", tags=["shifts"])
async def get_shifts(
    user_query: UserQuery = Depends(),
    data_query: DateQuery = Depends(),
):
    shift_service = ShiftService()
    LOGGER.debug("user_query: %s", user_query)
    shifts = shift_service.get_shifts(user_query, data_query)
    return shifts, HTTPStatus.OK


@error_handler
@router.post("/shifts/create", tags=["shifts"])
async def create_shift(shift: Shift):
    # TO DO need to re think
    shift_service = ShiftService()
    shifts = shift_service.create_shift(shift)
    return shifts, HTTPStatus.OK


@router.put("/shifts/update", tags=["shifts"])
async def update_shift(shift: Shift):
    shift_service = ShiftService()
    shifts = shift_service.update_shift(shift)
    return shifts, HTTPStatus.OK


@router.patch("/shifts/patch/{shift_id}", tags=["shifts"])
async def patch_shift(shift_id: Optional[str], comments: Optional[str]):
    shift_service = ShiftService()
    shift = shift_service.patch_shift(shift_id=shift_id, comments=comments)
    return (
        shift.model_dump(mode="JSON", exclude_unset=True, exclude_none=True),
        HTTPStatus.OK,
    )


def error_response(
    err: Exception, http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
) -> Response:
    """
    Creates a general server error response from an exception

    :return: HTTP response server error
    """
    response_body = {
        "title": http_status.phrase,
        "detail": f"{repr(err)} with args {err.args}",
        "traceback": {
            "key": "Internal Server Error",
            "type": str(type(err)),
            "full_traceback": traceback.format_exc(),
        },
    }

    return response_body, http_status
