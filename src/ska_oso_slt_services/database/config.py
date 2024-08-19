import os


class LogDBConfig:
    API_KEY_PATH = os.getenv("LOGDB_API_KEY_PATH", "nakshatra.token")
    CA_CERTIFICATE_PATH = os.getenv("LOGDB_CA_CERT_PATH", "ca-certificate.crt")
    CLIENT_CERT_PATH = os.getenv("LOGDB_CLIENT_CERT_PATH", "apikey.nakshatra.crt")
    CLIENT_KEY_PATH = os.getenv("LOGDB_CLIENT_KEY_PATH", "apikey.nakshatra.key")
    HOST = os.getenv("LOGDB_HOST", "https://logging.stfc.skao.int:9200")
    CONNECTIONS_PER_NODE = int(os.getenv("LOGDB_CONNECTIONS_PER_NODE", "10"))


class EDADBConfig:
    DATABASE = os.getenv("EDA_DB_DATABASE", "ska_archiver_master")
    USER = os.getenv("EDA_DB_USER", "admin")
    PASSWORD = os.getenv("EDA_DB_PASSWORD")
    PORT = int(os.getenv("EDA_DB_PORT", "5432"))
    HOST = os.getenv(
        "EDA_DB_HOST", "timescaledb.ska-eda-mid-db.svc.techops.internal.skao.int"
    )
