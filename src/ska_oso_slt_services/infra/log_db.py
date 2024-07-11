from elasticsearch import Elasticsearch
from ssl import create_default_context


class LogDB:

    def __init__(self) -> None:

        self.api_key_path = 'nakshatra.token'
        self.ca_certificate_path = 'ca-certificate.crt'
        self.client_cert_path = 'apikey.nakshatra.crt'
        self.client_key_path = 'apikey.nakshatra.key'
        self.base_url = 'https://logging.stfc.skao.int'
        self.port = 9200

    def read_api_key(self) -> str:
        with open(self.api_key_path, 'r') as file:
            return file.read().strip()
        
    def create_ssl_context(self) -> None:

        ssl_context = create_default_context(cafile=self.ca_certificate_path)
        ssl_context.load_cert_chain(certfile=self.client_cert_path, keyfile=self.client_key_path)

    def create_client(self) -> None:

        return Elasticsearch(
                [f'{self.base_url}:{self.port}'],  # Adjust the host and port appropriately
                api_key=self.api_key,
                ssl_context=self.ssl_context
            )