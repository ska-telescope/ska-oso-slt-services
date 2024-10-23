"""
Shift Router used for routes the request to appropriate method
"""

import logging
from functools import lru_cache
from http import HTTPStatus
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile

from ska_oso_slt_services.domain.shift_models import (
    MatchType,
    SbiEntityStatus,
    Shift,
    ShiftBaseClass,
)
from ska_oso_slt_services.repository.postgress_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)


class ShiftServiceSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ShiftService([PostgresShiftRepository])
        return cls._instance


@lru_cache()
def get_shift_service() -> ShiftService:
    """
    Dependency to get the ShiftService instance
    """
    return ShiftServiceSingleton.get_instance()


shift_service = get_shift_service()


router = APIRouter()


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
    summary="Retrieve shift data based on shift attributes like shift_id,"
    "match type and entity status",
)
def get_shifts(
    shift: ShiftBaseClass = Depends(),
    match_type: MatchType = Depends(),
    status: SbiEntityStatus = Depends(),
):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.
    """
    shifts = shift_service.get_shifts(shift, match_type, status)
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


@router.put(
    "/shifts/update/{shift_id}", tags=["shifts"], summary="Update an existing shift"
)
def update_shift(shift_id: str, shift: Shift):
    """
    Update an existing shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (ShiftUpdate): The updated shift data.

    Raises:
        HTTPException: If the shift is not found.
    """
    shifts = shift_service.update_shift(shift_id, shift)
    return shifts, HTTPStatus.OK


@router.put(
    "/shifts/upload_image/{shift_id}", tags=["shifts"], summary="Upload image for shift"
)
def add_media(shift_id: Optional[str], files: list[UploadFile] = File(...)):
    """
    Upload one or more image files for a specific shift.

    This endpoint allows uploading multiple imagefiles associated
    with a particular shift identified by the shift_id.

    Args:
        shift_id (Optional[str]): The unique identifier of the
            shift to which the images will be associated.
        files (list[UploadFile]): A list of files to be uploaded.
            Each file should be an image. This parameter uses
            FastAPI's File(...) for handling file uploads.

    Returns:
        list: A list containing elements:
            - image_response: The media (image) data associated with the shift.
            - HTTPStatus.OK: HTTP 200 status code indicating successful retrieval.
    """
    media = shift_service.add_media(shift_id, files)
    return media, HTTPStatus.OK


@router.get(
    "/shifts/download_images/{shift_id}",
    tags=["shifts"],
    summary="download shift image",
)
def get_media(shift_id: Optional[str]):
    """
    Retrieve media (image) associated with a specific shift.

    This endpoint allows downloading images related to a particular shift
    identified by the shift_id.

    Args:
        shift_id (Optional[str]): The unique identifier of the shift.
            If provided, it's used to fetch the specific shift's image.
            If None returns empty array.

    Returns:
        list: A list containing elements:
            - image_response: The media (image) data
                associated with the shift.
            - HTTPStatus.OK: HTTP 200 status
                code indicating successful retrieval.
    """
    image_response = shift_service.get_media(shift_id)
    return image_response, HTTPStatus.OK
