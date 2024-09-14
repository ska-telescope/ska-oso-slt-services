"""
Pure functions which map from entities to SQL queries with parameteres
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
    table_name: str
    identifier_field: str
    column_map: dict
    metadata_map: dict
    metadata_map: Dict[str, Callable[[Shift], SqlTypes]] = MappingProxyType({
        "created_on": lambda shift: shift.metadata.created_on,
        "created_by": lambda shift: shift.metadata.created_by,
        "last_modified_on": lambda shift: shift.metadata.last_modified_on,
        "last_modified_by": lambda shift: shift.metadata.last_modified_by,
    })


class ModelEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, "model_dump_json"):
            return json.loads(obj.model_dump_json())
        return super().default(obj)


from psycopg2.extras import Json


class ShiftLogMapping:
    @property
    def table_details(self) -> TableDetails:
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
        return tuple(self.table_details.column_map.keys()) + tuple(
            self.table_details.metadata_map.keys()
        )

    def get_params_with_metadata(self, shift) -> Tuple[SqlTypes]:
        return tuple(
            map_fn(shift) for map_fn in self.table_details.column_map.values()
        ) + tuple(map_fn(shift) for map_fn in self.table_details.metadata_map.values())
