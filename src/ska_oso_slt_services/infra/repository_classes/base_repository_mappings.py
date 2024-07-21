import json
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from psycopg import DatabaseError
from connection_init import connection_pool


class QueryType(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


def convert_value(value):
    """
    Convert values to appropriate types for database insertion.
    """
    if isinstance(value, dict):
        return json.dumps(value)
    elif isinstance(value, list):
        return '{' + ','.join(f'"{item}"' for item in value) + '}'
    return value


class BaseRepository:
    def __init__(self, table_name: str):
        """
        Initializes the BaseRepository with a table name and connection pool.

        :param table_name: The name of the database table.
        """
        self.pool = connection_pool
        self.table_name = table_name

    def _execute_query_or_update(self, query: str, query_type: QueryType, params: tuple = None):
        """
        Executes a query or update operation on the database.

        :param query: The SQL query to be executed.
        :param query_type: The type of query (GET, POST, PUT, DELETE).
        :param params: Parameters to be used in the SQL query.
        :return: The result of the query if query_type is GET; otherwise, None.
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if query_type == QueryType.GET:
                        return cursor.fetchall()
                    elif query_type in {QueryType.POST, QueryType.PUT, QueryType.DELETE}:
                        returned_id = None
                        if query_type == QueryType.POST:
                            returned_id = cursor.fetchone()
                            print(f"{returned_id=}")
                        conn.commit()
                        return returned_id #if returned_id else None
                    else:
                        raise ValueError(f"Unsupported query type: {query_type}")
        except (Exception, DatabaseError) as error:
            raise DatabaseError(f"Error executing {query_type.value} query: {query} with params: {params}. Error: {str(error)}")

    def get_records_by_id_or_by_slt_ref(self, record_id: Optional[int] = None, slt_ref: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves records from the table. If record_id is provided, fetches the specific record.

        :param record_id: Optional; ID of the record to fetch.
        :param slt_ref: Optional; slt_ref ID of the record to fetch.
        :return: List of records as dictionaries.
        """
        base_query = f"SELECT * FROM {self.table_name}"
        if record_id:
            query = base_query + (f" WHERE id = %s" if record_id is not None else "")
            params = (record_id,) if record_id is not None else None
        else:
            query = base_query + (f" WHERE slt_ref = %s" if slt_ref is not None else "")
            params = (slt_ref,) if slt_ref is not None else None

        return self._execute_query_or_update(query=query, query_type=QueryType.GET, params=params) or []

    def insert(self, record: Dict[str, Any]):
        """
        Inserts a new record into the table.

        :param record: Dictionary containing the record data to be inserted.
        """
        try:
            #record = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in record.items()}
            record['id'] = int(datetime.utcnow().timestamp())
            record["created_on"] = datetime.utcnow()
            record["last_modified_on"] = datetime.utcnow()

            # Convert all values in the record to the appropriate types
            converted_record = {k: convert_value(v) for k, v in record.items()}

            columns = ', '.join(converted_record.keys())
            placeholders = ', '.join(["%s"] * len(converted_record))
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders} ) RETURNING id"

            return self._execute_query_or_update(query=query, query_type=QueryType.POST, params=tuple(converted_record.values()))

        except (Exception, DatabaseError) as error:
            raise DatabaseError(f"Error inserting record into table: {self.table_name}. Error: {str(error)}")

    def update_record_by_id_or_slt_ref(self, record, slt_ref=None,record_id=None):
        try:
            record['last_modified_on'] = datetime.utcnow()
            set_clause = ', '.join([f"{col} = %s" for col in record.keys()])
            base_query = f"UPDATE {self.table_name} SET {set_clause}"

            if slt_ref:
                query = base_query + f" WHERE slt_ref = {slt_ref}"
            else: #record
                query = base_query + f" WHERE id = {record_id}"

            onverted_record = {k: convert_value(v) for k, v in record.items()}
            params = tuple(onverted_record[col] for col in onverted_record.keys())
            self._execute_query_or_update(query=query, query_type=QueryType.PUT, params=params)
        except (Exception, DatabaseError) as error:
            raise DatabaseError(f"Error updating record in table: {self.table_name}. Error: {str(error)}")

    def delete_by_id(self, record_id: int):
        """
        Deletes a record from the table by id.

        :param record_id: ID of the record to delete.
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = %s"
            params = (record_id,)

            self._execute_query_or_update(query=query, query_type=QueryType.DELETE, params=params)
        except (Exception, DatabaseError) as error:
            raise DatabaseError(f"Error deleting record from table: {self.table_name}. Error: {str(error)}")


