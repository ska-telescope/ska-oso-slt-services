"""
Shift Router used for routes the request to appropriate method
"""

import logging
from functools import lru_cache
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends

from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    JsonQuery,
    Shift,
    TextQuery,
    UserQuery,
)
from ska_oso_slt_services.repository.postgress_shift_repository import (
    PostgressShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)


class ShiftServiceSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ShiftService([PostgressShiftRepository])
        return cls._instance


@lru_cache()
def get_shift_service() -> ShiftService:
    """
    Dependency to get the ShiftService instance
    """
    return ShiftServiceSingleton.get_instance()


shift_service = get_shift_service()


router = APIRouter(prefix="/shift")


@router.get("/shift", tags=["shifts"], summary="Get a shift")
def get_shift(shift_id: Optional[str] = None):
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
    text_query: TextQuery = Depends(),
    json_query: JsonQuery = Depends(),
):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.
    """

    LOGGER.debug("user_query: %s", user_query)
    shifts = shift_service.get_shifts(user_query, data_query, text_query, json_query)
    return shifts, HTTPStatus.OK


@router.post("/shifts/create", tags=["shifts"], summary="Create a new shift")
def create_shift(shift: Shift):
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
def update_shift(shift: Shift):
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
    shift_id: Optional[str], column_name: Optional[str], column_value: Optional[str]
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


@router.patch(
    "/shifts/patch/update_shift_log_info/{shift_id}",
    tags=["shifts"],
    summary="Update Shift Log info",
)
def patch_shift_log_info(shift_id: Optional[str]):
    """
    Partially update an existing shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (ShiftUpdate): The partial shift data to update.

    Raises:
        HTTPException: If the shift is not found.
    """
    shift = shift_service.updated_shift_log_info(current_shift_id=shift_id)
    return shift, HTTPStatus.OK
