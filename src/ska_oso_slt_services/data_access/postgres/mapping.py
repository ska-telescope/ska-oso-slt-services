"""
Pure functions which map from entities to SQL queries with parameters.

This module provides classes and functions to facilitate mapping between
entity objects and SQL queries, focusing on shift-related data.
"""

import json
from datetime import datetime
from typing import Optional, Tuple, Union

from ska_oso_slt_services.data_access.postgres.base_mapping import (
    BaseMapping,
    TableDetails,
)
from ska_oso_slt_services.domain.shift_models import (
    Shift,
    ShiftAnnotation,
    ShiftComment,
    ShiftLogComment,
)

SqlTypes = Union[str, int, datetime]


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


class ShiftLogMapping(BaseMapping[Shift]):
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
                "shift_logs": lambda shift: _field_json_dump(shift, "shift_logs"),
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
            "shift_logs": lambda shift: _field_json_dump(shift, "shift_logs"),
        }
        return tuple(map_fn(shift) for map_fn in column_map_extra_keys.values())


class ShiftLogCommentMapping(BaseMapping[ShiftLogComment]):
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
        )


class ShiftCommentMapping(BaseMapping[ShiftComment]):
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
            table_name="tab_oda_slt_shift_comments",
            identifier_field="id",
            column_map={
                "comment": lambda comment: comment.comment,
                "operator_name": lambda comment: comment.operator_name,
                "shift_id": lambda comment: comment.shift_id,
                "image": lambda comment: _field_json_dump(comment, "image"),
            },
        )


class ShiftAnnotationMapping(BaseMapping[ShiftAnnotation]):
    """
    Provides mapping functionality for Shift Annotation object
    to database operations.
    """

    @property
    def table_details(self) -> TableDetails:
        """
        Get the table details for shift annotations.

        Returns:
            AnnotationTableDetails: An object containing the table name,
            identifier field, and column mappings.
        """
        return TableDetails(
            table_name="tab_oda_slt_shift_annotations",
            identifier_field="id",
            column_map={
                "annotation": lambda annotation: annotation.annotation,
                "user_name": lambda annotation: annotation.user_name,
                "shift_id": lambda annotation: annotation.shift_id,
            },
        )
