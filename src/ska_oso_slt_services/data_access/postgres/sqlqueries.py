"""
Pure functions which map from entities to SQL queries with parameters.

This module provides functions to generate SQL queries for various database operations
related to shift management, including inserting, updating,
selecting, and querying shifts.
"""

from datetime import datetime
from typing import Any, Dict, Tuple, Union, List

from psycopg import sql

from ska_oso_slt_services.data_access.postgres.mapping import TableDetails
from ska_oso_slt_services.domain.shift_models import DateQuery, Shift, UserQuery, TextBasedQuery

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


def select_by_text_query(
    table_details: TableDetails, qry_params: TextBasedQuery
) -> QueryAndParameters:
    """
    Creates a query to select shifts based on text-based criteria using full-text search.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (TextBasedQuery): The text-based query parameters.

    Returns:
        QueryAndParameters: A tuple of the query and parameters.
    """
    columns = get_all_columns(table_details)
    search_columns = get_search_columns(table_details)
    
    query, params = build_search_query(table_details, columns, search_columns, qry_params)
    
    return query, params

def get_all_columns(table_details: TableDetails) -> List[str]:
    return list(table_details.get_columns_with_metadata_with_extra_keys()) + \
           list(table_details.table_details.metadata_map.keys())

def get_search_columns(table_details: TableDetails) -> List[str]:
    return [table_details.table_details.text_base_search_fields]

def build_search_query(
    table_details: TableDetails, 
    columns: List[str], 
    search_columns: List[str], 
    qry_params: TextBasedQuery
) -> Tuple[sql.Composed, Tuple[str, ...]]:
    if qry_params.match_type.value == "equals":
        return build_full_text_search_query(table_details, columns, search_columns, qry_params)
    elif qry_params.match_type.value in ["starts_with", "contains"]:
        return build_like_query(table_details, columns, search_columns[0], qry_params)
    else:
        raise ValueError(f"Unsupported match_type: {qry_params.match_type}")

def build_full_text_search_query(
    table_details: TableDetails, 
    columns: List[str], 
    search_columns: List[str], 
    qry_params: TextBasedQuery
) -> Tuple[sql.Composed, Tuple[str, str]]:
    combined_tsvector = sql.SQL(' || ').join(
        sql.SQL("to_tsvector('english', {}::text)").format(sql.Identifier(col))
        for col in search_columns
    )
    
    query = sql.SQL("""
        SELECT {fields},
            ts_rank({combined_tsvector}, plainto_tsquery('english', %s)) AS search_rank
        FROM {table}
        WHERE {combined_tsvector} @@ plainto_tsquery('english', %s)
        ORDER BY search_rank DESC
    """).format(
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        combined_tsvector=combined_tsvector
    )
    
    return query, (qry_params.search_text, qry_params.search_text)

def build_like_query(
    table_details: TableDetails, 
    columns: List[str], 
    search_column: str, 
    qry_params: TextBasedQuery
) -> Tuple[sql.Composed, Tuple[str]]:
    like_pattern = f"{qry_params.search_text}%" if qry_params.match_type == "starts_with" else f"%{qry_params.search_text}%"
    
    query = sql.SQL("""
        SELECT {fields}
        FROM {table}
        WHERE {search_column} ILIKE %s
    """).format(
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        search_column=sql.Identifier(search_column)
    )
    
    return query, (like_pattern,)

from psycopg2 import sql
from typing import List, Tuple, Any, Dict

class JSONFieldQuery:
    def __init__(self, conditions: Dict[str, Any]):
        self.conditions = conditions


def select_by_json_field_query(
    table_details: TableDetails, 
    qry_params: JSONFieldQuery
) -> Tuple[sql.Composed, Tuple[Any, ...]]:
    """
    Creates a query to select records based on multiple conditions in a JSON array column.

    Args:
        table_details (TableDetails): The information about the table to query.
        qry_params (JSONFieldQuery): The query parameters including multiple JSON field conditions.

    Returns:
        Tuple[sql.Composed, Tuple[Any, ...]]: A tuple of the query and parameters.
    """
    columns = get_all_columns(table_details)
    
    query, params = build_json_field_query(table_details, columns, qry_params)
    
    return query, params

