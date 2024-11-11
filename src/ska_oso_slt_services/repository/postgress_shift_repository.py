import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from deepdiff import DeepDiff

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.data_access.postgres.mapping import (
    ShiftCommentMapping,
    ShiftLogCommentMapping,
    ShiftLogMapping,
)
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    insert_query,
    select_by_date_query,
    select_by_shift_params,
    select_by_text_query,
    select_comments_query,
    select_last_serial_id,
    select_latest_query,
    select_latest_shift_query,
    select_logs_by_status,
    select_metadata_query,
    shift_logs_patch_query,
    update_query,
)
from ska_oso_slt_services.domain.shift_models import (
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftComment,
    ShiftLogComment,
    ShiftLogImage,
    ShiftLogs,
)
from ska_oso_slt_services.repository.shift_repository import CRUDShiftRepository
from ska_oso_slt_services.utils.date_utils import get_datetime_for_timezone
from ska_oso_slt_services.utils.metadata_mixin import update_metadata
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
        self._insert_shift_to_database(table_details=self.table_details, entity=shift)
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

    def _insert_shift_to_database(self, table_details, entity) -> None:
        """
        Insert the shift into the database.

        Args:
            table_details: The mapping details for the shift table.
            entity : The object to be inserted in DB.

        Returns:
            The ID of the created shift entry.
        """
        query, params = self._build_insert_query(
            table_details=table_details, entity=entity
        )
        id_created = self.postgres_data_access.insert(query, params)
        return id_created

    def _build_insert_query(self, table_details, entity) -> Tuple[str, Any]:
        """
        Build the insert query and parameters for the given shift.

        Args:
            shift (Shift): The shift object to build the query for.

        Returns:
            Tuple[str, Any]: A tuple containing the query string and its parameters.
        """
        return insert_query(table_details=table_details, entity=entity)

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

    def get_latest_metadata(
        self, entity_id: str | int, table_details=ShiftLogMapping()
    ) -> Optional[Metadata]:
        """
        Get the latest metadata for a given  entity.

        Args:
            entity_id (str | int): ID of the  entity to fetch metadata for.
            table_details: Mapping details for the entity table.

        Returns:
            Optional[Metadata]: Metadata for the specified entity if available.

        Raises:
            NotFoundError: If no metadata is found for the entity.
        """

        query, params = select_metadata_query(
            table_details=table_details,
            entity_id=entity_id,
        )
        meta_data = self.postgres_data_access.get_one(query, params)
        if not meta_data:
            raise NotFoundError(f"No entity found with ID: {entity_id}")
        return Metadata.model_validate(meta_data)

    def _update_shift_in_database(
        self, entity, table_details=ShiftLogMapping()
    ) -> None:
        """
        Update an existing entity in the database.

        Args:
            entity: The object to be updated in the database.
            table_details: The mapping details for the entity table.
        """
        query, params = update_query(table_details=table_details, entity=entity)

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

    def get_shift_logs_comments(self, shift_id=None, eb_id=None):
        """
        Retrieve comments from shift logs based on shift ID or EB ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter comments by.
            eb_id (Optional[str]): The EB ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        query, params = select_comments_query(
            table_details=ShiftLogCommentMapping(), shift_id=shift_id, eb_id=eb_id
        )
        comments = self.postgres_data_access.get(query=query, params=params)
        return comments

    def get_shift_logs_comment(self, comment_id):
        """
        Retrieve a single comment from shift logs by comment ID.

        Args:
            comment_id (int): The ID of the comment to retrieve.

        Returns:
            Dict: The comment data associated with the specified ID.
        """
        query, params = select_comments_query(
            table_details=ShiftLogCommentMapping(), id=comment_id
        )
        comments = self.postgres_data_access.get(query=query, params=params)[0]
        return comments

    def create_shift_logs_comment(self, shift_log_comment: ShiftLogComment):
        """
        Create a new comment for a shift log and save it to the database.

        Args:
            shift_log_comment (ShiftLogComment): The comment data to create.

        Returns:
            ShiftLogComment: The newly created shift log comment.
        """
        shift_log_comment_id = self._insert_shift_to_database(
            table_details=ShiftLogCommentMapping(), entity=shift_log_comment
        )
        shift_log_comment.id = shift_log_comment_id["id"]

        return shift_log_comment

    def update_shift_logs_comments(self, shift_log_comment: ShiftLogComment):
        """
        Update an existing shift log comment with new data.

        Args:
            shift_log_comment (ShiftLogComment): The updated comment data.

        Returns:
            ShiftLogComment: The updated shift log comment.
        """
        existing_shift_log_comment = ShiftLogComment.model_validate(
            self.get_shift_logs_comment(comment_id=shift_log_comment.id)
        )
        existing_shift_log_comment.id = shift_log_comment.id
        if shift_log_comment.log_comment:
            existing_shift_log_comment.log_comment = shift_log_comment.log_comment
        if shift_log_comment.eb_id:
            existing_shift_log_comment.eb_id = shift_log_comment.eb_id
        if shift_log_comment.operator_name:
            existing_shift_log_comment.operator_name = shift_log_comment.operator_name

        existing_shift_log_comment.metadata = shift_log_comment.metadata
        self._update_shift_in_database(
            entity=existing_shift_log_comment, table_details=ShiftLogCommentMapping()
        )

        return existing_shift_log_comment

    def update_shift_log_with_image(self, shift_log_comment: ShiftLogComment, file):
        """
        Update a shift log comment with an image, uploading the image to S3.

        Args:
            shift_log_comment (ShiftLogComment): The comment data to update.
            file: The image file to upload.

        Returns:
            ShiftLogComment: The updated shift log comment with the image added.
        """
        file_path, _, _ = upload_file_object_to_s3(file)
        image = ShiftLogImage(path=file_path)
        existing_shift_log_image = ShiftLogComment.model_validate(
            self.get_shift_logs_comment(comment_id=shift_log_comment.id)
        )
        existing_shift_log_image.id = shift_log_comment.id
        existing_shift_log_image.image = image
        existing_shift_log_image.metadata = shift_log_comment.metadata

        self._update_shift_in_database(
            entity=existing_shift_log_image, table_details=ShiftLogCommentMapping()
        )

        return existing_shift_log_image

    def get_current_shift(self):
        """
        Retrieve the most recent shift from the database.

        This method fetches the latest shift from the database by selecting the
        most recent entry, ordered by  `created_on` timestamps.

        Returns:
            Shift: The most recent shift object in the system.


        """
        query, params = select_latest_shift_query(self.table_details)
        shift = self.postgres_data_access.get_one(query, params)
        return shift

    def get_oda_data(self, filter_date):
        filter_date_tz = datetime.fromisoformat(filter_date).replace(
            tzinfo=timezone(timedelta(hours=0, minutes=0))
        )
        eb_query = """
                    SELECT
                        e.eb_id,
                        e.info,
                        e.sbd_id,
                        e.sbi_id,
                        e.sbd_version,
                        e.version,
                        e.created_on,
                        e.created_by,
                        e.last_modified_on,
                        e.last_modified_by,
                        (
                            SELECT current_status
                            FROM tab_oda_eb_status_history
                            WHERE eb_ref = e.eb_id
                            ORDER BY id DESC
                            LIMIT 1
                        ) AS current_status
                    FROM
                        tab_oda_eb e
                    WHERE
                        e.last_modified_on >=%s
                    """
        eb_params = [filter_date_tz]
        eb_rows = self.postgres_data_access.execute_query_or_update(
            query=eb_query, params=tuple(eb_params), query_type="GET"
        )

        info = {}
        if eb_rows:
            for eb in eb_rows:
                request_responses = eb["info"].get("request_responses", [])

                if not request_responses:
                    sbi_current_status = "Created"
                else:
                    ok_count = sum(
                        1
                        for response in request_responses
                        if response["status"] == "OK"
                    )
                    error_count = sum(
                        1
                        for response in request_responses
                        if response["status"] == "ERROR"
                    )

                    if error_count > 0:
                        sbi_current_status = "failed"
                    elif ok_count == 5:  # Assuming the total number of blocks is 5
                        sbi_current_status = "completed"
                    else:
                        sbi_current_status = "executing"

                info[eb["eb_id"]] = eb["info"]
                info[eb["eb_id"]]["sbi_status"] = sbi_current_status
                info[eb["eb_id"]]["eb_status"] = eb["current_status"]
        return info

    def _extract_eb_id_from_key(self, key: str) -> str:
        """
        Extract the EB SID from a given key string.

        :param key str: The key string from which to extract the EB SID.
        :returns: The extracted EB SID.
        """
        try:

            eb_id = key.split("[")[1].split("]")[0].strip("'")
            return eb_id
        except IndexError as e:
            raise ValueError(  # 1pylint: disable=raise-missing-from
                f"Unexpected key format: {key}"
            ) from e

    def patch_shift(
        self,
        shift: Shift | None = None,
    ) -> Dict[str, str]:
        """
        Patch a specific column of a shift.

        Args:
            param shift: The shift to be patched.

        Returns:
            Dict[str, str]: A dictionary with a success message.

        Raises:
            NotFoundError: Error in updating shift.
        """
        if shift and shift.shift_logs:
            query, params = shift_logs_patch_query(self.table_details, shift)
            self.postgres_data_access.update(query, params)
            return {"details": "Shift updated successfully"}
        else:
            raise NotFoundError("Error in updating shift")

    def updated_shift_log_info(self, current_shift_id: str) -> Union[Shift, str]:
        """
        Update the shift log information based on new information from ODA
        sources.

        :param current_shift_id int: The unique identifier of the current shift.
        :returns: Updated Shift if new data found else message stating
        no new data found
        """
        shift_logs_info = {}
        current_shift_data = self.get_shift(current_shift_id)
        current_shift_data = Shift.model_validate(current_shift_data)

        created_after_eb_sbi_info = self.get_oda_data(
            filter_date=current_shift_data.shift_start.isoformat()
        )

        if current_shift_data.shift_logs and current_shift_data.shift_logs.logs:
            for log in current_shift_data.shift_logs.logs:
                log = ShiftLogs.model_validate(log)
                shift_logs_info[log.info["eb_id"]] = log.info
        else:
            current_shift_data.shift_logs = []

        if created_after_eb_sbi_info:
            diff = DeepDiff(
                shift_logs_info, created_after_eb_sbi_info, ignore_order=True
            )

            new_eb_ids = set(
                self._extract_eb_id_from_key(key)
                for key in diff.get("dictionary_item_added", [])
            )
            changed_eb_ids = set(
                [
                    self._extract_eb_id_from_key(key)
                    for key in diff.get("values_changed", {}).keys()
                ]
            )

            new_eb_ids = new_eb_ids - changed_eb_ids

            if new_eb_ids:
                for new_eb_id in new_eb_ids:
                    new_info = created_after_eb_sbi_info[new_eb_id]
                    new_log_obj = ShiftLogs(
                        info=new_info,
                        log_time=datetime.now(tz=timezone.utc),
                        source="ODA",
                    )
                    current_shift_data.shift_logs.append(new_log_obj)

            if changed_eb_ids:
                for updated_eb_id in changed_eb_ids:
                    for i in range(len(current_shift_data.shift_logs.logs)):
                        if (
                            current_shift_data.shift_logs[i].info["eb_id"]
                            == updated_eb_id
                        ):
                            current_shift_data.shift_logs[i].info = (
                                created_after_eb_sbi_info[updated_eb_id]
                            )

            metadata = self.get_latest_metadata(current_shift_id)
            shift = update_metadata(
                current_shift_data,
                metadata=metadata,
                last_modified_by=current_shift_data.shift_operator,
            )

            updated_shift_with_info = self.patch_shift(shift=shift)

            LOGGER.info("Shift Logs have been updated successfully")
            LOGGER.info(updated_shift_with_info)

            return shift

        else:
            LOGGER.info("No New Logs found in ODA")
            return "NO New Logs found in ODA"

    def create_shift_comment(self, shift_comment: ShiftComment):
        """
        Create a new comment for a shift log and save it to the database.

        Args:
            shift_comment (ShiftLogComment): The comment data to create.

        Returns:
            ShiftLogComment: The newly created shift log comment.
        """
        shift_comment_id = self._insert_shift_to_database(
            table_details=ShiftCommentMapping(), entity=shift_comment
        )
        shift_comment.id = shift_comment_id["id"]

        return shift_comment

    def get_shift_comments(self, shift_id=None):
        """
        Retrieve comments from shift logs based on shift ID or EB ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        query, params = select_comments_query(
            table_details=ShiftCommentMapping(), shift_id=shift_id
        )
        comments = self.postgres_data_access.get(query=query, params=params)
        return comments

    def get_shift_comment(self, comment_id):
        """
        Retrieve comments from shift logs based on shift ID or EB ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        query, params = select_comments_query(
            table_details=ShiftCommentMapping(), id=comment_id
        )
        comment = self.postgres_data_access.get(query=query, params=params)[0]
        return comment

    def update_shift_comments(self, shift_comment: ShiftComment):
        """
        Update an existing shift log comment with new data.

        Args:
            shift_log_comment (ShiftLogCommentUpdate): The updated comment data.

        Returns:
            ShiftLogCommentUpdate: The updated shift log comment.
        """
        existing_shift_comment = ShiftComment.model_validate(
            self.get_shift_comment(comment_id=shift_comment.id)
        )
        existing_shift_comment.id = shift_comment.id
        if shift_comment.comment:
            existing_shift_comment.comment = shift_comment.comment
        # if shift_log_comment.eb_id:
        #     existing_shift_log_comment.eb_id = shift_log_comment.eb_id
        # if shift_log_comment.operator_name:
        #     existing_shift_log_comment.operator_name = shift_log_comment.operator_name

        existing_shift_comment.metadata = shift_comment.metadata
        self._update_shift_in_database(
            entity=existing_shift_comment, table_details=ShiftCommentMapping()
        )

        return existing_shift_comment
