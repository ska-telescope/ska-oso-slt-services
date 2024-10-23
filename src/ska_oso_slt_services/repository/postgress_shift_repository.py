import logging
from typing import Any, List, Optional, Tuple

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.data_access.postgres.mapping import ShiftLogMapping
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    insert_query,
    select_by_date_query,
    select_by_shift_params,
    select_by_text_query,
    select_last_serial_id,
    select_latest_query,
    select_logs_by_status,
    select_metadata_query,
    update_query,
)
from ska_oso_slt_services.domain.shift_models import (
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
)
from ska_oso_slt_services.repository.shift_repository import CRUDShiftRepository
from ska_oso_slt_services.utils.date_utils import get_datetime_for_timezone
from ska_oso_slt_services.utils.s3_bucket import (
    get_file_object_from_s3,
    upload_file_object_to_s3,
)

LOGGER = logging.getLogger(__name__)


class PostgresShiftRepository(CRUDShiftRepository):
    """
    Postgres implementation of the CRUDShiftRepository.

    This class provides concrete implementations for the abstract methods defined in
    the CRUDShiftRepository base class.
    """

    def __init__(self) -> None:
        """
        Initialize the ShiftService.
        Sets up the PostgresDataAccess and ShiftLogMapping instances.
        """

        self.postgres_data_access = PostgresDataAccess()
        self.table_details = ShiftLogMapping()

    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        entity_status: Optional[SbiEntityStatus] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts based on the provided query parameters.

        Args:
            shift (Optional[Shift]): The shift object containing query parameters.
            match_type (Optional[MatchType]): The match type for text-based queries.
            entity_status (Optional[SbiEntityStatus]): Search shift data based on
            SBI status present in shift logs.

        Returns:
            List[Shift]: A list of shifts matching the query or raises shift
            not found error.

        Raises:
            NotFoundError: If no query get matched.
        """
        if shift.shift_start and shift.shift_end:
            query, params = select_by_date_query(self.table_details, shift)
        elif shift.comments and match_type.dict()["match_type"]:
            query, params = select_by_text_query(
                self.table_details, shift.comments, match_type
            )
        elif entity_status.sbi_status:
            query, params = select_logs_by_status(
                self.table_details, entity_status, "sbi_status"
            )
        elif (shift.shift_id or shift.shift_operator) and match_type.dict()[
            "match_type"
        ]:
            query, params = select_by_shift_params(
                self.table_details, shift, match_type
            )
        else:
            raise NotFoundError("Shift not found please pass parameters correctly")
        shifts = self.postgres_data_access.get(query, params)
        return shifts

    def get_shift(self, shift_id) -> Shift:
        """
        Retrieve a specific shift by its ID.

        Args:
            shift_id (str): The unique identifier of the shift.

        Returns:
            Shift: The Shift object if found.

        Raises:
            NotFoundError: If no shift is found with the given ID.
            Exception: For any other unexpected errors.
        """
        query, params = select_latest_query(self.table_details, shift_id=shift_id)
        shift = self.postgres_data_access.get_one(query, params)
        return shift

    def create_shift(self, shift: Shift) -> Shift:
        """
        Create a new shift with updated metadata, start time, and unique ID.

        Args:
            shift (Shift): The shift object to be created.

        Returns:
            Shift: The newly created shift with updated attributes.
        """
        shift = self._prepare_new_shift(shift)
        self._insert_shift_to_database(shift)
        return shift

    def _prepare_new_shift(self, shift: Shift) -> Shift:
        """
        Prepare a new shift by setting metadata, start time, and unique ID.

        Args:
            shift (Shift): The shift object to be prepared.

        Returns:
            Shift: The prepared shift object.
        """
        query, params = select_last_serial_id(self.table_details)
        last_serial_id = self.postgres_data_access.get_one(query, params)
        if last_serial_id and "max" in last_serial_id and last_serial_id["max"]:
            serial_id = last_serial_id.get("max") + 1
        else:
            serial_id = 1
        shift.shift_start = get_datetime_for_timezone("UTC")
        shift.shift_id = f"shift-{shift.shift_start.strftime('%Y%m%d')}-{serial_id}"
        return shift

    def _insert_shift_to_database(self, shift: Shift) -> None:
        """
        Insert the shift into the database.

        Args:
            shift (Shift): The shift object to be inserted.
        """
        query, params = self._build_insert_query(shift)
        self.postgres_data_access.insert(query, params)

    def _build_insert_query(self, shift: Shift) -> Tuple[str, Any]:
        """
        Build the insert query and parameters for the given shift.

        Args:
            shift (Shift): The shift object to build the query for.

        Returns:
            Tuple[str, Any]: A tuple containing the query string and its parameters.
        """
        return insert_query(table_details=self.table_details, shift=shift)

    def update_shift(self, shift: Shift) -> Shift:
        """
        Update an existing shift.

        Args:
            shift (Shift): The shift object with updated information.

        Returns:
            Shift: The updated shift object.

        Raises:
            ValueError: If there's an error in updating the shift.
        """
        existing_shift = Shift.model_validate(self.get_shift(shift.shift_id))
        if not existing_shift:
            raise NotFoundError(f"No shift found with ID: {existing_shift.shift_id}")
        if shift.shift_end:
            existing_shift.shift_end = shift.shift_end
        if shift.comments:
            existing_shift.comments = shift.comments
        if shift.annotations:
            existing_shift.annotations = shift.annotations
        if shift.media:
            existing_shift.media = shift.media
        existing_shift.metadata = shift.metadata
        self._update_shift_in_database(existing_shift)
        return existing_shift

    def get_latest_metadata(self, shift_id: str) -> Optional[Metadata]:
        """Get latest metadata for update."""

        query, params = select_metadata_query(
            table_details=self.table_details,
            shift_id=shift_id,
        )
        meta_data = self.postgres_data_access.get_one(query, params)
        if not meta_data:
            raise NotFoundError(f"No shift found with ID: {shift_id}")
        return Metadata.model_validate(meta_data)

    def _update_shift_in_database(self, shift: Shift) -> None:
        """
        Update the shift in the database.

        Args:
            shift (Shift): The shift object to update.
        """
        query, params = update_query(self.table_details, shift)
        self.postgres_data_access.update(query, params)

    def get_media(self, shift_id: int) -> Media:
        """
        Get a media file from a shift.

        Args:
            shift_id (str): The ID of the shift to get the media from.

        Returns:
            file: The requested media file.
        """
        shift = Shift.model_validate(self.get_shift(shift_id))
        if not shift:
            raise NotFoundError(f"No shift found with ID: {shift_id}")
        if not shift.media:
            raise NotFoundError(f"No media found for shift with ID: {shift_id}")
        files = []
        for media in shift.media:
            file_key, base64_content, content_type = get_file_object_from_s3(
                file_key=media.unique_id
            )
            files.append(
                {
                    "file_key": file_key,
                    "media_content": base64_content,
                    "content_type": content_type,
                }
            )
        return files

    def add_media(self, files, shift: Shift) -> Media:
        """
        Add a media file to a shift.

        Args:
            shift_id (str): The ID of the shift to add the media to.
            files (files): The media file to add.

        Returns:
            Shift: The updated shift with the added media.
        """
        media_list = []
        for file in files:
            file_path, file_unique_id, file_extension = upload_file_object_to_s3(file)
            media = Media(
                path=file_path, unique_id=file_unique_id, file_extension=file_extension
            )
            media_list.append(media)
        if shift.media:
            shift.media += media_list
        else:
            shift.media = media_list
        self.update_shift(shift)
        return shift

    def delete_shift(self, shift_id: str):
        pass
