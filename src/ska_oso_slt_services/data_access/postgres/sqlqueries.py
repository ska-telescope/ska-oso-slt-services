"""
Pure functions which map from entities to SQL queries with parameters.

This module provides functions to generate SQL queries for various database operations
related to shift management, including inserting, updating,
selecting, and querying shifts.
"""

from datetime import datetime
from typing import Any, Dict, Tuple, Union

from psycopg import sql

from ska_oso_slt_services.data_access.postgres.mapping import TableDetails
from ska_oso_slt_services.domain.shift_models import (
    SbiEntityStatus,
    Shift,
    ShiftLogComment,
)

SqlTypes = Union[str, int, datetime]
QueryAndParameters = Tuple[sql.Composed, Tuple[SqlTypes]]


def insert_query(
    table_details: TableDetails, entity: Shift | ShiftLogComment
) -> QueryAndParameters:
    """
    Creates a query and parameters to insert the given entity in the table,
    effectively creating a new version by inserting a new row,
    and returning the row ID.

    Args:
        table_details (TableDetails): The information about the
        table to perform the insert on.
        entity:  entity which will be persisted..

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    columns = table_details.get_columns_with_metadata()
    params = table_details.get_params_with_metadata(entity)
    query = sql.SQL(
        """
        INSERT INTO {table}
        ({fields})
        VALUES ({values})
        RETURNING id
        """
    ).format(
        table=sql.Identifier(table_details.table_details.table_name),
        fields=sql.SQL(",").join(map(sql.Identifier, columns)),
        values=sql.SQL(",").join(sql.Placeholder() * len(params)),
    )
    return query, params


def update_query(
    entity_id: str | int, table_details: TableDetails, entity: Any
) -> QueryAndParameters:
    """
    Creates a query and parameters to update the given entity in the table,
    directly setting the provided fields without first fetching the existing row.

    Args:
        entity_id: The entity_id contains id of shift or comment
        table_details (TableDetails): The information about the table
        to perform the update on.
        entity: The entity which will be persisted.

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    # Get only non-None fields to update
    columns_and_params = [
        (col, param)
        for col, param in zip(
            table_details.get_columns_with_metadata(),
            table_details.get_params_with_metadata(entity),
        )
        if param is not None
    ]

    if not columns_and_params:
        # If no fields to update, return a query that just verifies the record exists
        query = sql.SQL("SELECT id FROM {table} WHERE {identifier_field}=%s").format(
            table=sql.Identifier(table_details.table_details.table_name),
            identifier_field=sql.Identifier(
                table_details.table_details.identifier_field
            ),
        )
        return query, (entity_id,)

    columns, params = zip(*columns_and_params)

    # Build SET clause for only non-None fields
    set_pairs = sql.SQL(",").join(
        sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder())
        for col in columns
    )

    query = sql.SQL(
        """
        UPDATE {table} SET {set_pairs}
        WHERE {identifier_field}=%s
        RETURNING id;
        """
    ).format(
        table=sql.Identifier(table_details.table_details.table_name),
        set_pairs=set_pairs,
        identifier_field=sql.Identifier(table_details.table_details.identifier_field),
    )
    return query, params + (entity_id,)


def select_metadata_query(
    table_details: TableDetails, entity_id: str | int
) -> QueryAndParameters:
    """
    Creates a query to select all columns for all shifts.

    Args:
        entity_id: id of shift of comment.
        table_details (TableDetails): The information about the table to query.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    columns = table_details.get_metadata_columns()
    query = sql.SQL(
        """
        SELECT {fields}
        FROM {table}
        WHERE {identifier_field} = %s
        """
    ).format(
        fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        identifier_field=sql.Identifier(table_details.table_details.identifier_field),
    )
    return query, (entity_id,)


def select_by_shift_params(
    table_details: TableDetails, shift: Shift, qry_params: SbiEntityStatus
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on user-specific criteria.

    Args:
        table_details (TableDetails): The information about the table to query.
        shift (shift): The shift object containing query parameters.
        qry_params: extra query params based on user input
        (e.g., status, match_type)

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """

    columns = table_details.get_columns_with_metadata()
    if qry_params.match_type:
        match_type_formatters: Dict[str, str] = {
            "equals": "{}",
            "starts_with": "{}%",
            "contains": "%{}%",
        }

        formatter = match_type_formatters.get(qry_params.match_type.value, "{}")

        fields = (key for key in shift.model_fields.keys() if key != "match_type")
        where_clauses = []
        params = []

        for field in fields:
            attr_value = getattr(shift, field)
            if attr_value:
                where_clause = sql.SQL("{} LIKE %s").format(sql.Identifier(field))
                where_clauses.append(where_clause)
                params.append(formatter.format(attr_value))

        if where_clauses:
            where_clause = sql.SQL("WHERE") + sql.SQL(" AND ").join(where_clauses)
        else:
            where_clause = sql.SQL("")
    query = (
        sql.SQL(
            """
    SELECT {fields}
    FROM {table}
    """
        ).format(
            fields=sql.SQL(",").join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_details.table_details.table_name),
            identifier_field=sql.Identifier(
                table_details.table_details.identifier_field
            ),
        )
        + where_clause
        + sql.SQL(" ORDER BY id DESC")
    )

    return query, tuple(params)


