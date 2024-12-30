import logging
from typing import Any, List

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import (
    get_latest_metadata,
    set_new_metadata,
    update_metadata,
)
from ska_oso_slt_services.data_access.postgres.mapping import ShiftCommentMapping
from ska_oso_slt_services.domain.shift_models import Media, ShiftComment
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService
from ska_oso_slt_services.services.media_service import MediaService

LOGGER = logging.getLogger(__name__)


class ShiftComments(MediaService, BaseRepositoryService):

    def create_shift_comment(self, shift_comment_data: ShiftComment) -> ShiftComment:
        """
        Create a new comment for a shift with metadata.

        Args:
            shift_comment_data: The comment data for the shift.

        Returns:
            ShiftComment: The created shift comment.
        """
        if not shift_comment_data.shift_id:
            raise ValueError("Shift id is required")

        shift = self.get_shift(shift_comment_data.shift_id)
        if not shift:
            raise NotFoundError(
                f"No shift found with id: {shift_comment_data.shift_id}"
            )

        shift_comment = set_new_metadata(shift_comment_data, shift.shift_operator)
        return self.crud_shift_repository.create_shift_comment(
            shift_comment=shift_comment
        )

    def get_shift_comments(self, shift_id: str = None) -> List[ShiftComment]:
        """
        Retrieve comments for shift based on shift ID.

        Args:
            shift_id (str, optional): The shift ID for filtering comments.

        Returns:
            List[ShiftComment]: List of comments matching the specified query.

        Raises:
            NotFoundError: If no comments are found for the given filters.
        """
        shift_comments = self.crud_shift_repository.get_shift_comments(
            shift_id=shift_id
        )
        if not shift_comments:
            raise NotFoundError("No shifts comments found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_comments)

        shift_comments_obj_with_metadata = []
        for shift_comment in shift_comments:
            shift_comment_with_metadata = self._prepare_entity_with_metadata(
                entity=shift_comment, model=ShiftComment
            )
            shift_comments_obj_with_metadata.append(shift_comment_with_metadata)

        return shift_comments_obj_with_metadata

    def get_shift_comment(self, comment_id: int = None) -> List[ShiftComment]:
        """
        Retrieve comments for shift based on comment ID.

        Args:
            comment_id (int, optional): The comment ID for filtering comments.

        Returns:
            List[ShiftComment]: List of comments matching the specified query.

        Raises:
            NotFoundError: If no comments are found for the given filters.
        """
        shift_comment = self.crud_shift_repository.get_shift_comment(
            comment_id=comment_id
        )
        if not shift_comment:
            raise NotFoundError("No shift comment found for the given query.")
        LOGGER.info("Shift log comments : %s", shift_comment)

        shift_comment_with_metadata = self._prepare_entity_with_metadata(
            shift_comment, ShiftComment()
        )

        return shift_comment_with_metadata

    def update_shift_comments(self, comment_id: int, shift_comment: ShiftComment):
        """
        Update an existing shift comment with new data.

        Args:
            comment_id (int): The ID of the comment to update.
            shift_comment (ShiftComment): The updated comment data.

        Returns:
            ShiftComment: The updated shift comment.

        Raises:
            NotFoundError: If no comment is found with the provided ID.
        """
        # for getting shift_id to get operator name
        existing_shift_comment = self.get_shift_comment(comment_id=comment_id)

        if not existing_shift_comment:
            raise NotFoundError(f"No comment found with id: {comment_id}")

        shift = self.get_shift(existing_shift_comment.shift_id)
        if not shift:
            raise NotFoundError(f"No shift found with id: {shift_comment['shift_id']}")

        metadata = self.crud_shift_repository.get_entity_metadata(
            entity_id=comment_id, model=shift_comment
        )
        if not metadata:
            raise NotFoundError(f"No Comment found with ID: {comment_id}")

        shift_log_comment_with_metadata = update_metadata(
            entity=shift_comment,
            metadata=metadata,
            last_modified_by=shift.shift_operator,
        )
        updated_comment = self.crud_shift_repository.update_shift_comments(
            comment_id, shift_log_comment_with_metadata
        )
        return self._prepare_entity_with_metadata(updated_comment, ShiftComment())

    def add_media_to_comment(self, comment_id: id, files: Any, shift_model: Any):
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
            table_mapping=ShiftCommentMapping(),
        )

    def get_media_for_comment(self, comment_id: int, shift_model: Any) -> list[Media]:
        """
        Get a media file from a shift.

        Args:
            comment_id (int): The ID of the comment to get the media from.
            shift_model: The model of the shift log.

        Returns:
            file: The requested media file.
        """
        return self.crud_shift_repository.get_media(comment_id, shift_model)

    def create_media_for_comment(
        self, shift_id: int, shift_operator: str, file: Any, shift_model: Any
    ):
        """
        Create a media file for a shift.

        Args:
            shift_id (int): The ID of the shift to add the media to.
            shift_operator (str): The operator of the shift.
            file (files): The media file to add.
            shift_model: The model of the shift log.

        Returns:
            Shift: The updated shift with the added media.
        """
        shift = self.get_shift(shift_id)
        if not shift:
            raise NotFoundError(f"No shift found with id: {shift_id}")

        shift_comment = shift_model(shift_id=shift_id, operator_name=shift_operator)

        shift_comment = set_new_metadata(shift_comment, shift_operator)
        return self.post_media(file=file, shift_comment=shift_comment)
