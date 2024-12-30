import logging
from typing import List

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import (
    get_latest_metadata,
    set_new_metadata,
    update_metadata,
)
from ska_oso_slt_services.data_access.postgres.mapping import ShiftLogCommentMapping
from ska_oso_slt_services.domain.shift_models import Shift, ShiftLogComment
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService
from ska_oso_slt_services.services.media_service import MediaService

LOGGER = logging.getLogger(__name__)


class ShiftLogsComments(MediaService, BaseRepositoryService):

    def create_shift_logs_comment(self, shift_log_comment_data) -> ShiftLogComment:
        """
        Create a new comment for a shift log with metadata.

        Args:
            shift_log_comment_data: The comment data for the shift log.

        Returns:
            ShiftLogComment: The created shift log comment.
        """
        shift = self.crud_shift_repository.get_shift(
            shift_id=shift_log_comment_data.shift_id
        )
        shift = Shift(**shift)
        if not shift:
            raise NotFoundError(f"Shift not found {shift_log_comment_data.shift_id}")
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
        return self.crud_shift_repository.create_shift_logs_comment(
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
        shift_log_comments = self.crud_shift_repository.get_shift_logs_comments(
            ShiftLogComment(), shift_id=shift_id, eb_id=eb_id
        )
        if not shift_log_comments:
            raise NotFoundError("No shifts log comments found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_log_comments)

        shift_log_comments_obj_with_metadata = []
        for shift_log_comment in shift_log_comments:
            shift_log_comment_with_metadata = get_latest_metadata(
                entity=shift_log_comment, model=ShiftLogComment
            )
            shift_log_comments_obj_with_metadata.append(shift_log_comment_with_metadata)

        return shift_log_comments_obj_with_metadata

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
        metadata = self.crud_shift_repository.get_entity_metadata(
            entity_id=comment_id, table_details=ShiftLogCommentMapping()
        )
        if not metadata:
            raise NotFoundError(f"No Comment found with ID: {comment_id}")

        shift_log_comment_with_metadata = update_metadata(
            entity=shift_log_comment,
            metadata=metadata,
            last_modified_by=shift_log_comment.operator_name,
        )

        return self.crud_shift_repository.update_shift_logs_comments(
            comment_id, shift_log_comment_with_metadata
        )

    def create_shift_log_media(
        self, shift_id, shift_operator, file, eb_id, shift_model
    ):
        """
        Create a media file for a shift.

        Args:
            shift_id (int): The ID of the shift to add the media to.
            shift_operator (str): The operator of the shift.
            file (files): The media file to add.
            eb_id (str): The EB ID of the shift.
            shift_model: The model of the shift log.

        Returns:
            Shift: The updated shift with the added media.
        """
        shift = self.get_shift(shift_id)
        if not shift:
            raise NotFoundError(f"No shift found with id: {shift_id}")

        shift_comment = shift_model(shift_id=shift_id, operator_name=shift_operator)

        shift_comment.eb_id = eb_id
        shift_comment = set_new_metadata(shift_comment, shift_operator)

        return self.post_media(file=file, shift_comment=shift_comment)

    def get_shift_log_media(self, comment_id):
        """
        Get a media file from a shift.

        Args:
            comment_id (int): The ID of the comment to get the media from.

        Returns:
            file: The requested media file.
        """
        return self.crud_shift_repository.get_media(
            comment_id,
            table_model=ShiftLogComment,
        )

    def update_shift_log_with_image(self, comment_id, files, shift_model):
        """
        Add a media file to a shift.

        Args:
            comment_id (int): The ID of the comment to add the media to.
            files (files): The media files to add.
            shift_model: The model of the shift log.

        Returns:
            Shift: The updated comment with the added media.
        """
        return self.add_media(
            comment_id=comment_id,
            files=files,
            shift_model=shift_model,
            table_mapping=ShiftLogCommentMapping(),
        )
