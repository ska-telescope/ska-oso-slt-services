import os


def create_connection_pool() -> "ConnectionPool":
    conninfo = (
        f"host={os.environ.get('POSTGRES_HOST')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB_NAME', 'postgres')} "
        f"user={os.environ.get('ADMIN_POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('ADMIN_POSTGRES_PASSWORD')}"
    )

    connect_kwargs = {"row_factory": "dict_row"}

    return "ConnectionPool(conninfo, kwargs=connect_kwargs)"
