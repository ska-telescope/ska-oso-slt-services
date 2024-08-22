import logging
import threading
import time
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from deepdiff import DeepDiff
from flask import request
from pydantic import ValidationError
from ska_db_oda.rest.api.resources import error_response
from ska_db_oda.unit_of_work.postgresunitofwork import PostgresUnitOfWork
from werkzeug.datastructures import FileStorage

from ska_oso_slt_services.common.file_upload import (
    read_image_from_folder,
    upload_image_to_folder,
)
from ska_oso_slt_services.data_access.config import ODA_DATA_POLLING_TIME
from ska_oso_slt_services.data_access.postgres_data_acess import PostgresConnection
from ska_oso_slt_services.models.data_models import Shift, ShiftLogs
from ska_oso_slt_services.repositories.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

LOGGER = logging.getLogger(__name__)
Response = Tuple[Union[dict, list], int]

shift_repository = PostgresShiftRepository()
shift_service = ShiftService(
    crud_shift_repository=shift_repository, shift_repositories=None
)
uow = PostgresUnitOfWork(PostgresConnection().get_connection())


def _extract_eb_id_from_key(key: str) -> str:
    """
    Extract the EB SID from a given key string.

    :param key str: The key string from which to extract the EB SID.
    :returns: The extracted EB SID.
    """
    try:

        eb_id = key.split("[")[1].split("]")[0].strip("'")
        return eb_id
    except IndexError:
        raise ValueError(f"Unexpected key format: {key}")


def updated_shift_log_info(current_shift_id: int):
    """
    Update the shift log information based on new information from external data
     sources.

    :param current_shift_id int: The unique identifier of the current shift.
    :returns: The updated Shift object in JSON format and an HTTP status code.
    """
    # import pdb
    # pdb.set_trace()

    shift_logs_info = {}

    current_shift_data = shift_service.get_shift(sid=current_shift_id)
    if current_shift_data.shift_logs:
        for x in current_shift_data.shift_logs:
            if x.info["eb_id"] not in shift_logs_info:
                shift_logs_info[x.info["eb_id"]] = x.info
                shift_logs_info[x.info["eb_id"]]["log_time"] = x.log_time
            else:

                if shift_logs_info[x.info["eb_id"]]["log_time"] < x.log_time:
                    shift_logs_info[x.info["eb_id"]] = x.info

        for k in shift_logs_info:
            del shift_logs_info[k]["log_time"]

    created_after_eb_sbi_info = shift_repository.get_oda_data(
        filter_date=current_shift_data.shift_start.isoformat()
    )

    if created_after_eb_sbi_info:
        diff = DeepDiff(shift_logs_info, created_after_eb_sbi_info, ignore_order=True)
        new_eb_ids = set(
            _extract_eb_id_from_key(key)
            for key in diff.get("dictionary_item_added", [])
        )

        changed_eb_ids = set([
            _extract_eb_id_from_key(key)
            for key in diff.get("values_changed", {}).keys()
        ])

        new_eb_ids_merged_set = set()
        new_eb_ids_merged_set.update(new_eb_ids)
        new_eb_ids_merged_set.update(changed_eb_ids)

        new_eb_ids_merged = list(new_eb_ids_merged_set)

        LOGGER.info(f"------>New or Modified EB found in ODA {new_eb_ids_merged}")
        if new_eb_ids_merged:
            new_shift_logs = []
            for new_or_updated_eb_id in new_eb_ids_merged:
                new_info = created_after_eb_sbi_info[new_or_updated_eb_id]
                new_shift_log = ShiftLogs(
                    info=new_info, log_time=datetime.now(), source="ODA"
                )
                new_shift_logs.append(new_shift_log)

            if current_shift_data.shift_logs:
                new_shift_logs.extend(current_shift_data.shift_logs)

            updated_shift = Shift(sid=current_shift_id, shift_logs=new_shift_logs)

            updated_shift_with_info = shift_service.update_shift(shift=updated_shift)
            LOGGER.info("------> Shift Logs have been updated successfully")
            LOGGER.info(updated_shift_with_info)
            return (
                updated_shift_with_info.model_dump(
                    mode="JSON", exclude_unset=True, exclude_none=True
                ),
                HTTPStatus.CREATED,
            )
        else:
            LOGGER.info("------> NO New Logs found in ODA")
            return "", HTTPStatus.NO_CONTENT
    else:
        LOGGER.info("------> NO New Logs found in ODA")
        return "", HTTPStatus.NO_CONTENT


class ShiftLogUpdater:
    def __init__(self):
        self.current_shift_id: Optional[int] = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._background_task, daemon=True)
        self.thread_started = False

    def _background_task(self):
        while True:
            with self.lock:
                if self.current_shift_id is not None:
                    LOGGER.info(
                        "------> Checking Updated ODA LOGS for SHIFT ID"
                        f" {self.current_shift_id}"
                    )
                    updated_shift_log_info(self.current_shift_id)
            time.sleep(
                ODA_DATA_POLLING_TIME
            )  # Wait for 10 seconds before running again

    def start(self):
        if not self.thread_started:
            LOGGER.info("\n\n ---> Polling Started")
            self.thread.start()
            self.thread_started = True

    def update_shift_id(self, shift_id: int):
        with self.lock:
            self.current_shift_id = shift_id
            self.start()


