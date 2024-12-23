import logging
from typing import Any, List, Optional, Tuple

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
            # temporary SLT table creation code
            table_creator = get_table_creator()
            table_creator.create_slt_table()
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.fetchone()
        except (DatabaseError, InternalError, DataError) as e:
            # Handle database-related exceptions
            LOGGER.info("Error executing insert query: %s", e)
            # conn.rollback()
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
            # temporary SLT table creation code
            table_creator = get_table_creator()
            table_creator.create_slt_table()
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


# SLT Table creation added temporary once ODA start supporting for table creation
# then remove this piece of code


class TableCreator:
    _instance: Optional["TableCreator"] = None
    _postgres_connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def postgres_connection(self):
        if self._postgres_connection is None:
            self._postgres_connection = PostgresConnection().get_connection()
        return self._postgres_connection

    def create_slt_table(self):
        create_table_query = sql.SQL(
            """
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                shift_start TIMESTAMPTZ NOT NULL,
                shift_end TIMESTAMPTZ,
                shift_operator VARCHAR(100) NOT NULL,
                shift_logs JSONB,
                annotations TEXT,
                created_by VARCHAR(50) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_by VARCHAR(50) NOT NULL,
                last_modified_on TIMESTAMPTZ NOT NULL,
                CONSTRAINT unique_shift UNIQUE (shift_id, shift_start),
                CONSTRAINT unique_shift_id UNIQUE (shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_id
            ON public.tab_oda_slt (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_start
            ON public.tab_oda_slt (shift_start);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_comments (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                comment TEXT,
                image jsonb NULL,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_on TIMESTAMPTZ NOT NULL,
                last_modified_by VARCHAR(100) NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_comments_shift_id
            ON public.tab_oda_slt_shift_comments (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_comments_operator_name
            ON public.tab_oda_slt_shift_comments (operator_name);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_log_comments (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                eb_id VARCHAR(60) NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                log_comment TEXT,
                image jsonb NULL,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_by VARCHAR(100) NOT NULL,
                last_modified_on TIMESTAMPTZ NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_shift_id
            ON public.tab_oda_slt_shift_log_comments (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_eb_id
            ON public.tab_oda_slt_shift_log_comments (eb_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_log_comments_operator_name
            ON public.tab_oda_slt_shift_log_comments (operator_name);
            CREATE TABLE IF NOT EXISTS public.tab_oda_slt_shift_annotations (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(50) NOT NULL,
                operator_name VARCHAR(100) NOT NULL,
                annotation TEXT,
                created_by VARCHAR(100) NOT NULL,
                created_on TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified_on TIMESTAMPTZ NOT NULL,
                last_modified_by VARCHAR(100) NOT NULL,
                CONSTRAINT fk_shift FOREIGN KEY (shift_id)
                REFERENCES public.tab_oda_slt(shift_id)
            );
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_annotations_shift_id
            ON public.tab_oda_slt_shift_annotations (shift_id);
            CREATE INDEX IF NOT EXISTS idx_tab_oda_slt_shift_annotations_operator_name
            ON public.tab_oda_slt_shift_annotations (operator_name);
        """
        )
        try:
            with self.postgres_connection.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(create_table_query)
                    conn.commit()
            LOGGER.info("SLT table and index created successfully.")
        except Exception as e:
            LOGGER.error("Error creating SLT table: %s", {str(e)})
            raise


def get_table_creator():
    return TableCreator()
