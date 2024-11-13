import logging
import threading
from functools import lru_cache
from typing import Any, Dict, List, Optional, Type, Union

from confluent_kafka import Consumer, KafkaError, Producer

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.data_access.postgres.mapping import (
    ShiftCommentMapping,
    ShiftLogCommentMapping,
)
from ska_oso_slt_services.domain.shift_models import (
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftComment,
    ShiftLogComment,
)
from ska_oso_slt_services.repository.postgress_shift_repository import (
    CRUDShiftRepository,
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.config import KafkaConfig
from ska_oso_slt_services.utils.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.utils.metadata_mixin import set_new_metadata, update_metadata

LOGGER = logging.getLogger(__name__)


class ShiftService:
    def __init__(self, repositories: List[Type[CRUDShiftRepository]]):
        """
        Initialize the ShiftService with a list of repository classes.

        Args:
            repositories (List[Type[CRUDShiftRepository]]): A list of repository classes
                that inherit from CRUDShiftRepository.

        Raises:
            ValueError: If no PostgresShiftRepository
            is provided in the list of repositories.
        """
        self.shift_repositories = []
        self.postgres_repository = None

        self._initialize_repositories(repositories)
        self._validate_postgres_repository()

    def _initialize_repositories(self, repositories: List[Type[CRUDShiftRepository]]):
        """
        Initialize repository instances from the provided repository classes.

        Args:
            repositories (List[Type[CRUDShiftRepository]]): A list of
            repository classes.
        """
        for repo_class in repositories:
            if issubclass(repo_class, CRUDShiftRepository):
                repo_instance = repo_class()
                self.shift_repositories.append(repo_instance)
                if isinstance(repo_instance, PostgresShiftRepository):
                    self.postgres_repository = repo_instance

    def _validate_postgres_repository(self):
        """
        Ensure that a PostgresShiftRepository instance is available.

        Raises:
            ValueError: If no PostgresShiftRepository is found.
        """
        if not self.postgres_repository:
            raise ValueError("PostgresShiftRepository is required")

    def merge_comments(self, shifts: List[dict]):
        """
        Merge comments into shift logs for the provided list of shifts.

        Args:
            shifts (List[dict]): List of shift data dictionaries.

        Returns:
            List[dict]: List of shift data with merged comments in shift logs.
        """
        for shift in shifts:
            shift_log_comments_dict = self.postgres_repository.get_shift_logs_comments(
                shift_id=shift["shift_id"]
            )
            if shift.get("shift_logs"):
                for shift_log in shift["shift_logs"]:
                    shift_log["comments"] = []
                    for comment in shift_log_comments_dict:
                        if shift_log["info"]["eb_id"] == comment["eb_id"]:
                            shift_log["comments"].append(comment)
        return shifts

    def merge_shift_comments(self, shifts):
        for shift in shifts:
            shift_comment_dict = self.postgres_repository.get_shift_comments(
                shift_id=shift["shift_id"]
            )
            shift["comments"] = shift_comment_dict

        return shifts

    def get_shift(self, shift_id: str) -> Shift:
        """
        Retrieve a shift by its ID.

        Args:
            shift_id (str): The ID of the shift to retrieve.

        Returns:
            Shift: The shift data if found, None otherwise.
        """
        shift = self.postgres_repository.get_shift(shift_id)

        if shift:
            shifts_with_log_comments = self.merge_comments([shift])[0]
            shifts_with_comments_and_log_comments = self.merge_shift_comments(
                [shifts_with_log_comments]
            )[0]

            shift_with_metadata = self._prepare_shift_with_metadata(
                shifts_with_comments_and_log_comments
            )

            return shift_with_metadata
        else:
            raise NotFoundError(f"No shift found with ID: {shift_id}")

    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        status: Optional[SbiEntityStatus] = None,
    ) -> list[Shift]:
        """
        Retrieve shifts based on the provided query parameters.

        Args:
            shift (Optional[Shift]): The shift object containing query parameters.
            match_type (Optional[MatchType]): The match type for the query.
            status (Optional[SbiEntityStatus]): The SBI status present
            in shift_logs data.

        Returns:
            list[Shift]: A list of shift matching the query,
            or raises Shift Not Found.

        Raises:
            NotFoundError: If no shifts are found for the given query.
        """
        shifts = self.postgres_repository.get_shifts(shift, match_type, status)
        if not shifts:
            raise NotFoundError("No shifts found for the given query.")
        LOGGER.info("Shifts: %s", shifts)
        prepared_shifts = []
        for shift in shifts:
            processed_shift = self._prepare_shift_with_metadata(shift)
            prepared_shifts.append(processed_shift)
        return prepared_shifts

    def create_shift(self, shift_data) -> Shift:
        """
        Create a new shift.

        Args:
            shift_data (Shift): A shift object for create shift.

        Returns:
            Shift: The created shift data.
        """
        shift = set_new_metadata(shift_data, created_by=shift_data.shift_operator)
        return self.postgres_repository.create_shift(shift)

    def update_shift(self, shift_id, shift_data):
        """
        Update an existing shift.

        Args:
            shift_data (Shift): A shift object for update shift.

        Returns:
            Shift: The updated shift data.

        Raises:
            ShiftEndedException : If after shift end fields are updated other
            than annotation
        """

        shift_data.shift_id = shift_id
        current_shift_status = self.get_shift(shift_id=shift_data.shift_id)
        if current_shift_status.shift_end:
            # TODO remove hardcoding of fields here as this are only used once
            # so separate config file currently not feasible
            if {k for k, v in vars(shift_data).items() if v} - {
                "shift_id",
                "annotations",
                "shift_start",
            }:
                raise ShiftEndedException()

        metadata = self.postgres_repository.get_latest_metadata(shift_data.shift_id)
        if not metadata:
            raise NotFoundError(f"No shift found with ID: {shift_data.shift_id}")
        shift = update_metadata(
            shift_data, metadata=metadata, last_modified_by=shift_data.shift_operator
        )
        return self.postgres_repository.update_shift(shift)

    def post_media(
        self, shift_id, shift_operator, file, shift_model, table_mapping, eb_id=None
    ) -> Media:
        """
        Create a new comment for a shift log with metadata.

        Args:
            shift_id: The unique identifier for the shift log.
            shift_operator: The operator of the shift log.
            file: The file to be uploaded.
            shift_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.
            eb_id: The EB ID of the shift log.

        Returns:
            ShiftLogComment: The created shift log comment.
        """
        shift = self.get_shift(shift_id)
        if not shift:
            raise NotFoundError(f"No shift found with id: {shift_id}")

        shift_comment = shift_model(shift_id=shift_id, operator_name=shift_operator)

        if shift_comment.__class__.__name__ == "ShiftLogComment":
            shift_comment.eb_id = eb_id
        shift_comment = set_new_metadata(shift_comment, shift_operator)

        result = self.postgres_repository.insert_shift_image(
            file=file, shift_comment=shift_comment, table_mapping=table_mapping
        )
        return result

    def add_media(self, comment_id, files, shift_model, table_mapping) -> Media:
        """
        Add a media file to a shift.

        Args:
            comment_id (int): The ID of the comment to add the media to.
            files (files): The media files to add.
            shift_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.

        Returns:
            Shift: The updated comment with the added media.
        """
        metadata = self.postgres_repository.get_latest_metadata(
            entity_id=comment_id, table_details=table_mapping
        )

        stored_shift = shift_model(id=comment_id)

        stored_shift.metadata = metadata

        shift = update_metadata(
            entity=stored_shift,
            metadata=metadata,
        )
        result = self.postgres_repository.add_media(
            shift_comment=shift,
            files=files,
            shift_model=shift_model,
            table_mapping=table_mapping,
        )
        return result.image

    def get_media(self, comment_id, shift_model, table_mapping) -> list[Media]:
        """
        Get a media file from a shift.

        Args:
            comment_id (int): The ID of the comment to get the media from.
            shift_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.

        Returns:
            file: The requested media file.
        """
        return self.postgres_repository.get_media(
            comment_id, shift_model, table_mapping
        )

    def delete_shift(self, shift_id):
        """
        Delete a shift by its shift_id.

        Args:
            shift_id (str): The ID of the shift to delete.
        """
        self.postgres_repository.delete_shift(shift_id)

    def _prepare_shift_with_metadata(self, shift: Dict[Any, Any]) -> Shift:
        """
        Prepare a shift object with metadata.

        Args:
            shift (Dict[Any, Any]): Raw shift data from the database.

        Returns:
            Shift: A Shift object with metadata included.
        """
        shift_load = Shift.model_validate(shift)
        metadata_dict = self._create_metadata(shift)
        shift_load.metadata = Metadata.model_validate(metadata_dict)

        return shift_load

    def _create_metadata(self, shift: Dict[Any, Any]) -> Dict[str, str]:
        """
        Create metadata dictionary from shift data.

        Args:
            shift (Dict[Any, Any]): The shift data.

        Returns:
            Dict[str, str]: A dictionary containing metadata information.
        """
        return {
            "created_by": shift["created_by"],
            "created_on": shift["created_on"],
            "last_modified_on": shift["last_modified_on"],
            "last_modified_by": shift["last_modified_by"],
        }

    def create_shift_logs_comment(self, shift_log_comment_data) -> ShiftLogComment:
        """
        Create a new comment for a shift log with metadata.

        Args:
            shift_log_comment_data: The comment data for the shift log.

        Returns:
            ShiftLogComment: The created shift log comment.
        """

        missing_fields = []
        if not shift_log_comment_data.shift_id:
            missing_fields.append("shift_id")
        if not shift_log_comment_data.eb_id:
            missing_fields.append("eb_id")
        if not shift_log_comment_data.operator_name:
            missing_fields.append("operator_name")

        if missing_fields:
            raise ValueError("Following fields are required", missing_fields)

        shift_log_comment = set_new_metadata(
            shift_log_comment_data, shift_log_comment_data.operator_name
        )
        return self.postgres_repository.create_shift_logs_comment(
            shift_log_comment=shift_log_comment
        )

    def get_shift_logs_comments(
        self, shift_id: str = None, eb_id: str = None
    ) -> List[ShiftLogComment]:
        """
        Retrieve comments for shift logs based on shift ID or EB ID.

        Args:
            shift_id (str, optional): The shift ID for filtering comments.
            eb_id (str, optional): The EB ID for filtering comments.

        Returns:
            List[ShiftLogComment]: List of comments matching the specified query.

        Raises:
            NotFoundError: If no comments are found for the given filters.
        """
        shift_log_comments = self.postgres_repository.get_shift_logs_comments(
            shift_id=shift_id, eb_id=eb_id
        )

        if not shift_log_comments:
            raise NotFoundError("No shifts log comments found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_log_comments)

        return shift_log_comments

    def update_shift_log_comments(self, comment_id, shift_log_comment: ShiftLogComment):
        """
        Update an existing shift log comment with new data.

        Args:
            comment_id (int): The ID of the comment to update.
            shift_log_comment (ShiftLogComment): The updated comment data.

        Returns:
            ShiftLogComment: The updated shift log comment.

        Raises:
            NotFoundError: If no comment is found with the provided ID.
        """
        shift_log_comment.id = comment_id
        metadata = self.postgres_repository.get_latest_metadata(
            entity_id=shift_log_comment.id, table_details=ShiftLogCommentMapping()
        )
        if not metadata:
            raise NotFoundError(f"No Comment found with ID: {shift_log_comment.id}")

        shift_log_comment_with_metadata = update_metadata(
            entity=shift_log_comment,
            metadata=metadata,
            last_modified_by=shift_log_comment.operator_name,
        )

        return self.postgres_repository.update_shift_logs_comments(
            shift_log_comment_with_metadata
        )

    def update_shift_log_with_image(self, comment_id, operator_name, file):
        """
        Update a shift log comment with an image.

        Args:
            comment_id (int): The ID of the comment to update.
            operator_name (str): The name of the operator adding the image.
            file: The image file to add.

        Returns:
            ShiftLogComment: The updated shift log comment with the image added.

        Raises:
            NotFoundError: If no comment is found with the provided ID.
        """
        metadata = self.postgres_repository.get_latest_metadata(
            entity_id=comment_id, table_details=ShiftLogCommentMapping()
        )

        if not metadata:
            raise NotFoundError(f"No Comment found with ID: {comment_id}")

        shift_log_comment = ShiftLogComment(id=comment_id, operator_name=operator_name)
        shift_log_comment.metadata = metadata

        shift_log_comment_with_metadata = update_metadata(
            entity=shift_log_comment,
            metadata=metadata,
            last_modified_by=shift_log_comment.operator_name,
        )

        return self.postgres_repository.update_shift_log_with_image(
            shift_log_comment=shift_log_comment_with_metadata, file=file
        )

    def get_current_shift(self):
        """
        Retrieve the current shift.

        This method fetches the most recent shift from the database, based on the
        `created_on` timestamps. It retrieves the shift from
        the Postgres repository and returns it with associated metadata.

        Returns:
            Shift: The most recent shift object in the system, with metadata included.

        Raises:
            ValueError: If the PostgresShiftRepository is not available.
            NotFoundError: If no shifts are found in the system.
        """

        if not self.postgres_repository:
            raise ValueError("PostgresShiftRepository is not available")

        result = self.postgres_repository.get_current_shift()
        if result:
            shift_with_metadata = self._prepare_shift_with_metadata(result)
            return shift_with_metadata
        else:
            raise NotFoundError("No shift found")

    def updated_shift_log_info(self, current_shift_id: str) -> Union[Shift, str]:
        """
        Update the shift log info for a given shift ID.

        Args:
            current_shift_id (str): The ID of the shift to update.

        Returns:
            Union[Shift, str]: The updated shift object if successful, or an error
        """
        return self.postgres_repository.updated_shift_log_info(current_shift_id)

    def create_shift_comment(self, shift_comment_data: ShiftComment) -> ShiftComment:
        """
        Create a new comment for a shift log with metadata.

        Args:
            shift_log_comment_data: The comment data for the shift log.

        Returns:
            ShiftLogComment: The created shift log comment.
        """
        if not shift_comment_data.shift_id:
            raise ValueError("SHift id is required")

        shift = self.get_shift(shift_comment_data.shift_id)
        if not shift:
            raise NotFoundError(
                f"No shift found with id: {shift_comment_data.shift_id}"
            )

        shift_comment = set_new_metadata(shift_comment_data, shift.shift_operator)
        return self.postgres_repository.create_shift_comment(
            shift_comment=shift_comment
        )

    def get_shift_comments(self, shift_id: str = None) -> List[ShiftComment]:
        """
        Retrieve comments for shift logs based on shift ID or EB ID.

        Args:
            shift_id (str, optional): The shift ID for filtering comments.
            eb_id (str, optional): The EB ID for filtering comments.

        Returns:
            List[ShiftLogComment]: List of comments matching the specified query.

        Raises:
            NotFoundError: If no comments are found for the given filters.
        """
        shift_comments = self.postgres_repository.get_shift_comments(shift_id=shift_id)

        if not shift_comments:
            raise NotFoundError("No shifts comments found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_comments)

        return shift_comments

    def get_shift_comment(self, comment_id: str = None) -> List[ShiftComment]:
        """
        Retrieve comments for shift logs based on shift ID or EB ID.

        Args:
            shift_id (str, optional): The shift ID for filtering comments.
            eb_id (str, optional): The EB ID for filtering comments.

        Returns:
            List[ShiftLogComment]: List of comments matching the specified query.

        Raises:
            NotFoundError: If no comments are found for the given filters.
        """
        shift_comment = self.postgres_repository.get_shift_comment(
            comment_id=comment_id
        )

        if not shift_comment:
            raise NotFoundError("No shift comment found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_comment)

        return shift_comment

    def update_shift_comments(self, comment_id, shift_comment: ShiftComment):
        """
        Update an existing shift log comment with new data.

        Args:
            comment_id (int): The ID of the comment to update.
            shift_log_comment (ShiftLogCommentUpdate): The updated comment data.

        Returns:
            ShiftLogCommentUpdate: The updated shift log comment.

        Raises:
            NotFoundError: If no comment is found with the provided ID.
        """
        # for getting shift_id to get operator name
        existing_shift_comment = self.get_shift_comment(comment_id=comment_id)

        if not existing_shift_comment:
            raise NotFoundError(f"No comment found with id: {comment_id}")

        shift = self.get_shift(existing_shift_comment["shift_id"])
        if not shift:
            raise NotFoundError(f"No shift found with id: {shift_comment['shift_id']}")

        shift_comment.id = int(comment_id)
        metadata = self.postgres_repository.get_latest_metadata(
            entity_id=shift_comment.id, table_details=ShiftCommentMapping()
        )
        if not metadata:
            raise NotFoundError(f"No Comment found with ID: {shift_comment.id}")

        shift_log_comment_with_metadata = update_metadata(
            entity=shift_comment,
            metadata=metadata,
            last_modified_by=shift.shift_operator,
        )

        return self.postgres_repository.update_shift_comments(
            shift_log_comment_with_metadata
        )


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


# Callback for successful delivery or error
def delivery_report(err, msg):
    if err is not None:
        LOGGER.error("Message delivery failed: %s", err)
    else:
        LOGGER.error(
            "Message delivered to %s [%s] at offset %s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


class ShiftLogUpdater:
    """
    Class for updating Shift Logs
    """

    def __init__(self):
        self.current_shift_id: Optional[int] = None
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._background_task, daemon=True)
        self.thread_started = False

        consumer_conf = {
            "bootstrap.servers": KafkaConfig.BOOTSTRAP_SERVER,
            "group.id": KafkaConfig.GROUP_ID,
            "auto.offset.reset": KafkaConfig.AUTO_OFFSET_RESET,
        }

        producer_conf = {
            "bootstrap.servers": KafkaConfig.BOOTSTRAP_SERVER,
            "client.id": KafkaConfig.CLIEND_ID,
        }

        self.consumer = Consumer(consumer_conf)
        LOGGER.info("KAFKA CONFIGURED WITH FOLLOWING CONFIGURATION %s", consumer_conf)

        self.producer = Producer(producer_conf)

        self.producer_topic = KafkaConfig.PRODUCER_TOPIC
        self.consumer_topic = KafkaConfig.CONSUMER_TOPIC

    def _background_task(self):
        """
        Checks if new EB data is added or updated to ODA using Kafka Topic
        Once found Updates the same into the Current Shift and sends Notification to
        SLT UI through Topic.
        """

        try:
            self.consumer.subscribe([self.consumer_topic])
            metadata = self.consumer.list_topics(timeout=10.0)
            LOGGER.debug("Subscribed to topics: %s", metadata.topics)
            while True:
                LOGGER.debug("Checking for new data")

                message = self.consumer.poll(timeout=float(KafkaConfig.TOPIC_POLL_TIME))
                if message is None:
                    LOGGER.debug("No new notification from ODA")
                    continue
                if message.error():
                    if (
                        message.error().code()
                        == KafkaError._PARTITION_EOF  # pylint: disable=W0212
                    ):
                        LOGGER.debug("End of partition")
                    else:
                        LOGGER.info("Error occurred: %s", message.error())
                else:
                    LOGGER.info(
                        "Received message: %s from partition %s",
                        message.value().decode("utf-8"),
                        message.partition(),
                    )
                    shift_service.updated_shift_log_info(self.current_shift_id)
                    message = (
                        "Current Shift %s  Logs have been updated kindly check...",
                        self.current_shift_id,
                    )
                    self.producer.produce(
                        self.producer_topic,
                        message[0].encode("utf-8"),
                        callback=delivery_report,
                    )
                    self.producer.flush()

                    LOGGER.info("Message to frontend: %s,message")

        finally:
            self.consumer.close()

    def start(self):
        """
        Starts the background polling thread if it has not already been started.
        This method ensures that the polling of Kafka topics begins only once.
        """
        if not self.thread_started:
            LOGGER.debug("\n\nPolling Started")
            self.thread.start()
            self.thread_started = True

    def update_shift_id(self, shift_id: int):
        """
        Updates the current shift ID and ensures that the background thread is started
        for polling Kafka topics.

        Args:
            shift_id (int): The ID of the shift to be updated.
        """
        with self.lock:
            self.current_shift_id = shift_id
            self.start()
