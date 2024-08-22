from enum import Enum
from threading import Lock
from typing import List

from psycopg import DatabaseError
from psycopg_pool import ConnectionPool
from ska_db_oda.unit_of_work.postgresunitofwork import create_connection_pool


class QueryType(Enum):
    """
    Enum class for query types
    """

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class PostgresConnection:
    """
    Postgres Connection Class
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(PostgresConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._connection_pool = create_connection_pool()
            self._initialized = True

    def get_connection(self) -> ConnectionPool:
        """
        Get Postgres Connection
        :return: Postgres Connection
        """
        return self._connection_pool


class PostgresDataAccess:
    def __init__(self):
        self.connection_pool = PostgresConnection().get_connection()

    def execute_query_or_update(
        self, query: str, query_type: QueryType, params: tuple | List = None
    ):
        """
        Executes a query or update operation on the database.

        :param query: The SQL query to be executed.
        :param query_type: The type of query (GET, POST, PUT, DELETE).
        :param params: Parameters to be used in the SQL query.
        :return: The result of the query if query_type is GET; otherwise, None.
        """
        try:
            with self.connection_pool.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if query_type == QueryType.GET:
                        return cursor.fetchall()
                    elif query_type in {
                        QueryType.POST,
                        QueryType.PUT,
                        QueryType.DELETE,
                    }:
                        returned_id_or_data = None
                        if query_type == QueryType.POST:
                            returned_id_or_data = cursor.fetchone()
                        conn.commit()
                        return returned_id_or_data
                    else:
                        raise ValueError(f"Unsupported query type: {query_type}")
        except (Exception, DatabaseError) as error:
            raise DatabaseError(  # pylint: disable=raise-missing-from
                f"Error executing {query_type.value} query: {query} with params:"
                f" {params}. Error: {str(error)}"
            )
