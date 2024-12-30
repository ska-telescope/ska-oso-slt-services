import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from deepdiff import DeepDiff
from psycopg import DatabaseError, DataError, InternalError, sql
from ska_ser_skuid.client import SkuidClient

from ska_oso_slt_services.common.constant import (
    ODA_DATA_POLLING_TIME,
    SKUID_ENTITY_TYPE,
    SKUID_URL,
    TELESCOPE_DICT,
)
from ska_oso_slt_services.common.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import update_metadata
from ska_oso_slt_services.common.utils import (
    get_datetime_for_timezone,
    set_telescope_type,
)
from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.data_access.postgres.mapping import ShiftLogMapping
from ska_oso_slt_services.data_access.postgres.shift_crud import DBCrud
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    shift_logs_patch_query,
)
from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftComment,
    ShiftLogComment,
    ShiftLogs,
)
from ska_oso_slt_services.repository.shift_repository import CRUDShiftRepository
from ska_oso_slt_services.utils.s3_bucket import (
    get_file_object_from_s3,
    upload_file_object_to_s3,
)

LOGGER = logging.getLogger(__name__)

skuid = SkuidClient(SKUID_URL)

TELESCOPE_TYPE = set_telescope_type("TELESCOPE_TYPE")


def create_shift_id(
    telescope_type: str = TELESCOPE_TYPE,
    skuid_entity_type: str = SKUID_ENTITY_TYPE,
) -> str:
    """
    Create a shift ID based on the provided parameters.

    ##TODO
    Instead of replace function we should use regex for replacing
    `t` to `m` or `l` its more robust and less error prone.
    This replace functionality maybe be deprecated once SKUID
    supports the id generation based on Telescope type.

    Args:
        telescope_type (str): The Telescope type MID or LOW.
        skuid_entity_type (str): The SKUID entity type.

    Returns:
        str: The generated shift ID.
    """

    return f"{skuid.fetch_skuid(skuid_entity_type)}".replace(
        "t", TELESCOPE_DICT[telescope_type]
    )


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
        self.crud = DBCrud()

    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        entity_status: Optional[SbiEntityStatus] = None,
        entities: Optional[EntityFilter] = None,
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
        shifts = self.crud.get_entities(
            entity=shift,
            db=self.postgres_data_access,
            oda_entities=entities,
            entity_status=entity_status,
            match_type=match_type,
        )
        return shifts

    def get_shift(self, shift_id: str) -> Shift:
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
        filter = {"shift_id": shift_id}
        shift = self.crud.get_entity(
            entity=Shift(), db=self.postgres_data_access, filters=filter
        )
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
        unique_id = self._insert_shift_to_database(entity=shift)
        if unique_id:
            shift.id = unique_id.get("id")
        shift_log_updater.update_shift_id(shift.shift_id)
        return shift

    def _prepare_new_shift(self, shift: Shift) -> Shift:
        """
        Prepare a new shift by setting metadata, start time, and unique ID.

        Args:
            shift (Shift): The shift object to be prepared.

        Returns:
            Shift: The prepared shift object.
        """
        shift.shift_start = get_datetime_for_timezone("UTC")
        # shift.shift_id = create_shift_id()
        import random

        shift.shift_id = "slt-" + str(random.randint(1, 1000000))
        return shift

    def _insert_shift_to_database(self, entity: Any) -> None:
        """
        Insert the entity into the database using appropriate table mapping.

        Args:
            entity: The object to be inserted in DB.

        Returns:
            The ID of the created entry.
        """
        id_created = self.crud.insert_entity(
            entity=entity, db=self.postgres_data_access
        )
        return id_created

    def update_shift_end_time(self, shift: Shift) -> Shift:
        """
        Update the end time of a shift.

        Args:
            shift (Shift): A shift object for update shift end.

        Returns:
            Shift: The updated shift object.
        """

        try:

            existing_shift = Shift.model_validate(self.get_shift(shift.shift_id))

            if existing_shift.shift_end:

                return ShiftEndedException(f"Shift Already Ended: {shift.shift_id}")

            existing_shift.shift_end = get_datetime_for_timezone("UTC")
            existing_shift.metadata = shift.metadata
            self.crud.update_entity(
                entity_id=shift.shift_id,
                entity=existing_shift,
                db=self.postgres_data_access,
            )
            return existing_shift

        except (DatabaseError, DataError, InternalError) as error_msg:

            LOGGER.info("Error updating shift end time: %s", error_msg)
            return error_msg

    def update_shift(self, shift: Shift) -> Shift:
        """
        Update an existing shift with the provided fields.
        Only non-None fields in the shift object will be updated.

        Args:
            shift (Shift): The shift object containing fields to update.
                Only non-None fields will be updated.

        Returns:
            Shift: The updated shift object.

        Raises:
            NotFoundError: If no shift exists with the provided ID.
            ValueError: If there's an error in updating the shift.
        """
        # Update will fail if shift doesn't exist due to WHERE clause in update_query
        self.crud.update_entity(
            entity_id=shift.shift_id,
            entity=shift,
            db=self.postgres_data_access,
        )

        # Fetch and return the updated shift
        updated_shift = self.get_shift(shift.shift_id)
        return updated_shift

    def get_entity_metadata(
        self, entity_id: str | int, model=Shift()
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
        filter = {"entity_id": entity_id}
        meta_data = self.crud.get_entity(
            entity=model, db=self.postgres_data_access, metadata=True, filters=filter
        )
        if not meta_data:
            raise NotFoundError(f"No entity found with ID: {entity_id}")
        return Metadata.model_validate(meta_data)

    def get_media(self, comment_id: int, table_model: Any) -> Media:
        """
        Get a media file from a shift.

        Args:
            comment_id (int): The ID of the comment to get the media from.
            table_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.

        Returns:
            file: The requested media file.
        """
        comment = table_model.model_validate(
            self.get_shift_logs_comment(comment_id=comment_id, entity=table_model)
        )

        if not comment.image:
            raise NotFoundError(f"No media found for comment with ID: {comment_id}")
        files = []

        for image in comment.image:
            file_key, base64_content, content_type = get_file_object_from_s3(
                file_key=image.unique_id
            )
            files.append(
                {
                    "file_key": file_key,
                    "media_content": base64_content,
                    "content_type": content_type,
                }
            )
        return files

    def add_media(
        self,
        comment_id: int,
        shift_comment: ShiftComment,
        files: Any,
        shift_model: Any,
    ) -> Media:
        """
        Add media files associated with a shift comment.

        Args:
            comment_id: id of comment or shift log comment
            files: The media files to be added. Can be single file or multiple files.
            shift_comment (ShiftComment): The shift comment object to associate
            the media with.
            shift_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.

        Returns:
            Media: The media object containing information about the added media files.
        """
        media_list = []
        for file in files:
            file_path, file_unique_id, _ = upload_file_object_to_s3(file)
            media = Media(path=file_path, unique_id=file_unique_id)
            media.timestamp = media.timestamp
            media_list.append(media)

        current_shift_comment = shift_model.model_validate(
            self.get_shift_logs_comment(comment_id=comment_id, entity=shift_comment)
        )

        current_shift_comment.metadata = shift_comment.metadata

        if current_shift_comment.image:
            current_shift_comment.image += media_list
        else:
            current_shift_comment.image = media_list

        self.crud.update_entity(
            entity_id=comment_id,
            entity=current_shift_comment,
            db=self.postgres_data_access,
        )

        return current_shift_comment

    def delete_shift(self, shift_id: str) -> bool:
        """
        Delete a shift by its ID.

        Args:
            shift_id (str): The unique identifier of the shift to delete.

        Returns:
            bool: True if the shift was successfully deleted, False otherwise.

        Raises:
            NotFoundError: If no shift is found with the given ID.
            Exception: For any other unexpected errors.
        """
        pass  # pylint: disable=W0107

    def get_shift_logs_comments(
        self, shift, shift_id: str = None, eb_id: str = None
    ) -> List[ShiftLogComment]:
        """
        Retrieve comments from shift logs based on shift ID or EB ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter comments by.
            eb_id (Optional[str]): The EB ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        filters = {}
        if shift_id:
            filters["shift_id"] = shift_id
        if eb_id:
            filters["eb_id"] = eb_id
        return self.crud.get_entities(
            entity=shift, db=self.postgres_data_access, filters=filters
        )

    def get_shift_logs_comment(self, comment_id, entity=ShiftLogComment()) -> dict:
        return self.crud.get_entity(
            entity=entity,
            db=self.postgres_data_access,
            filters={"comment_id": comment_id},
        )

    def create_shift_logs_comment(self, shift_log_comment: ShiftLogComment) -> dict:
        """
        Create a new comment for a shift log and save it to the database.

        Args:
            shift_log_comment (ShiftLogComment): The comment data to create.

        Returns:
            ShiftLogComment: The newly created shift log comment.
        """
        unique_id = self.crud.insert_entity(
            entity=shift_log_comment, db=self.postgres_data_access
        )
        if unique_id:
            shift_log_comment.id = unique_id.get("id")
        return shift_log_comment

    def update_shift_logs_comments(
        self, comment_id: int, shift_log_comment: ShiftLogComment
    ) -> ShiftLogComment:
        """
        Update an existing shift log comment with new data.

        Args:
            comment_id (int): The ID of the comment to update.
            shift_log_comment (ShiftLogComment): The updated comment data.

        Returns:
            ShiftLogComment: The updated shift log comment.
        """
        self.crud.update_entity(
            entity_id=comment_id,
            entity=shift_log_comment,
            db=self.postgres_data_access,
        )

        updated_log_comment = self.get_shift_logs_comment(
            comment_id, entity=shift_log_comment
        )
        return ShiftLogComment(**updated_log_comment)

    def get_current_shift(self) -> Shift:
        """
        Retrieve the most recent shift from the database.

        This method fetches the latest shift from the database by selecting the
        most recent entry, ordered by  `created_on` timestamps.

        Returns:
            Shift: The most recent shift object in the system.


        """

        return self.crud.get_latest_entity(entity=Shift(), db=self.postgres_data_access)

    def get_oda_data(self, filter_date):
        """Retrieve and process ODA data for the given filter date.

        Args:
            filter_date: The date to filter ODA data from

        Returns:
            dict: Processed ODA information

        Raises:
            Exception: If there are issues with data retrieval or processing
        """
        try:
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
            eb_rows = self.postgres_data_access.get(
                query=sql.SQL(eb_query), params=tuple(eb_params)
            )
        except Exception as e:  # pylint: disable=W0718
            LOGGER.error("Error fetching ODA data: %s", str(e))
        else:
            info = {}
            if eb_rows:
                for eb in eb_rows:
                    if not isinstance(eb.get("info"), dict):
                        LOGGER.warning(  # pylint: disable=W1203
                            f"Missing or invalid info for eb_id {eb.get('eb_id')}"
                        )
                        continue
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
                            sbi_current_status = "Failed"
                        elif ok_count == 5:  # Assuming the total number of blocks is 5
                            sbi_current_status = "Completed"
                        else:
                            sbi_current_status = "Executing"

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
            # TODO planning to remove patch method along along with this
            # below code also get removed
            query, params = shift_logs_patch_query(ShiftLogMapping(), shift)
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

        if current_shift_data.shift_logs and current_shift_data.shift_logs:
            for log in current_shift_data.shift_logs:
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
                    for i in range(len(current_shift_data.shift_logs)):
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
        Create a new comment for a shift and save it to the database.

        Args:
            shift_comment (ShiftComment): The comment data to create.

        Returns:
            ShiftComment: The newly created shift comment.
        """
        unique_id = self.crud.insert_entity(
            entity=shift_comment, db=self.postgres_data_access
        )
        if unique_id:
            shift_comment.id = unique_id.get("id")
        return shift_comment

    def get_shift_comments(self, shift_id: str = None) -> ShiftComment:
        """
        Retrieve comments from shift based on shift ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        return self.crud.get_entities(
            entity=ShiftComment(),
            db=self.postgres_data_access,
            filters={"shift_id": shift_id},
        )

    def get_shift_comment(self, comment_id: int) -> ShiftComment:
        """
        Retrieve comments from shift based on comment ID.

        Args:
            comment_id (Optional[int]): The comment ID to filter comments by.

        Returns:
            List[Dict]: List of comments associated with the specified filters.
        """
        return self.crud.get_entity(
            entity=ShiftComment(),
            db=self.postgres_data_access,
            filters={"id": comment_id},
        )

    def update_shift_comments(
        self, comment_id: int, shift_comment: ShiftComment
    ) -> ShiftComment:
        """
        Update an existing shift comment with new data.

        Args:
            comment_id: Id of comment which needs to update.
            shift_comment (ShiftComment): The updated comment data.

        Returns:
            ShiftComment: The updated shift comment.
        """
        self.crud.update_entity(
            entity_id=comment_id,
            entity=shift_comment,
            db=self.postgres_data_access,
        )

        updated_comment = self.get_shift_comment(comment_id)
        return updated_comment

    def insert_shift_image(self, file: Any, shift_comment: ShiftComment) -> Media:
        """
        Update a shift comment with an image, uploading the image to S3.

        Args:
            shift_comment (ShiftComment): The comment data to update.
            file: The image file to upload.

        Returns:
            ShiftLogCommentUpdate: The updated shift log comment with the image added.
        """
        media_list = []
        file_path, file_unique_id, _ = upload_file_object_to_s3(file)
        media = Media(path=file_path, unique_id=file_unique_id)
        media.timestamp = media.timestamp
        media_list.append(media)
        shift_comment.image = media_list
        self.crud.insert_entity(entity=shift_comment, db=self.postgres_data_access)
        return shift_comment

    def create_shift_annotation(self, shift_annotation: ShiftAnnotation) -> dict:
        """
        Create a new annotation for a shift and save it to the database.

        Args:
            shift_annotation (ShiftAnnotation): The annotation data to create.

        Returns:
            ShiftAnnotation: The newly created shift annotation.
        """
        unique_id = self._insert_shift_to_database(entity=shift_annotation)
        if unique_id:
            shift_annotation.id = unique_id.get("id")
        return shift_annotation

    def get_shift_annotations(self, shift_id: str = None) -> ShiftAnnotation:
        """
        Retrieve annotations from shift based on shift ID.

        Args:
            shift_id (Optional[str]): The shift ID to filter annotations by.

        Returns:
            List[Dict]: List of annotations associated with the specified filters.
        """
        return self.crud.get_entities(
            entity=ShiftAnnotation(),
            db=self.postgres_data_access,
            filters={"shift_id": shift_id},
        )

    def get_shift_annotation(self, annotation_id: int) -> ShiftAnnotation:
        """
        Retrieve annotations from shift based on annotation ID.

        Args:
            annotation_id (Optional[int]): The annotation ID to filter annotations by.

        Returns:
            List[Dict]: List of annotations associated with the specified filters.
        """
        annotation = self.crud.get_entity(
            entity=ShiftAnnotation(),
            db=self.postgres_data_access,
            filters={"annotation_id": annotation_id},
        )
        print(annotation)
        if annotation:
            return annotation
        else:
            raise NotFoundError(f"No annotation found with ID: {annotation_id}")

    def update_shift_annotations(
        self, annotation_id: int, shift_annotation: ShiftAnnotation
    ) -> ShiftAnnotation:
        """
        Update an existing shift annotation with new data.

        Args:
            annotation_id: Id of annotation which needs to update.
            shift_annotation (ShiftAnnotation): The updated annotation data.

        Returns:
            ShiftAnnotation: The updated shift annotation.
        """

        self.crud.update_entity(
            entity_id=annotation_id,
            entity=shift_annotation,
            db=self.postgres_data_access,
        )

        updated_comment = self.get_shift_annotation(annotation_id)
        return updated_comment


class ShiftLogUpdater:
    def __init__(self):
        self.current_shift_id: Optional[int] = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._background_task, daemon=True)
        self.thread_started = False
        self.crud_shift_repository = PostgresShiftRepository()

    def _background_task(self):
        while True:
            with self.lock:
                if self.current_shift_id is not None:
                    LOGGER.info(
                        "------> Checking Updated ODA LOGS for SHIFT ID %s",
                        self.current_shift_id,
                    )
                    self.crud_shift_repository.updated_shift_log_info(
                        self.current_shift_id
                    )
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