def _build_where_clause(
    field_name: str, value: str, match_type_name: str
) -> Tuple[sql.SQL, str]:
    """
    Build WHERE clause based on field name, value and match type.

    Args:
        field_name (str): Name of the field to filter on
        value (str): Value to match against
        match_type_name (str): Type of match to perform (EQUALS, STARTS_WITH, CONTAINS)

    Returns:
        Tuple[sql.SQL, str]: SQL WHERE clause and parameter value
    """
    if match_type_name == "EQUALS":
        return sql.SQL(f"""WHERE {field_name} = %s"""), value
    elif match_type_name in ["STARTS_WITH", "CONTAINS"]:
        return sql.SQL(f"""WHERE {field_name} LIKE %s"""), f"%{value}%"
    return sql.SQL(""), ""


def select_table_data_by_where_clause(
    table_details: TableDetails, oda_entities: Any = None, match_type: str = "Failed"
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on user-specific criteria.

    Args:
        table_details (TableDetails): The information about the table to query.
        oda_entities (Any): The entities containing filter criteria.
        match_type (str): The type of match to perform.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    params = []
    columns = table_details.get_columns_with_metadata()
    where_clause = sql.SQL("")

    if oda_entities:
        if oda_entities.sbi_id:
            where_clause, param = _build_where_clause(
                "sbi_ref", oda_entities.sbi_id, match_type.match_type.name
            )
            params.append(param)
        elif oda_entities.eb_id:
            where_clause, param = _build_where_clause(
                "eb_id", oda_entities.eb_id, match_type.match_type.name
            )
            params.append(param)
    elif match_type and match_type.sbi_status:
        where_clause = sql.SQL("""WHERE sbi_status = %s""")
        params.append(match_type.sbi_status.name.title())

    query = (
        sql.SQL(
            """
        SELECT {fields}
        FROM {table}
        """
        ).format(
            fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_details.table_details.table_name),
            identifier_field=sql.Identifier(
                table_details.table_details.identifier_field
            ),
        )
        + where_clause
        + sql.SQL(" ORDER BY id DESC")
    )

    return query, tuple(params)


