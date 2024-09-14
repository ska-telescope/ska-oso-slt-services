import logging
import traceback
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Dict, List, Optional, Tuple, Union

from fastapi import APIRouter, Depends, HTTPException, Response

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresConnection
from ska_oso_slt_services.infrastructure.postress.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.models.shiftmodels import DateQuery, Shift, UserQuery
from ska_oso_slt_services.services.shift_service import ShiftService
from ska_oso_slt_services.utils.exception import DatabaseError, InvalidInputError


def get_shift_service() -> ShiftService:
    return ShiftService()


LOGGER = logging.getLogger(__name__)
from pydantic import ValidationError

shift_repository = PostgresShiftRepository
connection_pool = PostgresConnection().get_connection()

shift_service_dependency = Depends(get_shift_service)

router = APIRouter(prefix="/shift")


def error_handler(route_function):
    @wraps(route_function)
    async def wrapper(*args, **kwargs):
        try:
            LOGGER.debug("Executing route function: %s", route_function.__name__)
            return await route_function(*args, **kwargs)
        except InvalidInputError as e:
            LOGGER.exception("Invalid input: %s", str(e))
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
        except ValidationError as e:
            LOGGER.exception("Invalid input: %s", str(e))
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
        except DatabaseError as e:
            LOGGER.exception("Database error: %s", str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Database error occurred",
            )
        except ValueError as e:
            LOGGER.exception("Unexpected error: %s", str(e))
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Wrong value provided"
            )

        except Exception as e:
            LOGGER.exception("Unexpected error: %s", str(e))
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    return wrapper


@router.get("/shift", tags=["shifts"])
@error_handler
async def get_shift(
    shift_id: Optional[str] = None,
    shift_service: ShiftService = shift_service_dependency,
):
    """
    Retrieve a list of shifts filtered by the specified start and end times.

    :param shift_start Optional[str]: The start time to filter shifts in ISO format.
     If None, no start time filter is applied.
    :param shift_end Optional[str]: The end time to filter shifts in ISO format. If
    None, no end time filter is applied.
    :returns: A list of Shift objects in JSON format and an HTTP status code.
    """
    shifts = await shift_service.get_shift(shift_id=shift_id)
    return shifts, HTTPStatus.OK


@router.get("/shifts", tags=["shifts"])
@error_handler
async def get_shifts(
    user_query: UserQuery = Depends(),
    data_query: DateQuery = Depends(),
    shift_service: ShiftService = shift_service_dependency,
):
    LOGGER.debug("user_query: %s", user_query)
    shifts = await shift_service.get_shifts(user_query, data_query)
    return shifts, HTTPStatus.OK


@router.post("/shifts/create", tags=["shifts"])
@error_handler
async def create_shift(
    shift: Shift, shift_service: ShiftService = shift_service_dependency
):
    # TO DO need to re think
    shifts = await shift_service.create_shift(shift)
    return shifts, HTTPStatus.OK


@router.put("/shifts/update", tags=["shifts"])
@error_handler
async def update_shift(
    shift: Shift, shift_service: ShiftService = shift_service_dependency
):
    shifts = await shift_service.update_shift(shift)
    return shifts, HTTPStatus.OK


@router.patch("/shifts/patch/{shift_id}", tags=["shifts"])
@error_handler
async def patch_shift(
    shift_id: Optional[str],
    column_name: Optional[str],
    column_value: Optional[str],
    shift_service: ShiftService = shift_service_dependency,
):
    shift = await shift_service.patch_shift(
        shift_id=shift_id, column_name=column_name, column_value=column_value
    )
    return shift, HTTPStatus.OK
