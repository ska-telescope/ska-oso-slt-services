import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.data_access.postgres.mapping import ShiftLogMapping
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    column_based_query,
    insert_query,
    patch_query,
    select_by_date_query,
    select_by_user_query,
    select_latest_query,
    select_metadata_query,
    update_query,
)
from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    Media,
    Metadata,
    Shift,
    UserQuery,
)
from ska_oso_slt_services.repository.shift_repository import CRUDShiftRepository
from ska_oso_slt_services.utils.date_utils import get_datetime_for_timezone

LOGGER = logging.getLogger(__name__)


class PostgressShiftRepository(CRUDShiftRepository):
    """
    Postgress implementation of the CRUDShiftRepository.

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
        user_query: Optional[UserQuery] = None,
        date_query: Optional[DateQuery] = None,
    ) -> List[Shift]:
        """
        Retrieve shifts based on user or date query.

        Args:
            user_query (Optional[any]): Query parameters for user-based search.
            date_query (Optional[any]): Query parameters for date-based search.

        Returns:
            List[Shift]: A list of Shift objects matching the query.

        Raises:
            NotFoundError: If there's an error in processing the query.
            Exception: For any other unexpected errors.
        """

        if date_query.shift_start and date_query.shift_end:
            query, params = select_by_date_query(self.table_details, date_query)
        else:
            query, params = select_by_user_query(self.table_details, user_query)
        shifts = self.postgres_data_access.get(query, params)
        return shifts

    def get_shift(self, shift_id):
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
        shift.shift_start = get_datetime_for_timezone("UTC")
        shift.shift_id = f"shift-{uuid.uuid4()}"
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
        self._validate_shift_exists(shift.shift_id)
        if shift.comments:
            existing_shift = self._get_existing_shift(shift.shift_id)
            self._validate_shift_end(existing_shift)
            shift.comments = self._merge_comments(
                shift.comments, existing_shift["comments"]
            )

        self._update_shift_in_database(shift)
        return shift

    def get_latest_metadata(self, shift: Shift) -> Optional[Metadata]:
        """Get latest metadata for update."""

        query, params = select_metadata_query(
            table_details=self.table_details,
            shift_id=shift.shift_id,
        )
        meta_data = self.postgres_data_access.get_one(query, params)
        return Metadata.model_validate(meta_data)

    def _get_existing_shift(self, shift_id: int) -> Optional[dict]:
        """
        Retrieve an existing shift from the database.

        Args:
            shift_id (int): The ID of the shift to retrieve.

        Returns:
            Optional[dict]: The shift data if found, None otherwise.

        Raises:
            ValueError: If no shift is found with the given ID.
        """
        query, params = column_based_query(
            table_details=self.table_details,
            shift_id=shift_id,
            column_names=["comments", "shift_end"],
        )
        result = self.postgres_data_access.get_one(query, params)
        if result is None:
            raise NotFoundError(f"No shift found with ID: {shift_id}")
        return result

    def _validate_shift_end(self, existing_shift: dict) -> None:
        """
        Validate if a shift can be updated based on its end time.

        Args:
            existing_shift (dict): The existing shift data.

        Raises:
            ValueError: If the shift has already ended and cannot be updated.
        """
        if existing_shift["shift_end"]:
            raise ValueError("After shift end update shift disabled")

    def _merge_comments(
        self, new_comments: str, existing_comments: Optional[str]
    ) -> str:
        """
        Merge new comments with existing comments.

        Args:
            new_comments (str): The new comments to add.
            existing_comments (Optional[str]): The existing comments, if any.

        Returns:
            str: The merged comments.
        """
        if existing_comments:
            return f"{existing_comments} {new_comments}"
        return new_comments

    def _update_shift_in_database(self, shift: Shift) -> None:
        """
        Update the shift in the database.

        Args:
            shift (Shift): The shift object to update.
        """
        query, params = update_query(self.table_details, shift=shift)
        self.postgres_data_access.update(query, params)

    def patch_shift(
        self, shift_id: str | None, column_name: str | None, column_value: str | None
    ) -> Dict[str, str]:
        """
        Patch a specific column of a shift.

        Args:
            shift_id (str | None): The ID of the shift to patch.
            column_name (str | None): The name of the column to update.
            column_value (str | None): The new value for the column.

        Returns:
            Dict[str, str]: A dictionary with a success message.

        Raises:
            NotFoundError: If shift_id, column_name, or column_value is None.
            DatabaseError: If there's an error in the database operation.
            RuntimeError: For any unexpected errors during the operation.
        """
        if not all([shift_id, column_name, column_value]):
            raise NotFoundError(
                "shift_id, column_name, and column_value must be provided"
            )

        self._validate_shift_exists(shift_id)
        query, params = self._build_patch_query(shift_id, column_name, column_value)
        self.postgres_data_access.update(query, params)
        return {"details": "Shift updated successfully"}

    def _validate_shift_exists(self, shift_id: str) -> None:
        """
        Validate that a shift with the given ID exists.

        Args:
            shift_id (str): The ID of the shift to validate.

        Raises:
            ValueError: If the shift does not exist.
        """
        existing_shift = self._get_existing_shift(shift_id)
        if not existing_shift:
            raise NotFoundError(f"Shift with ID {shift_id} does not exist")

    def _build_patch_query(
        self, shift_id: str, column_name: str, column_value: str
    ) -> Tuple[str, List[Any]]:
        """
        Build the SQL query and parameters for patching a shift.

        Args:
            shift_id (str): The ID of the shift to patch.
            column_name (str): The name of the column to update.
            column_value (str): The new value for the column.

        Returns:
            Tuple[str, List[Any]]: A tuple containing the SQL query and its parameters.
        """
        query = patch_query(self.table_details, [column_name], [column_value], shift_id)
        params = [column_value, shift_id]
        return query, params

    def get_media(self, shift_id: int) -> Media:
        pass

    def add_media(self, shift_id: int, media: Media) -> Media:
        pass

    def delete_shift(self, sid: str):
        pass
