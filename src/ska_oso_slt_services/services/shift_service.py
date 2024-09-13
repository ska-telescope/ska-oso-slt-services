import logging
import random
import uuid
from datetime import datetime, timezone
from typing import List, Optional

# shift_repository = PostgresShiftRepository()
from ska_oso_slt_services.data_access.postgres_data_acess import (
    PostgresDataAccess,
    QueryType,
)
from ska_oso_slt_services.models.data_models import Media, Shift, ShiftLogs
from ska_oso_slt_services.repositories.abstract_base import (
    CRUDShiftRepository,
    ShiftRepository,
)
from ska_oso_slt_services.utils.codec import CODEC
from ska_oso_slt_services.utils.metadatamixin import set_new_metadata, update_metadata
from ska_oso_slt_services.utils.sqlqueries import (
    ShiftLogMapping,
    insert_query,
    patch_query,
    select_by_date_query,
    select_by_user_query,
    select_latest_query,
    update_query,
    column_based_query
)

LOGGER = logging.getLogger(__name__)


# from ska_oso_slt_services.repositories.postgres_shift_repository import (
#     PostgresShiftRepository,
# )


class ShiftService(CRUDShiftRepository):
    def __init__(self) -> None:
        self.postgres_data_access = PostgresDataAccess()

    def get_shifts(
        self,
        user_query: Optional[any] = None,
        date_query: Optional[any] = None,
    ) -> List[Shift]:
        try:
            if date_query.shift_start and date_query.shift_end:
                query, params = select_by_date_query(date_query)
            else:
                query, params = select_by_user_query(user_query)
            shift = self.postgres_data_access.get(query, params)
            return shift
        except (ValueError, Exception) as e:
            # Log the error
            LOGGER.error(f"Error getting shift: {e}")

            # Optionally, you can re-raise the exception
            raise

    def get_shift(self, shift_id):
        try:
            query, params = select_latest_query(shift_id=shift_id)
            shift = self.postgres_data_access.get_one(query, params)
            if shift:
                return shift
            else:
                raise ValueError(f"No shift found with ID: {shift_id}")
        except (ValueError, Exception) as e:
            # Log the error
            LOGGER.error(f"Error getting shift: {e}")

            # Optionally, you can re-raise the exception
            raise

    def create_shift(self, shift: Shift) -> Shift:
        """
        Create a new shift record in the database.

        :param shift: The shift object to be created.
        :return: The created shift object.
        :raises Exception: If an error occurs during the database operation.
        """
        try:
            shift = set_new_metadata(shift)
            shift.shift_start = datetime.now(timezone.utc)
            shift.shift_id = f"shift-{uuid.uuid4()}"
            query, params = insert_query(shift=shift)
            self.postgres_data_access.insert(query, params)
            return shift
        except ValueError as e:
            # Handle ValueError specifically
            LOGGER.error(f"ValueError occurred: {e}")
            # You can return an error message or take appropriate action
            return "Invalid value encountered. Please check your input."
        except Exception as e:
            # Handle other exceptions
            LOGGER.error(f"Error occurred while inserting shift record: {e}")
            raise e

    def update_shift(self, shift: Shift) -> Shift:
        """
        Update an existing shift record in the database.

        :param shift: The shift object with updated information.
        :return: The updated shift object.
        :raises Exception: If an error occurs during the database operation.
        """
        try:
            shift = update_metadata(shift)
            shift.shift_end = datetime.now(timezone.utc)
            if shift.comments:
                query, params = column_based_query(shift_id=shift.shift_id, column_name="comments")
                result = self.postgres_data_access.get_one(query, params)
                if result is None:
                    raise ValueError(f"No shift found with ID: {shift.shift_id}")
                shift.comments = shift.comments + " " + result["comments"]
            query, params = update_query(shift=shift)
            self.postgres_data_access.update(query, params)
            return shift
        except ValueError as e:
            # Handle ValueError specifically
            LOGGER.error(f"ValueError occurred: {e}")
            # You can return an error message or take appropriate action
            return "Invalid value encountered. Please check your input."
        except Exception as e:
            # Handle other exceptions
            LOGGER.error(f"Error occurred while inserting shift record: {e}")
            raise e

    def patch_shift(self, shift_id: str | None, comments: str | None) -> Shift:
        # get comments from database

        query, params = patch_query(
            column_names=("comments",), values=(comments,), shift_id=shift_id
        )
        return self.postgres_data_access.update(query, params)

    def get_media(self, shift_id: int) -> Media:
        """
        Retrieve the media data associated with a specific shift.

        :param shift_id: The unique identifier of the shift.
        :return: A list of Media objects associated with the shift.
        """
        query = """
        SELECT media
        FROM tab_oda_slt
        WHERE sid = %s;
        """
        params = (shift_id,)
        rows = self.postgresDataAccess.execute_query_or_update(
            query=query, params=params, query_type=QueryType.GET
        )

        if not rows:
            return []

        media_data = rows[0]["media"]
        if media_data is None:
            return []

        return media_data

    def add_media(self, shift_id: int, media: Media) -> Media:
        query = """
        UPDATE tab_oda_slt
        SET media = CASE
            WHEN media IS NULL THEN %s::jsonb
            ELSE media || %s::jsonb
        END
        WHERE sid = %s
        RETURNING media;
        """

        params = (json.dumps(media), json.dumps(media), shift_id)
        rows = self.postgresDataAccess.execute_query_or_update(
            query=query, params=params, query_type=QueryType.PUT
        )

        if not rows:
            return False

        return True
        return self.crud_shift_repository.add_media(shift_id, media)

    def delete_shift(self, sid: str):
        pass
