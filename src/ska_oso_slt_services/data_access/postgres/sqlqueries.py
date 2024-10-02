"""
Pure functions which map from entities to SQL queries with parameters.

This module provides functions to generate SQL queries for various database operations
related to shift management, including inserting, updating,
selecting, and querying shifts.
"""

from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from psycopg import sql

from ska_oso_slt_services.data_access.postgres.mapping import TableDetails
from ska_oso_slt_services.domain.shift_models import (
    DateQuery,
    JsonQuery,
    Shift,
    TextQuery,
    UserQuery,
)

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


def shift_logs_patch_query(
    table_details: TableDetails, shift: Shift
) -> Tuple[str, tuple]:
    columns = table_details.get_shift_log_columns()
    params = table_details.get_shift_log_params(shift)
    return patch_query(table_details, columns, params, shift.shift_id, shift=shift)


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

    params = params + table_details.get_metadata_params(shift)
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
    columns = table_details.get_columns_with_metadata_with_extra_keys()
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


def select_metadata_query(
    table_details: TableDetails, shift_id: str
) -> QueryAndParameters:
    """
    Creates a query to select all columns for all shifts.

    Args:
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
    return query, (shift_id,)


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

    columns = table_details.get_columns_with_metadata_with_extra_keys()
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
    columns = table_details.get_columns_with_metadata_with_extra_keys()
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


def select_by_text_query(
    table_details: TableDetails, qry_params: TextQuery
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on text-based criteria
    using full-text search.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (TextQuery): The text-based query parameters.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    columns = list(table_details.get_columns_with_metadata_with_extra_keys())
    search_columns = get_search_columns(table_details)

    query, params = build_search_query(
        table_details, columns, search_columns, qry_params
    )

    return query, params


def get_search_columns(table_details: TableDetails) -> List[str]:
    return [table_details.table_details.text_base_search_fields]


def build_search_query(
    table_details: TableDetails,
    columns: List[str],
    search_columns: List[str],
    qry_params: TextQuery,
) -> Tuple[sql.Composed, Tuple[str, ...]]:
    """
    Builds a search query based on the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_columns (List[str]): The list of columns to search within.
        qry_params (TextQuery): The text-based query parameters.

    Returns:
        Tuple[sql.Composed, Tuple[str, ...]]:
        A tuple containing the query and parameters.

    Raises:
        ValueError: If an unsupported match_type is provided.
    """

    if qry_params.match_type.value == "equals":
        return build_full_text_search_query(
            table_details, columns, search_columns, qry_params
        )
    elif qry_params.match_type.value in ["starts_with", "contains"]:
        return build_like_query(table_details, columns, search_columns[0], qry_params)
    else:
        raise ValueError(f"Unsupported match_type: {qry_params.match_type}")


def build_full_text_search_query(
    table_details: TableDetails,
    columns: List[str],
    search_columns: List[str],
    qry_params: TextQuery,
) -> Tuple[sql.Composed, Tuple[str, str]]:
    """
    Builds a full-text search query using the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_columns (List[str]): The list of columns to search within.
        qry_params (TextQuery): The text-based query parameters.

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

    return query, (qry_params.search_text, qry_params.search_text)


def build_like_query(
    table_details: TableDetails,
    columns: List[str],
    search_column: str,
    qry_params: TextQuery,
) -> Tuple[sql.Composed, Tuple[str]]:
    """
    Builds a LIKE query using the provided parameters.

    Args:
        table_details (TableDetails): The information about the table to query.
        columns (List[str]): The list of columns to select.
        search_column (str): The column to search within.
        qry_params (TextQuery): The text-based query parameters.

    Returns:
        Tuple[sql.Composed, Tuple[str]]: A tuple containing the query and parameters.
    """
    like_pattern = (
        f"{qry_params.search_text}%"
        if qry_params.match_type == "starts_with"
        else f"%{qry_params.search_text}%"
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
    table_details: TableDetails, qry_params: JsonQuery
) -> Tuple[str, Tuple[str]]:
    """
    Creates a query to select logs based on the status of the shift.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (JsonQuery): The JSON-based query parameters.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    # Get the dynamic columns
    dynamic_columns = table_details.get_columns_with_metadata_with_extra_keys()
    column_selection = ", ".join(dynamic_columns)

    # Build the dynamic column selection part of the query_
    query_str = f"""
        SELECT
            {column_selection},
            jsonb_build_object(
                'logs',
                jsonb_agg(
                    jsonb_build_object(
                        'info', log->'info',
                        'source', log->'source',
                        'log_time', log->'log_time'
                    )
                )
            ) as shift_logs
        FROM
            {table_details.table_details.table_name},
            jsonb_array_elements(shift_logs->'logs') AS log
        WHERE
            log->'info'->>'sbi_status' = %s
        GROUP BY
            {column_selection}
    """
    params = (qry_params.status.value,)

    return query_str, params
