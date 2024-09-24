"""
Shift Router used for routes the request to appropriate method
"""

import logging
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends

from ska_oso_slt_services.domain.shift_models import DateQuery, Shift, UserQuery
from ska_oso_slt_services.repository.postgress_shift_repository import (
    PostgressShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)


def get_shift_service() -> ShiftService:
    """
    Dependency to get the ShiftService instance
    """
    return ShiftService([PostgressShiftRepository])


shift_service_dependency = Depends(get_shift_service)

router = APIRouter(prefix="/shift")


@router.get("/shift", tags=["shifts"], summary="Get a shift")
def get_shift(
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
    shifts = shift_service.get_shift(shift_id=shift_id)
    return shifts, HTTPStatus.OK


@router.get(
    "/shifts",
    tags=["shifts"],
    summary="Retrieve shift data based on user and date query",
)
def get_shifts(
    user_query: UserQuery = Depends(),
    data_query: DateQuery = Depends(),
    shift_service: ShiftService = shift_service_dependency,
):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.
    """

    LOGGER.debug("user_query: %s", user_query)
    shifts = shift_service.get_shifts(user_query, data_query)
    return shifts, HTTPStatus.OK


@router.post("/shifts/create", tags=["shifts"], summary="Create a new shift")
def create_shift(shift: Shift, shift_service: ShiftService = shift_service_dependency):
    """
    Create a new shift.

    Args:
        shift (ShiftCreate): The shift data to create.

    Returns:
        Shift: The created shift.
    """
    shifts = shift_service.create_shift(shift)
    return shifts, HTTPStatus.CREATED


@router.put("/shifts/update", tags=["shifts"], summary="Update an existing shift")
def update_shift(shift: Shift, shift_service: ShiftService = shift_service_dependency):
    """
    Update an existing shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (ShiftUpdate): The updated shift data.

    Raises:
        HTTPException: If the shift is not found.
    """
    shifts = shift_service.update_shift(shift)
    return shifts, HTTPStatus.OK


@router.patch(
    "/shifts/patch/{shift_id}",
    tags=["shifts"],
    summary="Partially update an existing shift",
)
def patch_shift(
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
    shift = shift_service.patch_shift(
        shift_id=shift_id, column_name=column_name, column_value=column_value
    )
    return shift, HTTPStatus.OK
