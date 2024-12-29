"""Factory class for creating table mappings."""

from enum import Enum, auto
from typing import Type, Union

from ska_oso_slt_services.data_access.postgres.base_mapping import BaseMapping
from ska_oso_slt_services.data_access.postgres.mapping import (
    ShiftAnnotationMapping,
    ShiftCommentMapping,
    ShiftLogCommentMapping,
    ShiftLogMapping,
)
from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftBaseClass,
    ShiftComment,
    ShiftLogComment,
    ShiftLogs,
)


class MappingType(Enum):
    """Enum for different types of mappings."""

    SHIFT = auto()
    SHIFT_BASE_CLASS = auto()
    SHIFT_LOG_COMMENT = auto()
    SHIFT_COMMENT = auto()
    SHIFT_ANNOTATION = auto()


class TableMappingFactory:
    """Factory class for creating table mappings."""

    @staticmethod
    def _get_mapping_type(
        entity: Union[Shift, ShiftLogComment, ShiftComment, ShiftAnnotation],
    ) -> MappingType:
        """Get the mapping type for an entity.

        Args:
            entity: Entity to get mapping type for.

        Returns:
            MappingType: The mapping type for the entity.

        Raises:
            ValueError: If the entity type is not supported.
        """
        if isinstance(entity, Shift):
            return MappingType.SHIFT
        if isinstance(entity, Shift):
            return MappingType.SHIFT_BASE_CLASS
        elif isinstance(entity, ShiftLogComment):
            return MappingType.SHIFT_LOG_COMMENT
        elif isinstance(entity, ShiftComment):
            return MappingType.SHIFT_COMMENT
        elif isinstance(entity, ShiftAnnotation):
            return MappingType.SHIFT_ANNOTATION
        else:
            raise ValueError(f"Unsupported entity type: {type(entity)}")

    @staticmethod
    def get_mapping_class(mapping_type: MappingType) -> Type[BaseMapping]:
        """Get the mapping class for a mapping type.

        Args:
            mapping_type: Type of mapping to get class for.

        Returns:
            Type[BaseMapping]: The mapping class.

        Raises:
            ValueError: If the mapping type is not supported.
        """
        mapping_classes = {
            MappingType.SHIFT: ShiftLogMapping(),
            MappingType.SHIFT_BASE_CLASS: ShiftLogMapping(),
            MappingType.SHIFT_LOG_COMMENT: ShiftLogCommentMapping(),
            MappingType.SHIFT_COMMENT: ShiftCommentMapping(),
            MappingType.SHIFT_ANNOTATION: ShiftAnnotationMapping(),
        }

        if mapping_type not in mapping_classes:
            raise ValueError(f"Unsupported mapping type: {mapping_type}")

        return mapping_classes[mapping_type]
