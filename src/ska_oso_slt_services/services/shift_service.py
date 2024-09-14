import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from dateutil import parser
from psycopg2 import Error as PostgresError

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresDataAccess
from ska_oso_slt_services.infrastructure.abstract_base import CRUDShiftRepository
from ska_oso_slt_services.infrastructure.postress.mapping import ShiftLogMapping
from ska_oso_slt_services.infrastructure.postress.sqlqueries import (
    column_based_query,
    insert_query,
    patch_query,
    select_by_date_query,
    select_by_user_query,
    select_latest_query,
    update_query,
)
from ska_oso_slt_services.models.shiftmodels import Media, Metadata, Shift
from ska_oso_slt_services.utils.codec import CODEC
from ska_oso_slt_services.utils.exception import DatabaseError, InvalidInputError
from ska_oso_slt_services.utils.metadatamixin import set_new_metadata, update_metadata

LOGGER = logging.getLogger(__name__)


class ShiftService(CRUDShiftRepository):
    def __init__(self) -> None:
        self.postgres_data_access = PostgresDataAccess()
        self.table_details = ShiftLogMapping()

    async def get_shifts(
        self,
        user_query: Optional[any] = None,
        date_query: Optional[any] = None,
    ) -> List[Shift]:
        try:
            if date_query.shift_start and date_query.shift_end:
                query, params = select_by_date_query(self.table_details, date_query)
            else:
                query, params = select_by_user_query(self.table_details, user_query)
            shifts = await self.postgres_data_access.get(query, params)
            LOGGER.info(f"Shifts: {shifts}")
            prepared_shifts = []
            for shift in shifts:
                processed_shift = self._prepare_shift_with_metadata(shift)
                prepared_shifts.append(processed_shift)
            return prepared_shifts
        except (ValueError, Exception) as e:
            # Log the error
            LOGGER.error(f"Error getting shift: {e}")

            # Optionally, you can re-raise the exception
            raise

    async def get_shift(self, shift_id):
        try:
            query, params = select_latest_query(self.table_details, shift_id=shift_id)
            shift = await self.postgres_data_access.get_one(query, params)
            shift_with_metadata = self._prepare_shift_with_metadata(shift)
            if shift_with_metadata:
                return shift_with_metadata
            else:
                raise ValueError(f"No shift found with ID: {shift_id}")
        except (ValueError, Exception) as e:
            # Log the error
            LOGGER.error(f"Error getting shift: {e}")

            # Optionally, you can re-raise the exception
            raise

    def _prepare_shift_with_metadata(self, shift: Dict[Any, Any]) -> Shift:
        processed_data = json.loads(json.dumps(shift, default=self._datetime_to_string))
        shift_load = CODEC.loads(Shift, json.dumps(processed_data))

        metadata_dict = self._create_metadata(shift)
        shift_load.metadata = Metadata(**metadata_dict)

        return shift_load

    def _parse_datetime_string(self, date_string: str) -> datetime:
        dt = parser.parse(date_string)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def _datetime_to_string(self, obj: Any) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def _create_metadata(self, shift: Dict[Any, Any]) -> Dict[str, str]:
        return {
            "created_by": shift["created_by"],
            "created_on": self._parse_datetime_string(shift["created_on"].isoformat()),
            "last_modified_on": self._parse_datetime_string(
                shift["last_modified_on"].isoformat()
            ),
            "last_modified_by": shift["last_modified_by"],
        }

    async def create_shift(self, shift: Shift) -> Shift:
        """
        Create a new shift with updated metadata, start time, and unique ID.

        Args:
            shift (Shift): The shift object to be created.

        Returns:
            Shift: The newly created shift with updated attributes.
        """
        shift = self._prepare_new_shift(shift)
        await self._insert_shift_to_database(shift)
        return shift

    def _prepare_new_shift(self, shift: Shift) -> Shift:
        """
        Prepare a new shift by setting metadata, start time, and unique ID.

        Args:
            shift (Shift): The shift object to be prepared.

        Returns:
            Shift: The prepared shift object.
        """
        shift = set_new_metadata(shift)
        shift.shift_start = datetime.now(timezone.utc)
        shift.shift_id = f"shift-{uuid.uuid4()}"
        return shift

    async def _insert_shift_to_database(self, shift: Shift) -> None:
        """
        Insert the shift into the database.

        Args:
            shift (Shift): The shift object to be inserted.
        """
        query, params = self._build_insert_query(shift)
        await self.postgres_data_access.insert(query, params)

    def _build_insert_query(self, shift: Shift) -> Tuple[str, Any]:
        """
        Build the insert query and parameters for the given shift.

        Args:
            shift (Shift): The shift object to build the query for.

        Returns:
            Tuple[str, Any]: A tuple containing the query string and its parameters.
        """
        return insert_query(table_details=self.table_details, shift=shift)

    async def update_shift(self, shift: Shift) -> Shift:
        try:
            shift = update_metadata(shift)
            if shift.comments:
                existing_shift = await self._get_existing_shift(shift.shift_id)
                self._validate_shift_end(existing_shift)
                shift.comments = self._merge_comments(
                    shift.comments, existing_shift["comments"]
                )

            await self._update_shift_in_database(shift)
            return shift
        except ValueError as e:
            # Consider logging the error here
            LOGGER.error(f"Error updating shift: {e}")
            raise e

    async def _get_existing_shift(self, shift_id: int) -> Optional[dict]:
        query, params = column_based_query(
            table_details=self.table_details,
            shift_id=shift_id,
            column_names=["comments", "shift_end"],
        )
        result = await self.postgres_data_access.get_one(query, params)
        if result is None:
            raise ValueError(f"No shift found with ID: {shift_id}")
        return result

    def _validate_shift_end(self, existing_shift: dict) -> None:
        if existing_shift["shift_end"]:
            raise ValueError(f"After shift end update shift disabled")

    def _merge_comments(
        self, new_comments: str, existing_comments: Optional[str]
    ) -> str:
        if existing_comments:
            return f"{new_comments} {existing_comments}"
        return new_comments

    async def _update_shift_in_database(self, shift: Shift) -> None:
        query, params = update_query(self.table_details, shift=shift)
        await self.postgres_data_access.update(query, params)

    async def patch_shift(
        self, shift_id: str | None, column_name: str | None, column_value: str | None
    ) -> Shift:
        # get comments from database
        try:
            self._get_existing_shift(shift_id)
            query, params = patch_query(
                self.table_details,
                column_names=[column_name],
                values=[column_value],
                shift_id=shift_id,
            )
            await self.postgres_data_access.update(query, params)
            return {"details": "Shift updated"}
        except PostgresError as e:
            raise DatabaseError(
                f"Database error occurred while patching shift: {str(e)}"
            ) from e
        except ValueError as e:
            raise DatabaseError(
                f"Database error occurred while patching shift: {str(e)}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Unexpected error occurred while patching shift: {str(e)}"
            ) from e

    def get_media(self, shift_id: int) -> Media:
        pass

    def add_media(self, shift_id: int, media: Media) -> Media:
        pass

    def delete_shift(self, sid: str):
        pass
