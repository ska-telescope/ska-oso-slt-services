"""
Pure functions which map from entities to SQL queries with parameters.

This module provides classes and functions to facilitate mapping between
entity objects and SQL queries, focusing on shift-related data.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Callable, Dict, Tuple, Union

from ska_oso_slt_services.models.shiftmodels import Shift

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
    metadata_map: dict
    metadata_map: Dict[str, Callable[[Shift], SqlTypes]] = MappingProxyType(
        {
            "created_on": lambda shift: shift.metadata.created_on,
            "created_by": lambda shift: shift.metadata.created_by,
            "last_modified_on": lambda shift: shift.metadata.last_modified_on,
            "last_modified_by": lambda shift: shift.metadata.last_modified_by,
        }
    )


class ModelEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling model objects with 'model_dump_json' method.
    """

    def default(self, obj: Any) -> Any:  # pylint: disable=W0237
        """
        Encode objects with 'model_dump_json' method or use default encoding.

        Args:
            obj (Any): The object to encode.

        Returns:
            Any: The JSON-encodable representation of the object.
        """
        if hasattr(obj, "model_dump_json"):
            return json.loads(obj.model_dump_json())
        return super().default(obj)


class ShiftLogMapping:
    """
    Provides mapping functionality for Shift objects
    to database operations.
    """

    @property
    def table_details(self) -> TableDetails:
        """
        Get the table details for the shift log.

        Returns:
            TableDetails: An object containing the table name,
            identifier field, and column mappings.
        """
        return TableDetails(
            table_name="tab_oda_slt",
            identifier_field="shift_id",
            column_map={
                "shift_id": lambda shift: shift.shift_id,
                "shift_start": lambda shift: shift.shift_start,
                "shift_end": lambda shift: shift.shift_end,
                "shift_operator": lambda shift: shift.shift_operator,
                "shift_logs": lambda shift: json.dumps(
                    shift.shift_logs, cls=ModelEncoder
                ),
                "annotations": lambda shift: shift.annotations,
                "comments": lambda shift: shift.comments,
            },
        )

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

    def get_params_with_metadata(self, shift) -> Tuple[SqlTypes]:
        """
        Get parameter values for a given shift, including metadata.

        Args:
            shift: The Shift object to extract parameters from.

        Returns:
            Tuple[SqlTypes]: A tuple containing
            parameter values for all columns and metadata fields.
        """
        return tuple(
            map_fn(shift) for map_fn in self.table_details.column_map.values()
        ) + tuple(map_fn(shift) for map_fn in self.table_details.metadata_map.values())
