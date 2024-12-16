from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import update_metadata
from ska_oso_slt_services.domain.shift_models import Media, Shift
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService


class MediaService(BaseRepositoryService):

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

        if isinstance(shift_model, dict):
            shift_model = Shift.model_validate(shift_model)

        stored_shift = shift_model
        stored_shift.metadata = metadata

        shift = update_metadata(
            entity=stored_shift,
            metadata=metadata,
        )
        result = self.postgres_repository.insert_shift_images(
            comment_id=comment_id,
            shift_comment=shift,
            files=files,
            shift_model=shift_model,
            table_mapping=table_mapping,
        )
        return result.image

    def post_media(self, file, shift_comment, table_mapping) -> Media:
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

        if isinstance(shift_comment, dict):
            shift_comment = Media.model_validate(shift_comment)

        result = self.postgres_repository.insert_shift_image(
            file=file, shift_comment=shift_comment, table_mapping=table_mapping
        )
        return result

    def get_media(self, comment_id, shift_model, table_mapping) -> list[Media]:
        """
        Get a media file from a shift.

        Args:
            comment_id (int): The ID of the comment to get the media from.
            shift_model: The model of the shift log.
            table_mapping: The Database Model Mapping Class.

        Returns:
            list[Media]: List of media files associated with the comment.
        """
        if isinstance(shift_model, dict):
            shift_model = Shift.model_validate(shift_model)

        media_list = self.postgres_repository.get_images(
            comment_id, shift_model, table_mapping
        )
        if not media_list:
            raise NotFoundError("No media found for the given comment ID")
        return media_list
