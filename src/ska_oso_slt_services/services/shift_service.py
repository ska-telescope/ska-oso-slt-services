import logging
from typing import Any, Dict, List, Optional, Type

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    Metadata,
    Shift,
    UserQuery,
)
from ska_oso_slt_services.repository.postgress_shift_repository import (
    CRUDShiftRepository,
    PostgressShiftRepository,
)
from ska_oso_slt_services.utils.metadata_mixin import set_new_metadata, update_metadata

LOGGER = logging.getLogger(__name__)


class ShiftService:
    """
    Service class for managing shift operations.

    This class provides methods for creating, retrieving, updating, and deleting shifts.
    It interacts with the database through the PostgresDataAccess class.
    """

    def __init__(self, repositories: List[Type[CRUDShiftRepository]]):
        self.shift_repositories = []
        self.postgres_repository = None

        for repo_class in repositories:
            if issubclass(repo_class, CRUDShiftRepository):
                repo_instance = repo_class()
                self.shift_repositories.append(repo_instance)
                if isinstance(repo_instance, PostgressShiftRepository):
                    self.postgres_repository = repo_instance

        if not self.postgres_repository:
            raise ValueError("PostgressShiftRepository is required")

    def get_shift(self, shift_id: str) -> Optional[dict]:
        """
        Retrieve a shift by its ID.

        Args:
            shift_id (str): The ID of the shift to retrieve.

        Returns:
            Optional[dict]: The shift data if found, None otherwise.
        """
        if not self.postgres_repository:
            raise ValueError("PostgresShiftRepository is not available")

        result = self.postgres_repository.get_shift(shift_id)
        if result:
            shift_with_metadata = self._prepare_shift_with_metadata(result)
            return shift_with_metadata
        else:
            raise NotFoundError(f"No shift found with ID: {shift_id}")

    def get_shifts(
        self,
        user_query: Optional[UserQuery] = None,
        date_query: Optional[DateQuery] = None,
    ) -> Optional[dict]:
        """
        Retrieve a list of shifts based on the provided query parameters.

        Args:
            user_query (Optional[UserQuery]): Query parameters
            for filtering shifts by user.
            date_query (Optional[DateQuery]): Query parameters
            for filtering shifts by date.

        Returns:
            List[Shift]: A list of shifts matching the query parameters.
        """
        if not self.postgres_repository:
            raise ValueError("PostgresShiftRepository is not available")

        shifts = self.postgres_repository.get_shifts(user_query, date_query)
        if not shifts:
            raise NotFoundError("No shifts found for the given query.")
        LOGGER.info("Shifts: %s", shifts)
        prepared_shifts = []
        for shift in shifts:
            processed_shift = self._prepare_shift_with_metadata(shift)
            prepared_shifts.append(processed_shift)
        return prepared_shifts

    def create_shift(self, shift_data):
        """
        Create a new shift.

        Args:
            shift_data (dict): A dictionary containing the shift data.

        Returns:
            dict: The created shift data.
        """
        shift = set_new_metadata(shift_data, created_by=shift_data.shift_operator)
        return self.postgres_repository.create_shift(shift)

    def update_shift(self, shift_data):
        """
        Update an existing shift.

        Args:
            shift_id (str): The ID of the shift to update.
            shift_data (dict): A dictionary containing the updated shift data.

        Returns:
            dict: The updated shift data.
        """
        metadata = self.postgres_repository.get_latest_metadata(shift_data)
        shift = update_metadata(
            shift_data, metadata=metadata, last_modified_by=shift_data.shift_operator
        )
        return self.postgres_repository.update_shift(shift)

    def patch_shift(
        self, shift_id: str | None, column_name: str | None, column_value: str | None
    ):
        return self.postgres_repository.patch_shift(shift_id, column_name, column_value)

    def delete_shift(self, shift_id):
        """
        Delete a shift by its ID.

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
