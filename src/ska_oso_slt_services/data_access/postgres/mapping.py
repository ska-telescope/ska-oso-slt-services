"""
Pure functions which map from entities to SQL queries with parameters.

This module provides classes and functions to facilitate mapping between
entity objects and SQL queries, focusing on shift-related data.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Callable, Dict, Optional, Tuple, Union

from ska_oso_slt_services.domain.shift_models import Shift

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
    column_map_extra_keys: dict
    text_base_search_fields: Optional[str] = None
    metadata_map: Dict[str, Callable[[Shift], SqlTypes]] = MappingProxyType(
        {
            "created_on": lambda shift: shift.metadata.created_on,
            "created_by": lambda shift: shift.metadata.created_by,
            "last_modified_on": lambda shift: shift.metadata.last_modified_on,
            "last_modified_by": lambda shift: shift.metadata.last_modified_by,
        }
    )


def _field_json_dump(shift: Shift, field: str) -> Optional[str]:
    """
    Helper function to dump a field value as a JSON string.

    Args:
        shift (Shift): The Shift object.
        field (str): The field name to dump.

    Returns:
        Optional[str]: The JSON-dumped field value, or None if the field is not set.
    """
    shift_dict = shift.model_dump(exclude_unset=True)

    field_value = shift_dict.get(field, None)
    if field_value is None:
        return None

    return json.dumps(field_value, default=str, indent=2)


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
            column_map={
                "shift_id": lambda shift: shift.shift_id,
                "shift_start": lambda shift: shift.shift_start,
                "shift_end": lambda shift: shift.shift_end,
                "shift_operator": lambda shift: shift.shift_operator,
                "annotations": lambda shift: shift.annotations,
                "shift_logs": lambda shift: _field_json_dump(shift, "shift_logs"),
            },
            column_map_extra_keys={"shift_logs": lambda shift: shift.shift_logs},
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


class ShiftLogCommentMapping:
    """
    Provides mapping functionality for Shift Log Comment object
    to database operations.
    """

    @property
    def table_details(self) -> TableDetails:
        """
        Get the table details for shift comments.

        Returns:
            CommentTableDetails: An object containing the table name,
            identifier field, and column mappings.
        """
        return TableDetails(
            table_name="tab_oda_slt_shift_log_comments",
            identifier_field="id",
            column_map={
                "log_comment": lambda comment: comment.log_comment,
                "operator_name": lambda comment: comment.operator_name,
                "shift_id": lambda comment: comment.shift_id,
                "image": lambda comment: _field_json_dump(comment, "image"),
                "eb_id": lambda comment: comment.eb_id,
            },
            column_map_extra_keys={},
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


class ShiftCommentMapping:
    """
    Provides mapping functionality for Shift Comment object
    to database operations.
    """

    @property
    def table_details(self) -> TableDetails:
        """
        Get the table details for shift comments.

        Returns:
            CommentTableDetails: An object containing the table name,
            identifier field, and column mappings.
        """
        return TableDetails(
            table_name="tab_slt_comments",
            identifier_field="id",
            column_map={
                "comment": lambda comment: _field_json_dump(comment, "comment"),
                "operator_name": lambda comment: comment.operator_name,
                "shift_id": lambda comment: comment.shift_id,
                "image": lambda comment: _field_json_dump(comment, "image"),
            },
            column_map_extra_keys={},
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
