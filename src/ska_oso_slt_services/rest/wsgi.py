"""
SLT REST server entry point.
"""

import logging

from flask_cors import CORS
from ska_db_oda.rest.wsgi import UniformLogger  # noqa: F401

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresDataAccess, PostgresConnection
from ska_oso_slt_services.rest import init_app

app = init_app()
CORS(app)


def create_oda_slt_table():
    """
    Create SLT Table tab_oda_slt in ODA DB
    """
    query = """
        CREATE TABLE tab_oda_slt (
                id SERIAL PRIMARY KEY,
                shift_id VARCHAR(255),
                shift_start TIMESTAMP,
                shift_end TIMESTAMP,
                shift_operator JSONB,
                shift_logs JSONB,
                media JSONB,
                annotations TEXT,
                comments TEXT,
                created_by VARCHAR(255),
                created_time TIMESTAMP,
                last_modified_by VARCHAR(255),
                last_modified_time TIMESTAMP
        );
                """
    table_exist_query = """ 
    SELECT EXISTS ( SELECT 1 FROM pg_tables WHERE tablename = 'tab_oda_slt' )
     AS table_existence; 
                        """

    connection_pool = PostgresConnection().get_connection()
    with connection_pool.connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(table_exist_query)
            table_exist = cursor.fetchone()["table_existence"]

    if table_exist:
        print("---------------> Table Already present")

    if not table_exist:
        print("---------------> Creating Table")
        with connection_pool.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                cursor.execute(table_exist_query)
                table_exist = cursor.fetchone()["table_existence"]
                if table_exist:
                    print("----------> Table created successfully")


if __name__ == "__main__":
    create_oda_slt_table()
    app.run(host="0.0.0.0", port=5000)
else:
    # presume being run from gunicorn
    # use gunicorn logging level for app and module loggers
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.setLevel(gunicorn_logger.level)
    logger = logging.getLogger("ska_oso_slt_services")
    logger.setLevel(gunicorn_logger.level)
