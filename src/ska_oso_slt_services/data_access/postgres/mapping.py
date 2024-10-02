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

from pydantic import BaseModel

from ska_oso_slt_services.domain.shift_models import Logs, Shift

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
    text_base_search_fields: str
    json_base_search_fields: str
    column_map: dict
    column_map_extra_keys: dict
    metadata_map: dict
    metadata_map: Dict[str, Callable[[Shift], SqlTypes]] = MappingProxyType(
        {
            "created_on": lambda shift: shift.metadata.created_on,
            "created_by": lambda shift: shift.metadata.created_by,
            "last_modified_on": lambda shift: shift.metadata.last_modified_on,
            "last_modified_by": lambda shift: shift.metadata.last_modified_by,
        }
    )


# First, let's create a mock serializer function
def mock_default_serializer(obj: Any) -> dict:
    if isinstance(obj, BaseModel):
        return obj.dict()
    elif isinstance(obj, (list, tuple)):
        return [mock_default_serializer(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: mock_default_serializer(value) for key, value in obj.items()}
    elif hasattr(obj, "__dict__"):
        return {
            key: mock_default_serializer(value) for key, value in obj.__dict__.items()
        }
    else:
        return obj


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
            text_base_search_fields="comments",
            json_base_search_fields="shift_logs",
            column_map={
                "shift_id": lambda shift: shift.shift_id,
                "shift_start": lambda shift: shift.shift_start,
                "shift_end": lambda shift: shift.shift_end,
                "shift_operator": lambda shift: shift.shift_operator,
                "annotations": lambda shift: shift.annotations,
                "comments": lambda shift: shift.comments,
            },
            column_map_extra_keys={
                "shift_logs": lambda shift: shift.shift_logs,
                "media": lambda shift: shift.media,
            },
        )

    def get_shift_log_columns(self) -> Tuple[str]:
        """
        Get a tuple of column names for media fields.

        Returns:
            Tuple[str]: A tuple containing column names for media fields.
        """
        return ["shift_logs"]

    def get_shift_log_params(self, shift) -> Tuple[SqlTypes]:
        """
        Get parameter values for media fields.

        Returns:
            Tuple[SqlTypes]: A tuple containing parameter values
            for media fields.
        """
        column_map_extra_keys = {
            "shift_logs": lambda shift: json.dumps(
                shift.shift_logs.model_dump(), default=str, indent=2
            ),
        }
        return tuple(map_fn(shift) for map_fn in column_map_extra_keys.values())

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

    def get_columns_with_metadata_with_extra_keys(self) -> Tuple[str]:
        """
        Get a tuple of column names including metadata fields.

        Returns:
            Tuple[str]: A tuple containing all column names and
            metadata field names.
        """
        return (
            tuple(self.table_details.column_map.keys())
            + tuple(self.table_details.metadata_map.keys())
            + tuple(self.table_details.column_map_extra_keys.keys())
        )

    def get_metadata_columns(self) -> Tuple[str]:
        """
        Get a tuple of column names including metadata fields.

        Returns:
            Tuple[str]: A tuple containing only metadata field names.
        """
        return tuple(self.table_details.metadata_map.keys())

    def get_metadata_params(self, shift) -> Tuple[SqlTypes]:
        """
        Get parameter values for metadata fields.

        Returns:
            Tuple[SqlTypes]: A tuple containing parameter values
            for all metadata fields.
        """
        return tuple(
            map_fn(shift) for map_fn in self.table_details.metadata_map.values()
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
