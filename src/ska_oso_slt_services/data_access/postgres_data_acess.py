from enum import Enum
from threading import Lock

from psycopg import DatabaseError
from ska_db_oda.unit_of_work.postgresunitofwork import create_connection_pool
#conn_pool = create_connection_pool()



class QueryType(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"



class PostgresConnection:
    _instance = None
    _lock = Lock()  

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:  
                if cls._instance is None:  
                    cls._instance = super(PostgresConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  
            self._connection_pool = create_connection_pool()
            self._initialized = True

    def get_connection(self):
        return self._connection_pool


class PostgresDataAccess:
    def __init__(self):
        self.connection_pool = PostgresConnection().get_connection()

    def execute_query_or_update(
        self, query: str, query_type: QueryType, params: tuple = None
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
                        returned_id = None
                        if query_type == QueryType.POST:
                            returned_id = cursor.fetchone()
                        conn.commit()
                        return returned_id  # if returned_id else None
                    else:
                        raise ValueError(f"Unsupported query type: {query_type}")
        except (Exception, DatabaseError) as error:
            raise DatabaseError(
                f"Error executing {query_type.value} query: {query} with params:"
                f" {params}. Error: {str(error)}"
            )