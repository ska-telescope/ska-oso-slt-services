import logging
from typing import Any, List, Tuple

from psycopg import DatabaseError, DataError, InternalError, sql

from ska_oso_slt_services.infrastructure.postgres_connection import PostgresConnection

LOGGER = logging.getLogger(__name__)


class PostgresDataAccess:
    """
    Postgres Data Access Class
    """

    def __init__(self):
        self.postgres_connection = PostgresConnection().get_connection()

    def insert(self, query: sql.Composed, params: Tuple) -> int:
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
        except (DatabaseError, InternalError, DataError) as e:
            # Handle database-related exceptions
            LOGGER.info("Error executing insert query: %s", e)
            conn.rollback()
            raise e
        except Exception as e:
            # Handle other exceptions
            LOGGER.info("Unexpected error: %s", e)
            raise e

    def update(self, query: sql.Composed, params: Tuple) -> int:
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
        except (DatabaseError, InternalError, DataError) as e:
            # Handle database-related exceptions
            LOGGER.info("Error executing update query: %s", e)
            conn.rollback()
            raise e
        except Exception as e:
            # Handle other exceptions
            LOGGER.info("Unexpected error: %s", e)
            raise e

    def delete(self, query: str, connection):
        pass

    def get(self, query: sql.Composed, params: Tuple) -> List[Tuple[int, str]]:
        """
        Get data from the database.

        :param query: The SQL query to be executed (as sql.Composed).
        :param params: The parameters for the SQL query.
        :return: The result of the query.
        """
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    return cursor.fetchall()
        except (DatabaseError, InternalError, DataError) as e:
            LOGGER.error("Error executing get query: %s", e)
            raise
        except Exception as e:
            LOGGER.error("Unexpected error: %s", e)
            raise

    def get_one(self, query: sql.Composed, params: Tuple) -> Tuple[Any, ...]:
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
        except (DatabaseError, InternalError, DataError) as e:
            # Handle database-related exceptions
            LOGGER.info("Error executing single record query: %s", e)
            raise e
        except Exception as e:
            # Handle other exceptions
            LOGGER.info("Unexpected error: %s", e)
            raise e
