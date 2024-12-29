"""Base mapping class for database operations."""
from typing import Tuple, TypeVar, Generic, Union,  Dict, Optional, Callable
from ska_oso_slt_services.domain.shift_models import Shift, ShiftComment, ShiftLogComment


from types import MappingProxyType
from dataclasses import dataclass

from datetime import datetime

SqlTypes = Union[str, int, datetime]


@dataclass
class TableDetails:
    """
    Represents the details of a database table and its mapping
    to a Shift object.

    Attributes:
        table_name (str): The name of the database table.
        identifier_field (str): The primary identifier field of the table.
        column_map (dict): Mapping of table columns to Shift object attributes.
        metadata_map (Dict[str, Callable[[Shift], SqlTypes]]):
        Mapping of metadata fields to their respective getter functions.
    """

    table_name: str
    identifier_field: str
    column_map: dict
    text_base_search_fields: Optional[str] = None
    metadata_map: Dict[str, Callable[[Shift,ShiftComment, ShiftLogComment], SqlTypes]] = MappingProxyType(
        {
            "created_on": lambda shift: shift.metadata.created_on,
            "created_by": lambda shift: shift.metadata.created_by,
            "last_modified_on": lambda shift: shift.metadata.last_modified_on,
            "last_modified_by": lambda shift: shift.metadata.last_modified_by,
        }
    )

T = TypeVar('T')

class BaseMapping(Generic[T]):
    """
    Base mapping class providing common mapping functionality
    for database operations.
    """

    @property
    def table_details(self)->TableDetails:
        """
        Get the table details. Must be implemented by subclasses.

        Returns:
            TableDetails: An object containing the table name,
            identifier field, and column mappings.
        """
        raise NotImplementedError
    
    def get_columns_with_metadata(self) -> Tuple[str]:
        """
        Get a tuple of column names including metadata fields.

        Returns:
            Tuple[str]: A tuple containing all column names and
            metadata field names.
        """
        return tuple(self.table_details.column_map.keys()) + tuple(
            self.table_details.metadata_map.keys()
        )

    def get_metadata_columns(self) -> Tuple[str]:
        """
        Get a tuple of column names including metadata fields.

        Returns:
            Tuple[str]: A tuple containing only metadata field names.
        """
        return tuple(self.table_details.metadata_map.keys())

    def get_metadata_params(self, obj: T) -> Tuple[SqlTypes]:
        """
        Get parameter values for metadata fields.

        Args:
            obj: The object to extract parameters from.

        Returns:
            Tuple[SqlTypes]: A tuple containing parameter values
            for all metadata fields.
        """
        return tuple(
            map_fn(obj) for map_fn in self.table_details.metadata_map.values()
        )

    def get_params_with_metadata(self, obj: T) -> Tuple[SqlTypes]:
        """
        Get parameter values for a given object, including metadata.

        Args:
            obj: The object to extract parameters from.

        Returns:
            Tuple[SqlTypes]: A tuple containing
            parameter values for all columns and metadata fields.
        """
        return tuple(
            map_fn(obj) for map_fn in self.table_details.column_map.values()
        ) + tuple(map_fn(obj) for map_fn in self.table_details.metadata_map.values())