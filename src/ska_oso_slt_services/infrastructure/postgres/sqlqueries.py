"""
Pure functions which map from entities to SQL queries with parameters.

This module provides functions to generate SQL queries for various database operations
related to shift management, including inserting, updating,
selecting, and querying shifts.
"""

from datetime import datetime
from typing import Any, Dict, Tuple, Union

from psycopg import sql

from ska_oso_slt_services.infrastructure.postgres.mapping import TableDetails
from ska_oso_slt_services.models.shiftmodels import DateQuery, Shift, UserQuery

SqlTypes = Union[str, int, datetime]
QueryAndParameters = Tuple[sql.Composed, Tuple[SqlTypes]]


def insert_query(table_details: TableDetails, shift: Shift) -> QueryAndParameters:
    """
    Creates a query and parameters to insert the given entity in the table,
    effectively creating a new version by inserting a new row,
    and returning the row ID.

    Args:
        table_details (TableDetails): The information about the
        table to perform the insert on.
        shift (Shift): The shift entity which will be persisted.

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    columns = table_details.get_columns_with_metadata()
    params = table_details.get_params_with_metadata(shift)
    # params = tuple(shift_dump[key] for key in mapping.table_details.column_map.keys())
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


def update_query(table_details: TableDetails, shift: Shift) -> QueryAndParameters:
    """
    Creates a query and parameters to update the given entity in the table,
    overwriting values in the existing row and returning the row ID.

    If there is not an existing row for the identifier
    then no update is performed.

    Args:
        table_details (TableDetails): The information about the table
        to perform the update on.
        shift (Shift): The shift entity which will be persisted.

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    columns = table_details.get_columns_with_metadata()
    params = table_details.get_params_with_metadata(shift)
    # query to add comments

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
    return query, params + (shift.shift_id,)


def patch_query(
    table_details: TableDetails,
    column_names: list[str],
    values: list[Any],
    shift_id: int,
) -> Tuple[str, tuple]:
    """
    Creates a query and parameters to patch specific columns of a shift entry.

    Args:
        table_details (TableDetails): The information about
        the table to perform the patch on.
        column_names (list[str]): List of column names to be updated.
        values (list[Any]): List of values corresponding to the column names.
        shift_id (int): The ID of the shift to be patched.

    Returns:
        Tuple[str, tuple]: A tuple of the query string and parameters.
    """
    params = tuple(values) + (shift_id,)
    placeholders = ",".join(["%s"] * len(values))
    query = f"""
    UPDATE {table_details.table_details.table_name}
    SET ({','.join(tuple(column_names,))}) = ROW({placeholders})
    WHERE {table_details.table_details.identifier_field}=%s
    RETURNING id;
    """
    return query, params


def select_latest_query(
    table_details: TableDetails, shift_id: str
) -> QueryAndParameters:
    """
    Creates a query and parameters to find the latestversion of
    the given entity in the table, returning the row if found.

    Args:
        table_details (TableDetails): The information about
        the table to perform the query on.
        shift_id (str): The identifier of the shift to search for.

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    columns = table_details.table_details.column_map.keys()
    mapping_columns = [key for key in table_details.table_details.metadata_map.keys()]
    columns = list(columns) + mapping_columns
    where_clause = sql.SQL("WHERE {identifier_field} = %s ORDER BY id").format(
        identifier_field=sql.Identifier(table_details.table_details.identifier_field),
    )
    params = (shift_id,)

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
    )

    return query, params


def column_based_query(table_details: TableDetails, shift_id: str, column_names: list):
    """
    Creates a query to select specific columns for a given shift ID.

    Args:
        table_details (TableDetails): The information about the table to query.
        shift_id (str): The identifier of the shift to query.
        column_names (list): List of column names to select.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    query = sql.SQL(
        """
        SELECT {column_name}
        FROM {table}
        WHERE {identifier_field} = %s
        """
    ).format(
        column_name=sql.SQL(",").join(map(sql.Identifier, column_names)),
        table=sql.Identifier(table_details.table_details.table_name),
        identifier_field=sql.Identifier(table_details.table_details.identifier_field),
    )
    params = (shift_id,)
    return query, params


def select_by_user_query(
    table_details: TableDetails, qry_params: UserQuery
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on user-specific criteria.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (UserQuery): The user query parameters.

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
    )

    return query, tuple(params)


def select_by_date_query(
    table_details: TableDetails, qry_params: DateQuery
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on date-specific criteria.

    Args:
        table_details (TableDetails): The information
        about the table to query.
        qry_params (DateQuery): The date query parameters.

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
    )

    return query, params