def get_all_columns(table_details: TableDetails) -> List[str]:
    return table_details.get_columns_with_metadata_with_extra_keys()

def build_json_field_query(
    table_details: TableDetails, 
    columns: List[str], 
    qry_params: JSONFieldQuery
) -> Tuple[sql.Composed, List[Any]]:
    conditions = []
    params = []
    qry_params = JSONFieldQuery({
     "sbi_status": "Created"})
    for json_path, search_value in qry_params.conditions.items():
        json_condition = build_json_condition(table_details.table_details.json_base_search_fields, json_path, search_value)
        conditions.append(json_condition)
        params.append(search_value)
    import pdb;pdb.set_trace()
    where_clause = sql.SQL(" AND ").join(conditions)
    
    query = sql.SQL("""
        SELECT {fields}
        FROM {table}
        WHERE {where_clause}
    """).format(
        fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
        table=sql.Identifier(table_details.table_details.table_name),
        where_clause=where_clause
    )
    
    return query, tuple(params)

def build_json_condition(json_column: str, json_path: str, search_value: Any) -> sql.Composed:
    json_access = build_json_access(json_column, json_path)
    
    return sql.SQL("{} = %s").format(json_access)

def build_json_access(json_column: str, json_path: str) -> sql.Composed:
    path_parts = json_path.split('.')
    result = sql.Identifier(json_column)
    
    for part in path_parts:
        if part == '*':
            # Use jsonb_array_elements to search in all array elements
            result = sql.SQL("jsonb_array_elements({})").format(result)
        elif part.isdigit():
            result = sql.SQL("{}->{}").format(result, sql.Literal(int(part)))
        else:
            result = sql.SQL("{}->>{}").format(result, sql.Literal(part))
    
    return result

# from psycopg2 import sql
# from typing import List, Tuple, Any, Dict

# def select_by_json_field_query(
#     table_details: TableDetails, 
#     qry_params: JSONFieldQuery
# ) -> Tuple[str, Tuple[Any, ...]]:
#     """
#     Creates a query to select records based on multiple conditions in a JSON array column.

#     Args:
#         table_details (TableDetails): The information about the table to query.
#         qry_params (JSONFieldQuery): The query parameters including multiple JSON field conditions.

#     Returns:
#         Tuple[str, Tuple[Any, ...]]: A tuple of the query string and parameters.
#     """
#     columns = get_all_columns(table_details)
    
#     query, params = build_json_field_query(table_details, columns, qry_params)
    
#     # Convert the sql.Composed object to a string
#     query_string = query.as_string(table_details.connection)
    
#     return query_string, params

# # ... (rest of the functions remain the same)

# class TableDetails:
#     def __init__(self, table_name: str, json_column_name: str, connection):
#         self.table_name = table_name
#         self.json_column_name = json_column_name
#         self.connection = connection

#     def get_columns_with_metadata_with_extra_keys(self):
#         # Implement this method based on your needs
#         return ["id", self.json_column_name]

# # Example usage
# import psycopg2

# # Establish your database connection
# conn = psycopg2.connect(
#     host="your_host",
#     database="your_database",
#     user="your_user",
#     password="your_password"
# )

# table_details = TableDetails(
#     table_name="your_table_name",
#     json_column_name="jsonb_column",
#     connection=conn
# )

# qry_params = JSONFieldQuery({
#     "*.info.sbi_status": "Created",
#     "*.info.telescope": "ska_mid",
#     "*.source": "ODA"
# })


# print(query_string)
# print(params)

# # Execute the query
# with conn.cursor() as cur:
#     cur.execute(query_string, params)
#     results = cur.fetchall()

# print(results)

# # Don't forget to close your connection when you're done
# conn.close()



# from psycopg2 import sql
# from typing import List, Tuple, Any, Dict

# class JSONFieldQuery:
#     def __init__(self, conditions: Dict[str, Any]):
#         self.conditions = conditions

# def select_by_json_field_query(
#     table_details: TableDetails, 
#     qry_params: JSONFieldQuery
# ) -> Tuple[sql.Composed, Tuple[Any, ...]]:
#     """
#     Creates a query to select records based on multiple conditions in a JSON array column.

#     Args:
#         table_details (TableDetails): The information about the table to query.
#         qry_params (JSONFieldQuery): The query parameters including multiple JSON field conditions.

