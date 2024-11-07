import logging
from typing import Any, Dict, List, Optional, Type

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.domain.shift_models import (
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
)
from ska_oso_slt_services.repository.postgress_shift_repository import (
    CRUDShiftRepository,
    PostgresShiftRepository,
)
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

    def get_shift(self, shift_id: str) -> Shift:
        """
        Retrieve a shift by its ID.

        Args:
            shift_id (str): The ID of the shift to retrieve.

        Returns:
            Shift: The shift data if found, None otherwise.
        """
        result = self.postgres_repository.get_shift(shift_id)
        if result:
            shift_with_metadata = self._prepare_shift_with_metadata(result)
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

    def add_media(self, shift_id, files) -> Media:
        """
        Add a media file to a shift.

        Args:
            shift_id (str): The ID of the shift to add the media to.
            file (file): The media file to add.

        Returns:
            Shift: The updated shift with the added media.
        """
        metadata = self.postgres_repository.get_latest_metadata(shift_id)
        stored_shift = Shift.model_validate(
            self.postgres_repository.get_shift(shift_id)
        )
        if not stored_shift:
            raise NotFoundError(f"No shift found with ID: {shift_id}")
        if stored_shift.shift_end:
            raise ShiftEndedException()
        shift = update_metadata(
            stored_shift,
            metadata=metadata,
            last_modified_by=stored_shift.shift_operator,
        )
        result = self.postgres_repository.add_media(files, shift)
        return result.media

    def get_media(self, shift_id) -> list[Media]:
        """
        Get a media file from a shift.

        Args:
            shift_id (str): The ID of the shift to get the media from.

        Returns:
            file: The requested media file.
        """
        return self.postgres_repository.get_media(shift_id)

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
