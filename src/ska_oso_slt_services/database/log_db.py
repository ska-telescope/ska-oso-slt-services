# pylint: disable=no-member,
from ssl import create_default_context

from elasticsearch import Elasticsearch


class LogDB:
    def __init__(self, config) -> None:

        self.config = config

    def read_api_key(self) -> str:
        with open(  # pylint: disable=unspecified-encoding
            self.config.DB_API_KEY_PATH, "r"
        ) as file:
            return file.read().strip()

    def create_ssl_context(self) -> None:

        ssl_context = create_default_context(cafile=self.config.DB_CA_CERT_PATH)
        ssl_context.load_cert_chain(
            certfile=self.config.DB_CLIENT_CERT_PATH,
            keyfile=self.config.DB_CLIENT_KEY_PATH,
        )

    def create_client(self) -> None:

        return Elasticsearch(
            [
                f"{self.config.DB_BASE_URL}:{self.config.DB_PORT}"
            ],  # Adjust the host and port appropriately
            api_key=self.api_key,
            ssl_context=self.config.ssl_context,
        )
