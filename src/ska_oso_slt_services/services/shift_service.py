import logging
from typing import List, Optional, Union

from ska_oso_slt_services.common.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import set_new_metadata, update_metadata
from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftComment,
    ShiftLogComment,
)
from ska_oso_slt_services.services.shift_annotation_service import ShiftAnnotations
from ska_oso_slt_services.services.shift_comments_service import ShiftComments
from ska_oso_slt_services.services.shift_logs_comment_service import ShiftLogsComments

LOGGER = logging.getLogger(__name__)


class ShiftService(ShiftComments, ShiftLogsComments, ShiftAnnotations):

    def merge_comments(self, shifts: List[dict]) -> Shift:
        """
        Merge comments into shift logs for the provided list of shifts.

        Args:
            shifts (List[dict]): List of shift data dictionaries.

        Returns:
            List[dict]: List of shift data with merged comments in shift logs.
        """

        for shift in shifts:
            shift_log_comments_dict = (
                self.crud_shift_repository.get_shift_logs_comments(
                    ShiftLogComment(), shift_id=shift["shift_id"]
                )
            )
            if shift.get("shift_logs"):
                for shift_log in shift["shift_logs"]:
                    shift_log["comments"] = []
                    for comment in shift_log_comments_dict:
                        if shift_log["info"]["eb_id"] == comment["eb_id"]:
                            shift_log["comments"].append(comment)
        return shifts

    def merge_shift_comments(self, shifts: Shift) -> Shift:
        """
        Merge shift comments into the provided list of shifts.

        Args:
            shifts (List[dict]): List of shift data dictionaries.

        Returns:
            List[dict]: List of shift data with merged shift comments.
        """
        for shift in shifts:
            shift_comment_dict = self.crud_shift_repository.get_shift_logs_comments(
                ShiftComment(), shift_id=shift["shift_id"]
            )
            shift["comments"] = shift_comment_dict

        return shifts

    def merge_shift_annotations(self, shifts: Shift) -> Shift:
        """
        Merge shift annotations into the provided list of shifts.

        Args:
            shifts (List[dict]): List of shift data dictionaries.

        Returns:
            List[dict]: List of shift data with merged shift annotations.
        """
        for shift in shifts:
            shift["annotations"] = self.crud_shift_repository.get_shift_annotations(
                shift_id=shift["shift_id"]
            )

        return shifts

    def get_shift(self, shift_id: str) -> Shift:
        """
        Retrieve a shift by its ID.

        Args:
            shift_id (str): The ID of the shift to retrieve.

        Returns:
            Shift: The shift data if found, None otherwise.
        """
        shift = self.crud_shift_repository.get_shift(shift_id)

        if shift:
            shifts_with_log_comments = self.merge_comments([shift])[0]
            shifts_with_comments_and_log_comments = self.merge_shift_comments(
                [shifts_with_log_comments]
            )[0]

            shifts_with_annotations = self.merge_shift_annotations([shift])[0]

            prepare_comment_with_metadata = []
            prepare_annotation_with_metadata = []
            if shift.get("comments"):
                for comment in shift["comments"]:
                    prepare_comment_with_metadata.append(
                        self._prepare_entity_with_metadata(comment, model=ShiftComment)
                    )

            if shift.get("annotations"):
                for annotation in shift["annotations"]:
                    prepare_annotation_with_metadata.append(
                        self._prepare_entity_with_metadata(
                            entity=annotation, model=ShiftAnnotation
                        )
                    )

            per_eb_comment_metadata = []
            if shift.get("shift_logs"):
                for shift_log in shift["shift_logs"]:  # per_eb
                    prepare_log_comment_with_metadata = []
                    for comment in shift_log["comments"]:
                        prepare_log_comment_with_metadata.append(
                            self._prepare_entity_with_metadata(
                                comment, model=ShiftLogComment
                            )
                        )
                    per_eb_comment_metadata.append(prepare_log_comment_with_metadata)

            shift_with_metadata = self._prepare_entity_with_metadata(
                shifts_with_comments_and_log_comments, model=Shift
            )

            shift_with_metadata = self._prepare_entity_with_metadata(
                entity=shifts_with_annotations, model=Shift
            )

            shift_with_metadata.comments = prepare_comment_with_metadata
            shift_with_metadata.annotations = prepare_annotation_with_metadata
            if shift_with_metadata.shift_logs and per_eb_comment_metadata:
                for i, shift_log in enumerate(
                    shift_with_metadata.shift_logs
                ):  # shift_log obj

                    shift_log.comments = per_eb_comment_metadata[i]
            return shift_with_metadata
        else:
            raise NotFoundError(f"No shift found with ID: {shift_id}")

    def get_shifts(
        self,
        shift: Optional[Shift] = None,
        match_type: Optional[MatchType] = None,
        status: Optional[SbiEntityStatus] = None,
        entities: Optional[EntityFilter] = None,
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
        shifts = self.crud_shift_repository.get_shifts(
            shift, match_type, status, entities
        )
        if not shifts:
            raise NotFoundError("No shifts found for the given query.")
        LOGGER.info("Shifts: %s", shifts)
        prepared_shifts = []
        for shift in shifts:
            shifts_with_log_comments = self.merge_comments([shift])[0]
            shifts_with_comments_and_log_comments = self.merge_shift_comments(
                [shifts_with_log_comments]
            )[0]
            shifts_with_annotations = self.merge_shift_annotations([shift])[0]
            prepare_comment_with_metadata = []
            prepare_annotation_with_metadata = []

            if shift.get("comments"):
                for comment in shift["comments"]:
                    prepare_comment_with_metadata.append(
                        self._prepare_entity_with_metadata(
                            entity=comment, model=ShiftComment
                        )
                    )
            if shift.get("annotations"):
                for annotation in shift["annotations"]:
                    prepare_annotation_with_metadata.append(
                        self._prepare_entity_with_metadata(
                            entity=annotation, model=ShiftAnnotation
                        )
                    )
            per_eb_comment_metadata = []
            if shift.get("shift_logs"):
                for shift_log in shift["shift_logs"]:  # per_eb
                    prepare_log_comment_with_metadata = []
                    for comment in shift_log["comments"]:
                        prepare_log_comment_with_metadata.append(
                            self._prepare_entity_with_metadata(
                                entity=comment, model=ShiftLogComment
                            )
                        )
                    per_eb_comment_metadata.append(prepare_log_comment_with_metadata)

            shift_with_metadata = self._prepare_entity_with_metadata(
                entity=shifts_with_comments_and_log_comments, model=Shift
            )
            shift_with_metadata = self._prepare_entity_with_metadata(
                entity=shifts_with_annotations, model=Shift
            )
            shift_with_metadata.comments = prepare_comment_with_metadata
            shift_with_metadata.annotations = prepare_annotation_with_metadata

            if shift_with_metadata.shift_logs and per_eb_comment_metadata:
                for i, shift_log in enumerate(
                    shift_with_metadata.shift_logs
                ):  # shift_log obj
                    shift_log.comments = per_eb_comment_metadata[i]

            prepared_shifts.append(shift_with_metadata)
        return prepared_shifts

    def create_shift(self, shift_data: Shift) -> Shift:
        """
        Create a new shift.

        Args:
            shift_data (Shift): A shift object for create shift.

        Returns:
            Shift: The created shift data.
        """
        shift = set_new_metadata(shift_data, created_by=shift_data.shift_operator)
        return self.crud_shift_repository.create_shift(shift)

    def update_shift_end_time(self, shift_id: str, shift_data: Shift) -> Shift:
        """
        Update the end time of a shift.

        Args:
            shift_id (str): A shift id to update shift end.
            shift_data (Shift): A shift object for update shift end.

        Returns:
            Shift: The updated shift data.
        """
        shift_data.shift_id = shift_id

        metadata = self.crud_shift_repository.get_entity_metadata(shift_id)

        if not metadata:

            raise NotFoundError(f"No Shift found with ID: {shift_id}")

        shift = update_metadata(
            shift_data, metadata=metadata, last_modified_by=shift_data.shift_operator
        )

        return self.crud_shift_repository.update_shift_end_time(shift)

    def update_shift(self, shift_id: str, shift_data: Shift) -> Shift:
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

        metadata = self.crud_shift_repository.get_entity_metadata(shift_data.shift_id)
        if not metadata:
            raise NotFoundError(f"No shift found with ID: {shift_data.shift_id}")
        shift = update_metadata(
            shift_data, metadata=metadata, last_modified_by=shift_data.shift_operator
        )
        updated_shift = self.crud_shift_repository.update_shift(shift)
        shift_with_metadata = self._prepare_entity_with_metadata(
            entity=updated_shift, model=Shift
        )
        return shift_with_metadata

    def delete_shift(self, shift_id):
        """
        Delete a shift by its shift_id.

        Args:
            shift_id (str): The ID of the shift to delete.
        """
        self.crud_shift_repository.delete_shift(shift_id)

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
        if not self.crud_shift_repository:
            raise ValueError("PostgresShiftRepository is not available")

        shift = self.crud_shift_repository.get_current_shift()
        if shift:
            return self.get_shift(shift_id=shift["shift_id"])
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
        return self.crud_shift_repository.updated_shift_log_info(current_shift_id)
