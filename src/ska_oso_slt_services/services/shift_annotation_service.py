import logging
from typing import List

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.common.metadata_mixin import set_new_metadata
from ska_oso_slt_services.data_access.postgres.mapping import ShiftAnnotationMapping
from ska_oso_slt_services.domain.shift_models import ShiftAnnotation
from ska_oso_slt_services.services.base_repository_service import BaseRepositoryService

LOGGER = logging.getLogger(__name__)


class ShiftAnnotations(BaseRepositoryService):

    def create_shift_annotation(
        self, shift_annotation_data: ShiftAnnotation
    ) -> ShiftAnnotation:
        """
        Create a new annotation for a shift with metadata.

        Args:
            shift_annotation_data: The annotation data for the shift.

        Returns:
            ShiftAnnotation: The created shift annotation.
        """

        if not shift_annotation_data.shift_id:
            raise ValueError("Shift id is required")

        shift = self.get_shift(shift_annotation_data.shift_id)
        if not shift:
            raise NotFoundError(
                f"No shift found with ID: {shift_annotation_data.shift_id}"
            )

        shift_annotation = set_new_metadata(shift_annotation_data, shift.shift_operator)
        return self.crud_shift_repository.create_shift_annotation(
            shift_annotation=shift_annotation
        )

    def get_shift_annotations(self, shift_id: str = None) -> List[ShiftAnnotation]:
        """
        Retrieve annotation for shift based on shift ID.

        Args:
            shift_id (str, optional): The shift ID for filtering annotation.

        Returns:
            List[ShiftAnnotation]: List of annotation matching the specified query.

        Raises:
            NotFoundError: If no annotation are found for the given filters.
        """

        shift_annotations = self.crud_shift_repository.get_shift_annotations(
            shift_id=shift_id
        )
        if not shift_annotations:
            raise NotFoundError("No Shift annotations found for the given query.")
        LOGGER.info("Shift annotations : %s", shift_annotations)

        shift_annotations_obj_with_metadata = []
        for shift_annotation in shift_annotations:
            shift_annotation_with_metadata = self._prepare_shift_common_with_metadata(
                shift_data=shift_annotation, shift_model=ShiftAnnotation
            )
            shift_annotations_obj_with_metadata.append(shift_annotation_with_metadata)

        return shift_annotations_obj_with_metadata

    def get_shift_annotation(self, annotation_id: int = None) -> List[ShiftAnnotation]:
        """
        Retrieve annotations for shift based on annotation ID.

        Args:
            annotation_id (int, optional): The annotation ID for filtering annotations.

        Returns:
            List[ShiftAnnotation]: List of annotations matching the specified query.

        Raises:
            NotFoundError: If no annotations are found for the given filters.
        """
        shift_annotation = self.crud_shift_repository.get_shift_annotation(
            annotation_id=annotation_id, table_mapping=ShiftAnnotationMapping()
        )
        if not shift_annotation:
            raise NotFoundError("No Shift annotation found for the given query.")
        LOGGER.info("Shift annotations : %s", shift_annotation)

        shift_annotation_with_metadata = self._prepare_shift_common_with_metadata(
            shift_annotation, shift_model=ShiftAnnotation
        )

        return shift_annotation_with_metadata
