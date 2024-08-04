from ssl import create_default_context
from threading import Lock

from elasticsearch import Elasticsearch

from ska_oso_slt_services.database.config import LogDBConfig


class LOGDBConnection:
    """
    LOG DB Connection Class
    """

    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LOGDBConnection, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._es = self._create_connection()
            self._initialized = True

    def _create_connection(self) -> Elasticsearch:
        """
        Create Log DB Connection
        :return: Log DB Connection
        """
        # Load the API key from the file
        with open(LogDBConfig.API_KEY_PATH, "r") as file:
            api_key = file.read().strip()

        ssl_context = create_default_context(cafile=LogDBConfig.CA_CERTIFICATE_PATH)
        ssl_context.load_cert_chain(
            certfile=LogDBConfig.CLIENT_CERT_PATH, keyfile=LogDBConfig.CLIENT_KEY_PATH
        )

        es = Elasticsearch(
            [LogDBConfig.HOST],
            api_key=api_key,
            ssl_context=ssl_context,
            connections_per_node=LogDBConfig.CONNECTIONS_PER_NODE,
        )

        return es

    def get_client(self) -> Elasticsearch:
        """
        Get Log DB Connection
        :return: Log DB Connection
        """
        return self._es


if __name__ == "__main__":
    logdb_connection = LOGDBConnection()
    es_client = logdb_connection.get_client()

    print(f"Health: {es_client.cluster.health()['status']}")