shift_log_updater = ShiftLogUpdater()


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

        except Exception as e:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper


@error_handler
def get_shifts(shift_start: Optional[str] = None, shift_end: Optional[str] = None):
    """
    Retrieve a list of shifts filtered by the specified start and end times.

    :param shift_start Optional[str]: The start time to filter shifts in ISO format.
     If None, no start time filter is applied.
    :param shift_end Optional[str]: The end time to filter shifts in ISO format. If
    None, no end time filter is applied.
    :returns: A list of Shift objects in JSON format and an HTTP status code.
    """

    shift_start = datetime.fromisoformat(shift_start) if shift_start else None
    shift_end = datetime.fromisoformat(shift_end) if shift_end else None

    shifts = shift_service.getShifts(shift_start, shift_end)
    return [
        shift.model_dump(mode="JSON", exclude_unset=True, exclude_none=True)
        for shift in shifts
    ], HTTPStatus.OK


@error_handler
def get_shift(shift_id):
    """
    Retrieve a single shift by its unique identifier.

    :param shift_id int: The unique identifier of the shift.
    :returns: The Shift object in JSON format and an HTTP status code.
    """
    shift = shift_service.get_shift(sid=shift_id)
    if shift is None:
        return {"error": "Shift not found"}, 404
    else:
        return (
            shift.model_dump(mode="json", exclude_unset=True, exclude_none=True),
            HTTPStatus.OK,
        )


@error_handler
def create_shift(body: Dict[str, Any]):
    """
    Create a new shift.

    :param body Dict[str, Any]: The JSON payload containing the shift details.
    :returns: The created Shift object in JSON format and an HTTP status code.
    """
    try:
        shift = Shift(**body)
    except ValidationError as e:
        return {"errors": e.errors()}, HTTPStatus.BAD_REQUEST

    created_shift = shift_service.create_shift(shift)
    shift_id = (
        f"shift-{created_shift.shift_start.strftime('%Y%m%d')}-{created_shift.sid}"
    )
    shift_service.update_shift(shift=Shift(shift_id=shift_id, sid=created_shift.sid))
    shift_log_updater.update_shift_id(created_shift.sid)
    # shift_service.get_shift(sid=created_shift.sid)
    return (
        shift_service.get_shift(sid=created_shift.sid).model_dump(
            mode="JSON", exclude_unset=True, exclude_none=True
        ),
        HTTPStatus.CREATED,
    )


@error_handler
def update_shift(shift_id, body):
    """
    Update an existing shift.

    :param shift_id int: The unique identifier of the shift to be updated.
    :param body Dict[str, Any]: The JSON payload containing the updated shift details.
    :returns: The updated Shift object in JSON format and an HTTP status code.
    """

    body["sid"] = shift_id
    try:

        shift = Shift(**body)
    except ValidationError as e:
        return {"errors": e.errors()}, HTTPStatus.BAD_REQUEST

    updated_shift = shift_service.update_shift(shift)
    return (
        updated_shift.model_dump(mode="JSON", exclude_unset=True, exclude_none=True),
        HTTPStatus.CREATED,
    )


@error_handler
def upload_image(**kwargs):
    """
    Upload an image to a specific folder.

    :param image_data: The image data to be uploaded.
    :returns: A success message and an HTTP status code.
    """
    try:
        # Get the uploaded file
        shift_id: str = kwargs.get("shift_id", "")
        if not shift_id:
            # Handle the case when shift_id is not provided
            raise ValueError("shift_id is required")

        files: List[FileStorage] = request.files.getlist("files")
        if not files:
            # Handle the case when no files are provided
            raise ValueError("No files provided")
        file_path_to_store: List[str] = []
        for file in files:
            _, path = upload_image_to_folder(media_content=file, file_id=shift_id)
            file_path_to_store.append({"type": "img", "path": path})
        shift_service.add_media(shift_id=shift_id, media=file_path_to_store)
        return "Images uploaded successfully"

    except Exception as e:
        print(e)
        return "Error uploading image!", 500


@error_handler
def get_shift_media(shift_id: str):
    """
    Retrieve the media associated with a specific shift.

    :param shift_id str: The unique identifier of the shift.
    :returns: A list of media URLs and an HTTP status code.
    """
    shift_data = shift_service.get_media(shift_id=shift_id)
    media_data = []
    for media in shift_data:
        data = read_image_from_folder(media["path"])
        media_data.append(data)
    if media_data:
        return media_data, HTTPStatus.OK
    else:
        return {"error": "Shift not found"}, HTTPStatus.NOT_FOUND


@error_handler
def get_current_shift():
    """
    Retrieve a single shift by its unique identifier.

    :param shift_id int: The unique identifier of the shift.
    :returns: The Shift object in JSON format and an HTTP status code.
    """
    shift = shift_service.get_current_shift()
    if shift is None:
        return {"error": "Shift not found"}, 404
    else:
        return (
            shift.model_dump(mode="json", exclude_unset=True, exclude_none=True),
            HTTPStatus.OK,
        )
