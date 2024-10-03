import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from deepdiff import DeepDiff

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    JsonQuery,
    Logs,
    Metadata,
    Shift,
    ShiftLogs,
    TextQuery,
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
        text_query: Optional[TextQuery] = None,
        json_query: Optional[JsonQuery] = None,
    ) -> Optional[dict]:
        """
        Retrieve a list of shifts based on the provided query parameters.

        Args:
            user_query (Optional[UserQuery]): Query parameters
            for filtering shifts by user.
            date_query (Optional[DateQuery]): Query parameters
            for filtering shifts by date.
            text_query (Optional[TextQuery]): Query parameters
            for filtering shifts by text.
            json_query (Optional[JsonQuery]): Query parameters
            for filtering shifts by JSON-based criteria.

        Returns:
            List[Shift]: A list of shifts matching the query parameters.
        """
        if not self.postgres_repository:
            raise ValueError("PostgresShiftRepository is not available")

        shifts = self.postgres_repository.get_shifts(
            user_query, date_query, text_query, json_query
        )
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
        metadata = self.postgres_repository.get_latest_metadata(shift_data.shift_id)
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

    def updated_shift_log_info(self, current_shift_id: int):
        """
        Update the shift log information based on new information from external data
        sources.

        :param current_shift_id int: The unique identifier of the current shift.
        :returns: The updated Shift object in JSON format and an HTTP status code.
        """
        shift_logs_info = {}
        current_shift_data = self.postgres_repository.get_shift(current_shift_id)
        current_shift_data = Shift.model_validate(current_shift_data)
        if current_shift_data.shift_logs.logs:
            for x in current_shift_data.shift_logs.logs:
                x = ShiftLogs.model_validate(x)
                if x.info["eb_id"] not in shift_logs_info:
                    shift_logs_info[x.info["eb_id"]] = x.info
                    shift_logs_info[x.info["eb_id"]]["log_time"] = x.log_time
                else:

                    if shift_logs_info[x.info["eb_id"]]["log_time"] < x.log_time:
                        shift_logs_info[x.info["eb_id"]] = x.info

            for k in shift_logs_info:
                del shift_logs_info[k]["log_time"]

        created_after_eb_sbi_info = self.postgres_repository.get_oda_data(
            filter_date=current_shift_data.shift_start.isoformat()
        )

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

            new_eb_ids_merged_set = set()
            new_eb_ids_merged_set.update(new_eb_ids)
            new_eb_ids_merged_set.update(changed_eb_ids)

            new_eb_ids_merged = list(new_eb_ids_merged_set)

            LOGGER.info("------>New or Modified EB found in ODA %s", new_eb_ids_merged)
            shift_lgs = Logs()
            shift_logs_array: List[ShiftLogs] = []
            if new_eb_ids_merged:
                for new_or_updated_eb_id in new_eb_ids_merged:
                    new_info = created_after_eb_sbi_info[new_or_updated_eb_id]
                    new_log = ShiftLogs(
                        info=new_info,
                        log_time=datetime.now(tz=timezone.utc),
                        source="ODA",
                    )
                    shift_logs_array.append(new_log)

                    # shift_lgs.logs = [ShiftLogs(
                    #     info=new_info, log_time=datetime.now(tz=timezone.utc), source="ODA"
                    # )]
                if current_shift_data.shift_logs:
                    shift_logs_array.extend(current_shift_data.shift_logs.logs)
                shift_lgs.logs = shift_logs_array
                metadata = self.postgres_repository.get_latest_metadata(
                    current_shift_id
                )

                updated_shift = Shift(shift_id=current_shift_id, shift_logs=shift_lgs)
                shift = update_metadata(
                    updated_shift,
                    metadata=metadata,
                    last_modified_by=current_shift_data.shift_operator,
                )

                updated_shift_with_info = self.postgres_repository.patch_shift(
                    shift=shift
                )
                LOGGER.info("------> Shift Logs have been updated successfully")
                LOGGER.info(updated_shift_with_info)
                return shift
            else:
                LOGGER.info("------> NO New Logs found in ODA")
                return "NO New Logs found in ODA"
        else:
            LOGGER.info("------> NO New Logs found in ODA")
            return "NO New Logs found in ODA"
