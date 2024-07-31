from threading import Lock

from pyhdbpp.timescaledb import TimescaleDbReader

from ska_oso_slt_services.database.config import EDADBConfig


class EDADBConnection:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  
                    cls._instance = super(EDADBConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  
            self._reader = self._create_connection()
            self._initialized = True

    def _create_connection(self):
        return TimescaleDbReader({
            'database': EDADBConfig.DATABASE,
            'user': EDADBConfig.USER,
            'password': EDADBConfig.PASSWORD,
            'port': EDADBConfig.PORT,
            'host': EDADBConfig.HOST
        })

    def get_connection(self):
        return self._reader