def select_by_date_query(
    table_details: TableDetails, qry_params: Shift
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on date-specific criteria.

    Args:
        table_details (TableDetails): The information
        about the table to query.
        qry_params (Shift): The shift object containing query parameters.
    Returns:
        QueryAndParameters: A tuple of the query and parameters.

    Raises:
        ValueError: If an unsupported query type is provided.
    """
    columns = table_details.get_columns_with_metadata()
    mapping_columns = [key for key in table_details.table_details.metadata_map.keys()]
    columns = list(columns) + mapping_columns
    if qry_params.shift_start:
        if qry_params.shift_end:
            where_clause = sql.SQL(
                """WHERE {date_field} >= %s AND {date_field} <= %s"""
            )
            params = (qry_params.shift_start, qry_params.shift_end)
        else:
            where_clause = sql.SQL(
                """
            WHERE {date_field} >= %s
            """
            )
            params = (qry_params.shift_start,)
    else:
        where_clause = sql.SQL("""WHERE {date_field} <= %s""")
        params = (qry_params.shift_end,)

    where_clause = where_clause.format(date_field=sql.Identifier("created_on"))

    query = (
        sql.SQL(
            """
        SELECT {fields}
        FROM {table}
        """
        ).format(
            fields=sql.SQL(",").join(map(sql.Identifier, columns)),
            table=sql.Identifier(table_details.table_details.table_name),
            identifier_field=sql.Identifier(
                table_details.table_details.identifier_field
            ),
        )
        + where_clause
        + sql.SQL(" ORDER BY id DESC")
    )

    return query, params


def select_latest_query(
    table_details: TableDetails, filters, entity_ids=None
) -> QueryAndParameters:
    """
    Creates a query to select comments / annotation based on various criteria:
    - If `id` is provided, fetch the comment / annotation with that `id`.
    - If `shift_id` is provided, fetch all comments / annotation for that shift.
    - If both `shift_id` and `eb_id` are provided, fetch comments matching both.
    - If nothing is passed, fetch all comments / annotation.

    Args:
        table_details (TableDetails): The information about the table to query.
        id (Optional[int]): The ID of the comment / annotation
        shift_id (Optional[str]): The ID of the shift to retrieve comments
        / annotation for.
        eb_id (Optional[str]): The EB ID to filter comments for a specific shift.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    # Get the columns for the select statement
    # Initialize an empty list for where clauses and parameters
    where_clauses = []
    params = []
    column_list = list(table_details.get_columns_with_metadata())
    column_list.append("id")
    columns = tuple(column_list)
    # Start building the base SQL query
    base_query = sql.SQL(
        """
        SELECT {fields}
        FROM {table}
        """
    ).format(
        fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
    )
    if entity_ids:
        # write in query where shift in entity_ids
        where_clauses.append(sql.SQL("shift_id = ANY(%s)"))
        params.append(entity_ids)
    else:
        tid, shift_id, eb_id = (
            filters.get("id"),
            filters.get("shift_id"),
            filters.get("eb_id"),
        )
        # Add conditions based on the parameters provided
        if tid is not None:
            where_clauses.append(
                sql.SQL("{field} = %s").format(field=sql.Identifier("id"))
            )
            params.append(tid)

        if shift_id is not None:
            where_clauses.append(
                sql.SQL("{field} = %s").format(field=sql.Identifier("shift_id"))
            )
            params.append(shift_id)

        if shift_id is not None and eb_id is not None:
            where_clauses.append(
                sql.SQL("{field} = %s").format(field=sql.Identifier("eb_id"))
            )
            params.append(eb_id)

        if eb_id:
            where_clauses.append(
                sql.SQL("{field} = %s").format(field=sql.Identifier("eb_id"))
            )
            params.append(eb_id)

    # Build the final query based on the conditions
    if where_clauses:
        query = base_query + sql.SQL(" WHERE ") + sql.SQL(" AND ").join(where_clauses)
    else:
        query = base_query  # No conditions, return all comments

    query += sql.SQL(" ORDER BY {order_field} DESC").format(
        order_field=sql.Identifier("id")
    )

    return query, tuple(params)


def select_latest_shift_query(table_details: TableDetails) -> QueryAndParameters:
    """
    Creates a query and parameters to find the latest shift in the table,
    returning the row with the most recent timestamp `created_on`.

    Args:
        table_details (TableDetails): The information about the table to perform
        the query on.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    query = sql.SQL(
        """
        SELECT shift_id
        FROM {table}
        WHERE shift_end IS NULL
        ORDER BY id DESC LIMIT 1
        """
    ).format(table=sql.Identifier(table_details.table_details.table_name))

    params = ()
    return query, params


def patch_query(
    table_details: TableDetails,
    column_names: list[str],
    params: list[Any],
    shift_id: int,
    shift: Shift = None,
) -> Tuple[str, tuple]:
    """
    Creates a query and parameters to patch specific columns of a shift entry.

    Args:
        table_details (TableDetails): The information about
        the table to perform the patch on.
        column_names (list[str]): List of column names to be updated.
        params (list[Any]): List of values corresponding to the column names.
        shift_id (int): The ID of the shift to be patched.

    Returns:
        Tuple[str, tuple]: A tuple of the query string and parameters.
    """

    params = tuple(params) + table_details.get_metadata_params(shift)
    columns = column_names + list(table_details.get_metadata_columns())
    query = sql.SQL(
        """
        UPDATE {table} SET ({fields}) = ({values})
        WHERE id=(SELECT id FROM {table} WHERE {identifier_field}=%s)
        RETURNING id;
        """
    ).format(
        identifier_field=sql.Identifier(table_details.table_details.identifier_field),
        table=sql.Identifier(table_details.table_details.table_name),
        fields=sql.SQL(",").join(map(sql.Identifier, columns)),
        values=sql.SQL(",").join(sql.Placeholder() * len(params)),
    )
    return query, params + (shift_id,)


def shift_logs_patch_query(
    table_details: TableDetails, shift: Shift
) -> Tuple[str, tuple]:
    columns = table_details.get_shift_log_columns()
    params = table_details.get_shift_log_params(shift)
    return patch_query(table_details, columns, params, shift.shift_id, shift=shift)
