import os


def create_connection_pool() -> None:
    conninfo = (
        f"host={os.environ.get('POSTGRES_HOST')} "
        f"port={os.environ.get('POSTGRES_PORT', '5432')} "
        f"dbname={os.environ.get('POSTGRES_DB_NAME', 'postgres')} "
        f"user={os.environ.get('ADMIN_POSTGRES_USER', 'postgres')} "
        f"password={os.environ.get('ADMIN_POSTGRES_PASSWORD')}"
    )

    connect_kwargs = {"row_factory": "dict_row"}

    conninfo = (
        "host=localhost port=5432 dbname=postgres user=postgres password=mynewpassword"
    )

    return {connect_kwargs: conninfo}
