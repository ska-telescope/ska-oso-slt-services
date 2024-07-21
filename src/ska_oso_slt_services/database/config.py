import os


class LogDBConfig:

    DB_API_KEY_PATH = "./files/nakshatra.token"
    DB_CA_CERT_PATH = "./files/ca-certificate.crt"
    DB_CLIENT_CERT_PATH = "./files/apikey.nakshatra.crt"
    DB_CLIENT_KEY_PATH = "./files/apikey.nakshatra.key"
    DB_BASE_URL = "https://logging.stfc.skao.int"
    DB_PORT = 9200


class EDAConfig:

    DB_HOST = os.environ.get("DB_HOST")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_PORT = os.environ.get("DB_PORT")
    DB_CLUSTER_PORT = os.environ.get("DB_CLUSTER_PORT")


class ODAConfig:

    DB_HOST = os.environ.get("DB_HOST", "http://192.168.1.102")
    DB_PORT = os.environ.get("DB_PORT", 5000)
    ODA_MAJOR_VERSION = 5
    DB_BASE_URL = os.environ.get(
        "DB_BASE_URL", f"ska-db-oda/oda/api/v{ODA_MAJOR_VERSION}/"
    )
    DB_URL = f"{DB_HOST}:{DB_PORT}/{DB_BASE_URL}"
    STATUS_API = "/status/sbis/"
