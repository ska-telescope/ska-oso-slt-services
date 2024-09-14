from enum import Enum
from threading import Lock
from typing import List, Tuple

from psycopg import Connection, DatabaseError, sql
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
    """
    Postgres Data Access Class

    """

    def __init__(self):
        self.postgres_connection = PostgresConnection().get_connection()


class PostgresDataAccess:
    """
    Postgres Data Access Class
    """

    def __init__(self):
        self.postgres_connection = PostgresConnection().get_connection()

    async def insert(self, query: sql.Composed, params: Tuple):
        """
        Insert data into the database.

        :param query: The SQL query to be executed.
        :param params: The parameters for the query.
        :return: The ID of the inserted row.
        """
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchone()
        except DatabaseError as e:
            # Handle database-related exceptions
            print(f"Error executing insert query: {e}")
            conn.rollback()
            raise
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            raise

    async def update(self, query: sql.Composed, params: Tuple):
        """
        Update data in the database.

        :param query: The SQL query to be executed.
        :param params: The parameters for the query.
        :return: The number of rows affected.
        """
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount
        except DatabaseError as e:
            # Handle database-related exceptions
            print(f"Error executing update query: {e}")
            conn.rollback()
            raise
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            raise

    def delete(self, query: str, connection):
        pass

    async def get(self, query: sql.Composed, params: Tuple):
        """
        Get data from the database.

        :param query: The SQL query to be executed.
        :param connection: The database connection object.
        :return: The result of the query.
        """
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchall()
        except DatabaseError as e:
            # Handle database-related exceptions
            print(f"Error executing get query: {e}")
            raise
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            raise

    async def get_one(self, query: sql.Composed, params: Tuple):
        """
        Get one row from the database.

        :param query: The SQL query to be executed.
        :param params: The parameters for the query.
        :return: The result of the query.
        """
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchone()
        except DatabaseError as e:
            # Handle database-related exceptions
            print(f"Error executing get_one query: {e}")
            raise
        except Exception as e:
            # Handle other exceptions
            print(f"Unexpected error: {e}")
            raise
