import logging
from threading import Lock

from psycopg_pool import ConnectionPool
from ska_db_oda.unit_of_work.postgresunitofwork import create_connection_pool

LOGGER = logging.getLogger(__name__)


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
