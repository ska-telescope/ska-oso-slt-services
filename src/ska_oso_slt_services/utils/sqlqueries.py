"""
Pure functions which map from entities to SQL queries with parameteres
"""

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Callable, Dict, Tuple, Union

from psycopg import sql

from ska_oso_slt_services.models.data_models import (
    DateQuery,
    Shift,
    ShiftLogs,
    UserQuery,
)
from ska_oso_slt_services.utils.codec import CODEC

SqlTypes = Union[str, int, datetime]
QueryAndParameters = Tuple[sql.Composed, Tuple[SqlTypes]]


@dataclass
class TableDetails:
    table_name: str
    identifier_field: str
    # These dicts are keyed by the name of the table column and the value is a function which maps the entity to that column value
    column_map: dict
    metadata_map: dict


import json
from typing import Any


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
            # TO DO need to revisit
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
            metadata_map={
                "created_on": lambda shift: shift.metadata.created_on,
                "created_by": lambda shift: shift.metadata.created_by,
                "last_modified_on": lambda shift: shift.metadata.last_modified_on,
                "last_modified_by": lambda shift: shift.metadata.last_modified_by,
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



import json


def insert_query(shift: Shift) -> QueryAndParameters:
    """
    Creates a query and parameters to insert the given entity in the table,
    effectively creating a new version by inserting a new row, and returning the row ID.

    :param table_details: The information about the table to perform the insert on.
    :param entity: The entity which will be persisted.
    :return: A tuple of the query and parameters, which psycopg will safely combine.
    """
    mapping = ShiftLogMapping()
    columns = mapping.get_columns_with_metadata()
    params = mapping.get_params_with_metadata(shift)
    # params = tuple(shift_dump[key] for key in mapping.table_details.column_map.keys())
    query = sql.SQL("""
        INSERT INTO {table}
        ({fields})
        VALUES ({values})
        RETURNING id
        """).format(
        table=sql.Identifier(mapping.table_details.table_name),
        fields=sql.SQL(",").join(map(sql.Identifier, columns)),
        values=sql.SQL(",").join(sql.Placeholder() * len(params)),
    )

    return query, params


def update_query(shift: Shift) -> QueryAndParameters:
    """
    Creates a query and parameters to update the given entity in the table, overwriting values in the existing row and returning the row ID.

    If there is not an existing row for the identifier then no update is performed.

    :param table_details: The information about the table to perform the update on.
    :param entity: The entity which will be persisted.
    :return: A tuple of the query and parameters, which psycopg will safely combine.
    """
    mapping = ShiftLogMapping()
    columns = mapping.get_columns_with_metadata()
    params = mapping.get_params_with_metadata(shift)
    # query to add comments

    query = sql.SQL("""
        UPDATE {table} SET ({fields}) = ({values})
        WHERE id=(SELECT id FROM {table} WHERE {identifier_field}=%s)
        RETURNING id;
        """).format(
        identifier_field=sql.Identifier(mapping.table_details.identifier_field),
        table=sql.Identifier(mapping.table_details.table_name),
        fields=sql.SQL(",").join(map(sql.Identifier, columns)),
        values=sql.SQL(",").join(sql.Placeholder() * len(params)),
    )
    return query, params + (shift.shift_id,)


def patch_query(
    column_names: Tuple[str, ...], values: Tuple[Any, ...], shift_id: int
) -> Tuple[str, tuple]:
    

    mapping = ShiftLogMapping()
    params = values + (shift_id,)
    placeholders = ",".join(["%s"] * len(values))
    query = f"""
    UPDATE {mapping.table_details.table_name}
    SET ({','.join(column_names)}) = ROW({placeholders})
    WHERE {mapping.table_details.identifier_field}=%s
    RETURNING id;
    """
    return query, params


def select_latest_query(shift_id: str) -> QueryAndParameters:
    """
    Creates a query and parameters to find the latest version of the given entity in the table, returning the row if found.

    :param table_details: The information about the table to perform the update on.
    :param entity_id: The identifier of the entity to search for.
    :return: A tuple of the query and parameters, which psycopg will safely combine.
    """

    mapping = ShiftLogMapping()
    columns = mapping.table_details.column_map.keys()
    mapping_columns = [key for key in mapping.table_details.metadata_map.keys()]
    columns = list(columns) + mapping_columns
    where_clause = sql.SQL("WHERE {identifier_field} = %s ORDER BY id").format(
        identifier_field=sql.Identifier(mapping.table_details.identifier_field),
    )
    params = (shift_id,)

    query = (
        sql.SQL("""
        SELECT {fields}
        FROM {table}
        """).format(
            fields=sql.SQL(",").join(map(sql.Identifier, columns)),
            table=sql.Identifier(mapping.table_details.table_name),
            identifier_field=sql.Identifier(mapping.table_details.identifier_field),
        )
        + where_clause
    )

    return query, params


def column_based_query(shift_id: str, column_name: str):
    mapping = ShiftLogMapping()
    query = sql.SQL("""
        SELECT {column_name}
        FROM {table}
        WHERE {identifier_field} = %s
        """).format(
        column_name=sql.Identifier(column_name),
        table=sql.Identifier(mapping.table_details.table_name),
        identifier_field=sql.Identifier(mapping.table_details.identifier_field),
    )
    params = (shift_id,)
    return query, params


def select_by_user_query(qry_params: UserQuery) -> QueryAndParameters:

    mapping = ShiftLogMapping()
    columns = mapping.get_columns_with_metadata()
    if qry_params.match_type:
        match_type_formatters: Dict[str, str] = {
            "equals": "{}",
            "starts_with": "{}%",
            "contains": "%{}%",
        }

        formatter = match_type_formatters.get(qry_params.match_type.value, "{}")

        fields = (key for key in qry_params.model_fields.keys() if key != "match_type")
        where_clauses = []
        params = []

        for field in fields:
            attr_value = getattr(qry_params, field)
            if attr_value:
                where_clause = sql.SQL("{} LIKE %s").format(sql.Identifier(field))
                where_clauses.append(where_clause)
                params.append(formatter.format(attr_value))

        if where_clauses:
            where_clause = sql.SQL("WHERE") + sql.SQL(" AND ").join(where_clauses)
        else:
            where_clause = sql.SQL("")
    query = (
        sql.SQL("""
    SELECT {fields}
    FROM {table}
    """).format(
            fields=sql.SQL(",").join(map(sql.Identifier, columns)),
            table=sql.Identifier(mapping.table_details.table_name),
            identifier_field=sql.Identifier(mapping.table_details.identifier_field),
        )
        + where_clause
    )

    return query, tuple(params)


def select_by_date_query(qry_params: DateQuery) -> QueryAndParameters:
    mapping = ShiftLogMapping()
    columns = mapping.get_columns_with_metadata()
    mapping_columns = [key for key in mapping.table_details.metadata_map.keys()]
    columns = list(columns) + mapping_columns
    if qry_params.shift_start:
        if qry_params.shift_end:
            where_clause = sql.SQL(
                """WHERE {date_field} >= %s AND {date_field} <= %s"""
            )
            params = (qry_params.shift_start, qry_params.shift_end)
        else:
            where_clause = sql.SQL("""
            WHERE {date_field} >= %s
            """)
            params = (qry_params.shift_start,)
    else:
        where_clause = sql.SQL("""WHERE {date_field} <= %s""")
        params = (qry_params.shift_end,)

    if qry_params.query_type:
        if qry_params.query_type.value == "modified_between":
            where_clause = where_clause.format(
                date_field=sql.Identifier("last_modified_on")
            )
        elif qry_params.query_type.value == "created_between":
            where_clause = where_clause.format(date_field=sql.Identifier("created_on"))
        else:
            raise ValueError(
                f"Unsupported query type {qry_params.query_type.__class__.__name__}"
            )

    query = (
        sql.SQL("""
        SELECT {fields}
        FROM {table}
        """).format(
            fields=sql.SQL(",").join(map(sql.Identifier, columns)),
            table=sql.Identifier(mapping.table_details.table_name),
            identifier_field=sql.Identifier(mapping.table_details.identifier_field),
        )
        + where_clause
    )

    return query, params
