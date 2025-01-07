"""
Shift Router used for routes the request to appropriate method
"""

import json
import logging
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, UploadFile

from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftBaseClass,
    ShiftComment,
    ShiftLogComment,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)

# Get the directory of the current script
current_dir = Path(__file__).parent


class ShiftServiceSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ShiftService()
        return cls._instance


@lru_cache()
def get_shift_service() -> ShiftService:
    """
    Dependency to get the ShiftService instance
    """
    return ShiftServiceSingleton.get_instance()


shift_service = get_shift_service()

router = APIRouter()


@router.get(
    "/shift",
    tags=["Shifts"],
    summary="Get a shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
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
    tags=["Shifts"],
    summary="Retrieve shift data based on shift attributes like shift_id,"
    "match type and entity status",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/multiple_shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {
                    "example": {
                        "type": "datetime_from_date_parsing",
                        "loc": ["query", "shift_start"],
                        "msg": "Input should be a valid datetime or date",
                        "input": "test",
                        "ctx": {"error": "input is too short"},
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_shifts(
    shift: ShiftBaseClass = Depends(),
    match_type: MatchType = Depends(),
    status: SbiEntityStatus = Depends(),
    entities: EntityFilter = Depends(),
):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.
    """
    shifts = shift_service.get_shifts(shift, match_type, status, entities)
    return shifts, HTTPStatus.OK


@router.post(
    "/shifts/create",
    tags=["Shifts"],
    summary="Create a new shift",
    responses={
        201: {
            "description": "Shift Created Successfully",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {
                    "example": {
                        "type": "datetime_from_date_parsing",
                        "loc": ["query", "shift_start"],
                        "msg": "Input should be a valid datetime or date",
                        "input": "test",
                        "ctx": {"error": "input is too short"},
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_shift(shift: Shift):
    """
    Create a new shift.

    Args:
        shift (ShiftCreate): The shift data to create.

    Returns:
        Shift: The created shift.
    """
    shifts = shift_service.create_shift(shift)
    # shift_log_updater.update_shift_id(shifts.shift_id)

    return shifts, HTTPStatus.CREATED


@router.put(
    "/shifts/update/{shift_id}",
    tags=["Shifts"],
    summary="Update an existing shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
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
    "/shift/end/{shift_id}",
    tags=["shifts"],
    summary="Update an existing shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def update_shift_end_time(shift_id: str, shift: Shift):
    """
    Update an existing shift end time.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift (Shift): The updated shift data.

    Raises:
        HTTPException: If the shift is not found.
    """
    shifts = shift_service.update_shift_end_time(shift_id, shift)
    return shifts, HTTPStatus.OK


@router.post(
    "/shift_log_comments",
    tags=["Shift Log Comments"],
    summary="Create a new shift log comment",
    responses={
        201: {
            "description": "Shift Log Comments Created Successfully",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_log_comments.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {
                    "example": {
                        "type": "datetime_from_date_parsing",
                        "loc": ["query", "shift_start"],
                        "msg": "Input should be a valid datetime or date",
                        "input": "test",
                        "ctx": {"error": "input is too short"},
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_shift_log_comments(shift_log_comment: ShiftLogComment):
    """
    Create a new shift.

    Args:
        shift (ShiftCreate): The shift data to create.

    Returns:
        ShiftLogComment: The created shift log comment.
    """
    shift_log_comment_obj = shift_service.create_shift_logs_comment(shift_log_comment)
    return shift_log_comment_obj, HTTPStatus.CREATED


@router.get(
    "/shift_log_comments",
    tags=["Shift Log Comments"],
    summary="Retrieve shift log comments based on shift ID and EB ID",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_log_comments.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_shift_log_comments(shift_id: Optional[str] = None, eb_id: Optional[str] = None):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.

    Args:
        shift_id(optional): Shift ID
        eb_id(optional): EB ID

    Returns:
        ShiftLogComment: Shift Log Comments match found
    """
    shift_log_comments = shift_service.get_shift_logs_comments(shift_id, eb_id)
    return shift_log_comments, HTTPStatus.OK


@router.put(
    "/shift_log_comments/{comment_id}",
    tags=["Shift Log Comments"],
    summary="Update an existing shift log comments",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_log_comments.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Invalid Comment ID",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def update_shift_log_comments(comment_id: str, shift_log_comment: ShiftLogComment):
    """
    Update an existing shift log comment.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift_log_comment (ShiftLogComment): The updated shift log comment  data.

    Raises:
        HTTPException: If the shift is not found.
    """

    shift_log_comments = shift_service.update_shift_log_comments(
        comment_id=comment_id, shift_log_comment=shift_log_comment
    )
    return shift_log_comments, HTTPStatus.OK


@router.put(
    "/shift_log_comments/upload_image/{comment_id}",
    tags=["Shift Log Comments"],
    summary="Upload image for Shift log comment",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "path": "test_path",
                            "unique_id": "test_unique_id",
                            "timestamp": "2024-11-11T15:46:13.223618Z",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Comment ID Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def update_shift_log_with_image(comment_id: int, files: list[UploadFile] = File(...)):
    """
    Uploads FIle to s3 and updates the relevant Shift Log comment image with the URL

    Args:
        comment_id: Comment ID
        file(s): File(s) to be uploaded

    Returns:
         shift_log_comment (ShiftLogComment): The updated shift log comment  data.
    """

    media = shift_service.update_shift_log_with_image(
        comment_id=comment_id, files=files, shift_model=ShiftLogComment
    )
    return media, HTTPStatus.OK


@router.get(
    "/current_shift",
    tags=["Shifts"],
    summary="Get Current Shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/multiple_shift_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Shift Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {
                    "example": {
                        "type": "datetime_from_date_parsing",
                        "loc": ["query", "shift_start"],
                        "msg": "Input should be a valid datetime or date",
                        "input": "test",
                        "ctx": {"error": "input is too short"},
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_current_shift():
    """
    Retrieve the current active shift.

    This endpoint returns the most recent shift based on the last modified or
    created time.
    It does not require any input parameters and is used to retrieve the latest shift
    that is currently active in the system.

    Returns:
        Shift: The latest shift object in the system.
        HTTPStatus: HTTP 200 OK on success.

    Raises:
        HTTPException: If there is an issue retrieving the current shift
         or if no shift is found.
    """
    shift = shift_service.get_current_shift()
    return shift, HTTPStatus.OK


@router.patch(
    "/shifts/patch/update_shift_log_info/{shift_id}",
    tags=["Shifts"],
    summary="Update Shift Log info",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/oda_log_info.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
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


@router.post(
    "/shift_comment",
    tags=["Shift Comments"],
    summary="Create a new shift comment",
    responses={
        201: {
            "description": "Shift Comments Created Successfully",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_comment.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_shift_comments(shift_comment: ShiftComment):
    """
    Create a new shift.

    Args:
        shift_comment (ShiftComment): The shift comment to create.

    Returns:
        ShiftComment: The created shift comment.
    """
    shift_comment_obj = shift_service.create_shift_comment(shift_comment)
    return shift_comment_obj, HTTPStatus.CREATED


@router.get(
    "/shift_comment",
    tags=["Shift Comments"],
    summary="Retrieve shift comments based on shift ID and EB ID,",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_comment.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No shifts log comments found for the given query."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_shift_comments(shift_id: Optional[str] = None):
    """
    Retrieve all shifts.
    This endpoint returns a list of all shifts in the system.

    Args:
        shift_id(optional): Shift ID

    Returns:
        ShiftComment: Shift Comments match found
    """
    shift_comments = shift_service.get_shift_comments(shift_id)
    return shift_comments, HTTPStatus.OK


@router.put(
    "/shift_comment/{comment_id}",
    tags=["Shift Comments"],
    summary="Update an existing shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_comment.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Comment ID",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def update_shift_comment(comment_id: str, shift_comment: ShiftComment):
    """
    Update an existing shift comment.

    Args:
        comment_id (str): The unique identifier of the shift to update.
        shift_comment (ShiftComment): The updated shift comment data.

    Raises:
        HTTPException: If the shift is not found.
    """

    shift_comments = shift_service.update_shift_comment(
        comment_id=comment_id, shift_comment=shift_comment
    )
    return shift_comments, HTTPStatus.OK


@router.post(
    "/shift_log_comments/upload_image",
    tags=["Shift Log Comments"],
    summary="Upload image for shift",
    responses={
        201: {
            "description": "Image Uploaded Successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "path": "test_path",
                            "unique_id": "test_unique_id",
                            "timestamp": "2024-11-11T15:46:13.223618Z",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_shift_log_media(
    shift_id: str, shift_operator: str, eb_id: str, file: UploadFile = File(...)
):
    """
    Upload one or more image files for a specific shift.

    This endpoint allows uploading multiple image files associated
    with a particular shift identified by the shift_id.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift_operator (str): The shift operator name.
        eb_id (str): The EB ID associated with the shift.
        files (list[UploadFile]): A list of files to be uploaded.

    Returns:
        list: A list containing elements:
            - image_response: The media (image) data associated with the comment.
            - HTTPStatus.OK: HTTP 200 status code indicating successful retrieval.
    """
    media = shift_service.create_shift_log_media(
        shift_id=shift_id,
        shift_operator=shift_operator,
        file=file,
        shift_model=ShiftLogComment,
        eb_id=eb_id,
    )
    return media, HTTPStatus.OK


@router.get(
    "/shift_log_comments/download_images/{comment_id}",
    tags=["Shift Log Comments"],
    summary="download shift image",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "file_key": "test.jpeg",
                            "media_content": "test_media_content",
                            "content_type": "image/jpeg",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Comment ID Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_shift_log_media(comment_id: Optional[int]):
    """Retrieve media associated with a shift comment.

    Args:
        comment_id (Optional[int]): The unique identifier of the comment.
            If None, returns all media.

    Returns:
        tuple: A tuple containing:
            - image_response: The media data from the shift service
            - HTTPStatus.OK: HTTP 200 status code indicating successful retrieval
    """

    image_response = shift_service.get_shift_log_media(comment_id)
    return image_response, HTTPStatus.OK


@router.post(
    "/shift_comment/upload_image",
    tags=["Shift Comments"],
    summary="Upload image for shift",
    responses={
        201: {
            "description": "Image Uploaded Successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "path": "test_path",
                            "unique_id": "test_unique_id",
                            "timestamp": "2024-11-11T15:46:13.223618Z",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_media_for_comment(
    shift_id: str, shift_operator: str, file: UploadFile = File(...)
):
    """
    Create a new shift.

    Args:
        shift_id (str): The unique identifier of the shift to update.
        shift_operator (str): The shift operator name.
        file (list[UploadFile]): A list of files to be uploaded.

    Returns:
        ShiftLogComment: The created shift log comment.
    """
    media = shift_service.create_media_for_comment(
        shift_id=shift_id,
        shift_operator=shift_operator,
        file=file,
        shift_model=ShiftComment,
    )
    return media, HTTPStatus.OK


@router.put(
    "/shift_comment/upload_image/{comment_id}",
    tags=["Shift Comments"],
    summary="Upload image for shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "path": "test_path",
                            "unique_id": "test_unique_id",
                            "timestamp": "2024-11-11T15:46:13.223618Z",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Comment ID Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def add_media_to_comment(
    comment_id: Optional[str], files: list[UploadFile] = File(...)
):
    """
    Upload one or more image files for a specific shift.

    This endpoint allows uploading multiple image files associated
    with a particular shift identified by the shift_id.

    Args:
        comment_id (Optional[int]): The unique identifier of the
            comment to which the images will be associated.
        files (list[UploadFile]): A list of files to be uploaded.
            Each file should be an image. This parameter uses
            FastAPI's File(...) for handling file uploads.

    Returns:
        list: A list containing elements:
            - image_response: The media (image) data associated with the comment.
            - HTTPStatus.OK: HTTP 200 status code indicating successful retrieval.
    """
    media = shift_service.add_media_to_comment(
        comment_id, files, shift_model=ShiftComment
    )
    return media, HTTPStatus.OK


@router.get(
    "/shift_comment/download_images/{comment_id}",
    tags=["Shift Comments"],
    summary="download shift image",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "file_key": "test.jpeg",
                            "media_content": "test_media_content",
                            "content_type": "image/jpeg",
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Comment ID Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Comment Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_media_for_comment(comment_id: Optional[int]):
    """Retrieve media associated with a shift comment.

    Args:
        comment_id (Optional[int]): The unique identifier of the comment.
            If None, returns all media.

    Returns:
        tuple: A tuple containing:
            - image_response: The media data from the shift service
            - HTTPStatus.OK: HTTP 200 status code indicating successful retrieval
    """

    image_response = shift_service.get_media_for_comment(
        comment_id, shift_model=ShiftComment
    )
    return image_response, HTTPStatus.OK


@router.post(
    "/shift_annotation",
    tags=["Shift Annotations"],
    summary="Create a new shift annotation",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_annotation.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def create_shift_annotation(shift_annotation: ShiftAnnotation):
    """
    Create a new annotation.

    Args:
        shift_annotation (ShiftAnnotation): The shift annotation to create.

    Returns:
        ShiftAnnotation: The created shift annotation.
    """
    shift_annotation_obj = shift_service.create_shift_annotation(shift_annotation)
    return shift_annotation_obj, HTTPStatus.CREATED


@router.get(
    "/shift_annotation",
    tags=["Shift Annotations"],
    summary="Get Shift annotation",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_annotation.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Shift Id",
            "content": {
                "application/json": {
                    "example": {
                        "message": "No shifts annotation found for the given query."
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_shift_annotation(shift_id: str):
    """
    Get Annotation based on shift_id.

    Args:
        shift_id (str): The shift id to get.

    Returns:
        ShiftAnnotation: The shift annotation.
    """
    shift_annotations_obj = shift_service.get_shift_annotations(shift_id)
    return shift_annotations_obj, HTTPStatus.OK


@router.put(
    "/shift_annotation/{annotation_id}",
    tags=["Shift Annotations"],
    summary="Update an existing shift",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_annotation.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Invalid Annotation ID",
            "content": {
                "application/json": {"example": {"message": "Invalid Annotation Id"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Shift Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def update_shift_annotations(annotation_id: str, shift_annotation: ShiftAnnotation):
    """
    Update an existing shift annotation.

    Args:
        annotation_id (str): The unique identifier of the shift to update.
        shift_annotation (ShiftAnnotation): The updated shift annotation data.

    Raises:
        HTTPException: If the shift is not found.
    """

    shift_annotations = shift_service.update_shift_annotations(
        annotation_id=annotation_id, shift_annotation=shift_annotation
    )
    return shift_annotations, HTTPStatus.OK
