
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService
from ska_oso_slt_services.domain.shift_models import (
    Media,
    Shift
)
from ska_oso_slt_services.common.metadata_mixin import set_new_metadata, update_metadata
from ska_oso_slt_services.common.error_handling import NotFoundError

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

        stored_shift = shift_model(id=comment_id)

        stored_shift.metadata = metadata

        shift = update_metadata(
            entity=stored_shift,
            metadata=metadata,
        )
        result = self.postgres_repository.add_media(
            comment_id=comment_id,
            shift_comment=shift,
            files=files,
            shift_model=shift_model,
            table_mapping=table_mapping,
        )
        return result.image

    def get_media(self, shift_id: int) -> Media:
        """
        Retrieve media information for a given shift.

        Args:
            shift_id (int): The ID of the shift for which media information is requested.

        Returns:
            Media: The media information for the specified shift.

        Raises:
            NotFoundError: If the shift is not found.
        """
        shift = self.postgres_repository.get_shifts(Shift(shift_id=shift_id))
        if not shift:
            raise NotFoundError("Shift not found")
        media = Media(
            shift_id=shift_id,
            shift_log_id=shift.shift_log_id,
            shift_log_url=shift.shift_log_url,
            shift_log_status=shift.shift_log_status,
            sbi_status=shift.sbi_status,
        )
        return media
    
    def post_media(
        self, file, shift_comment, table_mapping
    ) -> Media:
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
            file: The requested media file.
        """
        return self.postgres_repository.get_media(
            comment_id, shift_model, table_mapping
        )