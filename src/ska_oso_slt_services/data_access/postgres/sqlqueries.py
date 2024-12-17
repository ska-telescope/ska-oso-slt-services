"""
Pure functions which map from entities to SQL queries with parameters.

This module provides functions to generate SQL queries for various database operations
related to shift management, including inserting, updating,
selecting, and querying shifts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from psycopg import sql

from ska_oso_slt_services.data_access.postgres.mapping import TableDetails
from ska_oso_slt_services.domain.shift_models import (
    MatchType,
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
    overwriting values in the existing row and returning the row ID.

    If there is not an existing row for the identifier
    then no update is performed.

    Args:
        entity_id: The entity_id contais id of shift or comment
        table_details (TableDetails): The information about the table
        to perform the update on.
        entity: The entity which will be persisted.

    Returns:
        QueryAndParameters: A tuple of the query and parameters,
        which psycopg will safely combine.
    """
    columns = table_details.get_columns_with_metadata()
    params = table_details.get_params_with_metadata(entity)

    # Add the identifier value (e.g., shift_id or comment_id) to the end of params
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
    return query, params + (entity_id,)


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
    columns = table_details.get_columns_with_metadata()
    where_clause = sql.SQL("WHERE {identifier_field} = %s ORDER BY id DESC").format(
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


def select_by_text_query(
    table_details: TableDetails, search_text: str, qry_params: MatchType
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on text-based criteria
    using full-text search.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (TextQuery): The text-based query parameters.
        search_text (str): The text to search for.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    columns = list(table_details.get_columns_with_metadata())
    search_columns = get_search_columns(table_details)

    query, params = build_search_query(
        table_details, columns, search_columns, qry_params, search_text
    )

    return query, params


def get_search_columns(table_details: TableDetails) -> List[str]:
    """
    Get the search columns for the given table.
    Args:
        table_details (TableDetails): The information about the table to query.
    Returns:
        List[str]: A list of search columns for the given table
    """
    return [table_details.table_details.text_base_search_fields]


def build_search_query(
    table_details: TableDetails,
    columns: List[str],
    search_columns: List[str],
    qry_params: MatchType,
    search_text: str,
) -> Tuple[sql.Composed, Tuple[str, ...]]:
    """
    Builds a search query based on the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_columns (List[str]): The list of columns to search within.
        qry_params (TextQuery): The text-based query parameters.
        search_text (str): The text to search for.

    Returns:
        Tuple[sql.Composed, Tuple[str, ...]]:
        A tuple containing the query and parameters.

    Raises:
        ValueError: If an unsupported match_type is provided.
    """

    if qry_params.match_type.value == "equals":
        return build_full_text_search_query(
            table_details, columns, search_columns, search_text
        )
    elif qry_params.match_type.value in ["starts_with", "contains"]:
        return build_like_query(
            table_details, columns, search_columns[0], search_text, qry_params
        )
    else:
        raise ValueError(f"Unsupported match_type: {qry_params.match_type}")


def build_full_text_search_query(
    table_details: TableDetails,
    columns: List[str],
    search_columns: List[str],
    search_text: str,
) -> Tuple[sql.Composed, Tuple[str, str]]:
    """
    Builds a full-text search query using the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_columns (List[str]): The list of columns to search within.
        search_text (str): The text to search for.

    Returns:
        Tuple[sql.Composed, Tuple[str, str]]: A tuple containing
        the query and parameters.
    """
    combined_tsvector = sql.SQL(" || ").join(
        sql.SQL("to_tsvector('english', {}::text)").format(sql.Identifier(col))
        for col in search_columns
    )

    query = sql.SQL(
        """
        SELECT {fields},
            ts_rank({combined_tsvector}, plainto_tsquery('english', %s)) AS search_rank
        FROM {table}
        WHERE {combined_tsvector} @@ plainto_tsquery('english', %s)
        ORDER BY search_rank DESC
    """
    ).format(
        fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        combined_tsvector=combined_tsvector,
    )

    return query, (search_text, search_text)


def build_like_query(
    table_details: TableDetails,
    columns: List[str],
    search_column: str,
    search_text: str,
    qry_params: str,
) -> Tuple[sql.Composed, Tuple[str]]:
    """
    Builds a LIKE query using the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_column (str): The column to search within.
        qry_params (TextQuery): The text-based query parameters.
        search_text (str): The text to search for.

    Returns:
        Tuple[sql.Composed, Tuple[str]]: A tuple containing the query and parameters.
    """
    like_pattern = (
        f"{search_text}%"
        if qry_params.match_type == "starts_with"
        else f"%{search_text}%"
    )

    query = sql.SQL(
        """
        SELECT {fields}
        FROM {table}
        WHERE {search_column} ILIKE %s
    """
    ).format(
        fields=sql.SQL(", ").join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        search_column=sql.Identifier(search_column),
    )

    return query, (like_pattern,)


def select_logs_by_status(
    table_details: TableDetails, qry_params: SbiEntityStatus, status_column: str
) -> Tuple[str, Tuple[str]]:
    """
    Creates a query to select logs based on the status of the shift.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (SbiEntityStatus): The JSON-based query parameters.
        status_column (str): The column to search within

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    # Get the dynamic columns
    dynamic_columns = table_details.get_columns_with_metadata()
    column_selection = ", ".join(dynamic_columns)

    # Build the dynamic column selection part of the query_
    query_str = f"""
        SELECT
            {column_selection},
            jsonb_agg(
                jsonb_build_object(
                    'info', log->'info',
                    'source', log->'source',
                    'log_time', log->'log_time'
                )
            ) shift_logs
        FROM
            {table_details.table_details.table_name},
            jsonb_array_elements(shift_logs) AS log
        WHERE
            log->'info'->>{status_column!r} = %s
        GROUP BY
            {column_selection}
    """
    params = (qry_params.sbi_status.value,)

    return query_str, params


def select_comments_query(
    table_details: TableDetails,
    id: Optional[int] = None,  # pylint: disable=W0622
    shift_id: Optional[str] = None,
    eb_id: Optional[str] = None,
) -> QueryAndParameters:
    """
    Creates a query to select comments based on various criteria:
    - If `id` is provided, fetch the comment with that `id`.
    - If `shift_id` is provided, fetch all comments for that shift.
    - If both `shift_id` and `eb_id` are provided, fetch comments matching both.
    - If nothing is passed, fetch all comments.

    Args:
        table_details (TableDetails): The information about the table to query.
        id (Optional[int]): The ID of the comment.
        shift_id (Optional[str]): The ID of the shift to retrieve comments for.
        eb_id (Optional[str]): The EB ID to filter comments for a specific shift.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    # Get the columns for the select statement
    columns = table_details.get_columns_with_metadata()

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

    # Initialize an empty list for where clauses and parameters
    where_clauses = []
    params = []

    # Add conditions based on the parameters provided
    if id is not None:
        where_clauses.append(sql.SQL("{field} = %s").format(field=sql.Identifier("id")))
        params.append(id)

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