#     Returns:
#         Tuple[sql.Composed, Tuple[Any, ...]]: A tuple of the query and parameters.
#     """
#     qry_params = JSONFieldQuery({
#     "*.info.sbi_status": "Created"})
#     columns = get_all_columns(table_details)
    
#     query, params = build_json_field_query(table_details, columns, qry_params)
    
#     return query, params

# def get_all_columns(table_details: TableDetails) -> List[str]:
#     return table_details.get_columns_with_metadata_with_extra_keys()

# def build_json_field_query(
#     table_details: TableDetails, 
#     columns: List[str], 
#     qry_params: JSONFieldQuery
# ) -> Tuple[sql.Composed, List[Any]]:
#     conditions = []
#     params = []

#     for json_path, search_value in qry_params.conditions.items():
#         json_condition = build_json_condition(table_details.table_details.json_base_search_fields, json_path, search_value)
#         conditions.append(json_condition)
#         params.append(search_value)

#     where_clause = sql.SQL(" AND ").join(conditions)
    
#     query = sql.SQL("""
#         SELECT {fields}
#         FROM {table}
#         WHERE {where_clause}
#     """).format(
#         fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
#         table=sql.Identifier(table_details.table_details.table_name),
#         where_clause=where_clause
#     )
#     return query, tuple(params)

# def build_json_condition(json_column: str, json_path: str, search_value: Any) -> sql.Composed:
#     json_access = build_json_access(json_column, json_path)
    
#     return sql.SQL("{} = %s").format(json_access)

# def build_json_access(json_column: str, json_path: str) -> sql.Composed:
#     path_parts = json_path.split('.')
#     result = sql.Identifier(json_column)
    
#     for part in path_parts:
#         if part == '*':
#             # Use jsonb_array_elements to search in all array elements
#             result = sql.SQL("jsonb_array_elements({})").format(result)
#         elif part.isdigit():
#             result = sql.SQL("{}->{}").format(result, sql.Literal(int(part)))
#         else:
#             result = sql.SQL("{}->>{}").format(result, sql.Literal(part))
    
#     return result


# from psycopg2 import sql
# from typing import List, Tuple, Any, Dict

# def select_by_json_field_query(
#     table_details: TableDetails, 
#     qry_params: JSONFieldQuery
# ) -> Tuple[str, Tuple[Any, ...]]:
#     """
#     Creates a query to select records based on multiple conditions in a JSON array column.

#     Args:
#         table_details (TableDetails): The information about the table to query.
#         qry_params (JSONFieldQuery): The query parameters including multiple JSON field conditions.

#     Returns:
#         Tuple[str, Tuple[Any, ...]]: A tuple of the query string and parameters.
#     """
#     columns = get_all_columns(table_details)
    
#     query, params = build_json_field_query(table_details, columns, qry_params)
    
#     # Convert the sql.Composed object to a string
#     query_string = query.as_string(table_details.connection)
    
#     return query_string, params

# def build_json_field_query(
#     table_details: TableDetails, 
#     columns: List[str], 
#     qry_params: JSONFieldQuery
# ) -> Tuple[sql.Composed, List[Any]]:
#     conditions = []
#     params = []

#     for json_path, search_value in qry_params.conditions.items():
#         json_condition = build_json_condition(table_details.json_column_name, json_path, search_value)
#         conditions.append(json_condition)
#         params.append(search_value)

#     where_clause = sql.SQL(" AND ").join(conditions)
    
#     query = sql.SQL("""
#         SELECT {fields}
#         FROM {table}
#         WHERE {where_clause}
#     """).format(
#         fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
#         table=sql.Identifier(table_details.table_name),
#         where_clause=where_clause
#     )
    
#     return query, tuple(params)

# # ... (rest of the code remains the same)

# # Example usage
# table_details = TableDetails(
#     table_name="your_table_name",
#     json_column_name="jsonb_column",
#     connection=your_database_connection  # Make sure to pass your database connection here
# )

# qry_params = JSONFieldQuery({
#     "*.info.sbi_status": "Created",
#     "*.info.telescope": "ska_mid",
#     "*.source": "ODA"
# })

# query_string, params = select_by_json_field_query(table_details, qry_params)

# print(query_string)
# print(params)

    


