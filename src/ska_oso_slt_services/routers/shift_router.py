"""
Shift Router used for routes the request to appropriate method
"""

import logging
from functools import wraps
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from psycopg import DatabaseError, DataError, InternalError
from pydantic import ValidationError

from ska_oso_slt_services.models.shiftmodels import DateQuery, Shift, UserQuery
from ska_oso_slt_services.services.shift_service import ShiftService


def get_shift_service() -> ShiftService:
    """
    Dependency to get the ShiftService instance
    """
    return ShiftService()


LOGGER = logging.getLogger(__name__)


shift_service_dependency = Depends(get_shift_service)

router = APIRouter(prefix="/shift")


def error_handler(route_function):
    @wraps(route_function)
    async def wrapper(*args, **kwargs):
        try:
            LOGGER.debug("Executing route function: %s", route_function.__name__)
            return await route_function(*args, **kwargs)
        except ValidationError as e:
            LOGGER.exception("Invalid input: %s", str(e))
            raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
        except (DatabaseError, InternalError, DataError) as e:
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
    Retrieve a specific shift by its ID.

    Args:
        shift_id (str): The unique identifier of the shift.

    Raises:
        HTTPException: If the shift is not found.
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
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.
    """

    LOGGER.debug("user_query: %s", user_query)
    shifts = await shift_service.get_shifts(user_query, data_query)
    return shifts, HTTPStatus.OK


@router.post("/shifts/create", tags=["shifts"])
@error_handler
async def create_shift(
    shift: Shift, shift_service: ShiftService = shift_service_dependency
):
    """
    Create a new shift.

    Args:
        shift (ShiftCreate): The shift data to create.

    Returns:
        Shift: The created shift.
    """
    shifts = await shift_service.create_shift(shift)
    return shifts, HTTPStatus.CREATED


@router.put("/shifts/update", tags=["shifts"])
@error_handler
async def update_shift(
    shift: Shift, shift_service: ShiftService = shift_service_dependency
):
    """
    Update an existing shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (ShiftUpdate): The updated shift data.

    Raises:
        HTTPException: If the shift is not found.
    """
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
    """
    Partially update an existing shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (ShiftUpdate): The partial shift data to update.

    Raises:
        HTTPException: If the shift is not found.
    """
    shift = await shift_service.patch_shift(
        shift_id=shift_id, column_name=column_name, column_value=column_value
    )
    return shift, HTTPStatus.OK
