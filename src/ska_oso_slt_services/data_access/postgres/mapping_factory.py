"""Factory module for creating database table mappings.

This module provides functionality for mapping between domain entities and database tables
through the TableMappingFactory class. It handles various types of shift-related entities
and their corresponding database mappings.
"""

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
    Shift,
    ShiftAnnotation,
    ShiftBaseClass,
    ShiftComment,
    ShiftLogComment,
)


class MappingType(Enum):
    """Enumeration of supported mapping types for different shift-related entities.

    This enum defines the various types of mappings that can be created by the factory,
    corresponding to different types of shift-related database tables.
    """

    SHIFT = auto()
    SHIFT_BASE_CLASS = auto()
    SHIFT_LOG_COMMENT = auto()
    SHIFT_COMMENT = auto()
    SHIFT_ANNOTATION = auto()


class TableMappingFactory:
    """Factory class for creating database table mappings.

    This class provides methods to create appropriate mapping objects for different
    types of shift-related entities. It handles the mapping between domain entities
    and their database table representations.
    """

    @staticmethod
    def _get_mapping_type(
        entity: Union[
            Type[
                Union[
                    Shift,
                    ShiftBaseClass,
                    ShiftLogComment,
                    ShiftComment,
                    ShiftAnnotation,
                ]
            ],
            Union[
                Shift, ShiftBaseClass, ShiftLogComment, ShiftComment, ShiftAnnotation
            ],
        ],
    ) -> MappingType:
        """Determine the mapping type for a given entity.

        Args:
            entity: Either a class type or instance of a shift-related entity.

        Returns:
            MappingType: The appropriate mapping type for the entity.

        Raises:
            ValueError: If the entity type is not supported.
        """
        mapping_types = {
            Shift: MappingType.SHIFT,
            ShiftBaseClass: MappingType.SHIFT_BASE_CLASS,
            ShiftLogComment: MappingType.SHIFT_LOG_COMMENT,
            ShiftComment: MappingType.SHIFT_COMMENT,
            ShiftAnnotation: MappingType.SHIFT_ANNOTATION,
        }

        entity_type = entity if isinstance(entity, type) else type(entity)
        if entity_type in mapping_types:
            return mapping_types[entity_type]

        raise ValueError(f"Unsupported entity type: {entity_type.__name__}")

    @staticmethod
    def _get_mapping_class(mapping_type: MappingType) -> Type[BaseMapping]:
        """Get the mapping class for a given mapping type.

        Args:
            mapping_type: The type of mapping for which to get the class.

        Returns:
            Type[BaseMapping]: The appropriate mapping class.

        Raises:
            ValueError: If the mapping type is not supported.
        """
        mapping_classes = {
            MappingType.SHIFT: ShiftLogMapping,
            MappingType.SHIFT_BASE_CLASS: ShiftLogMapping,  # Uses same mapping as SHIFT
            MappingType.SHIFT_LOG_COMMENT: ShiftLogCommentMapping,
            MappingType.SHIFT_COMMENT: ShiftCommentMapping,
            MappingType.SHIFT_ANNOTATION: ShiftAnnotationMapping,
        }

        if mapping_type not in mapping_classes:
            raise ValueError(f"Unsupported mapping type: {mapping_type}")

        return mapping_classes[mapping_type]

    @staticmethod
    def create_mapping(
        entity: Union[
            Type[
                Union[
                    Shift,
                    ShiftBaseClass,
                    ShiftLogComment,
                    ShiftComment,
                    ShiftAnnotation,
                ]
            ],
            Union[
                Shift, ShiftBaseClass, ShiftLogComment, ShiftComment, ShiftAnnotation
            ],
        ],
    ) -> BaseMapping:
        """Create a mapping instance for the given entity.

        This method determines the appropriate mapping type for the given entity and creates
        an instance of the corresponding mapping class.

        Args:
            entity: Either a class type or instance of a shift-related entity
                   for which to create a mapping.

        Returns:
            BaseMapping: An instance of the appropriate mapping class for the entity.

        Raises:
            ValueError: If the entity type is not supported.
        """
        mapping_type = TableMappingFactory._get_mapping_type(entity)
        mapping_class = TableMappingFactory._get_mapping_class(mapping_type)
        return mapping_class()
