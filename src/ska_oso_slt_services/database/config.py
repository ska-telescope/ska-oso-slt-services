import os


# class LogDBConfig:
#
#     DB_API_KEY_PATH = "./files/nakshatra.token"
#     DB_CA_CERT_PATH = "./files/ca-certificate.crt"
#     DB_CLIENT_CERT_PATH = "./files/apikey.nakshatra.crt"
#     DB_CLIENT_KEY_PATH = "./files/apikey.nakshatra.key"
#     DB_BASE_URL = "https://logging.stfc.skao.int"
#     DB_PORT = 9200

class LogDBConfig:
    API_KEY_PATH = os.getenv('LOGDB_API_KEY_PATH', 'nakshatra.token')
    CA_CERTIFICATE_PATH = os.getenv('LOGDB_CA_CERT_PATH', 'ca-certificate.crt')
    CLIENT_CERT_PATH = os.getenv('LOGDB_CLIENT_CERT_PATH', 'apikey.nakshatra.crt')
    CLIENT_KEY_PATH = os.getenv('LOGDB_CLIENT_KEY_PATH', 'apikey.nakshatra.key')
    HOST = os.getenv('LOGDB_HOST', 'https://logging.stfc.skao.int:9200')
    CONNECTIONS_PER_NODE = int(os.getenv('LOGDB_CONNECTIONS_PER_NODE', 10))


# class EDAConfig:
#
#     DB_HOST = os.environ.get("DB_HOST")
#     DB_NAME = os.environ.get("DB_NAME")
#     DB_USER = os.environ.get("DB_USER")
#     DB_PASSWORD = os.environ.get("DB_PASSWORD")
#     DB_PORT = os.environ.get("DB_PORT")
#     DB_CLUSTER_PORT = os.environ.get("DB_CLUSTER_PORT")


class EDADBConfig:
    DATABASE = os.getenv('EDA_DB_DATABASE', 'ska_archiver_master')
    USER = os.getenv('EDA_DB_USER', 'admin')
    PASSWORD = os.getenv('EDA_DB_PASSWORD')
    PORT = int(os.getenv('EDA_DB_PORT', 5432))
    HOST = os.getenv('EDA_DB_HOST', 'timescaledb.ska-eda-mid-db.svc.techops.internal.skao.int')


# class ODAConfig:
#
#     DB_HOST = os.environ.get("DB_HOST", "http://192.168.1.9")
#     DB_PORT = os.environ.get("DB_PORT", 5002)
#     ODA_MAJOR_VERSION = 5
#     DB_BASE_URL = os.environ.get(
#         "DB_BASE_URL", f"ska-db-oda/oda/api/v{ODA_MAJOR_VERSION}/"
#     )
#     DB_URL = f"{DB_HOST}:{DB_PORT}/{DB_BASE_URL}"
#     STATUS_API = "/status/sbis/"
#
#
# class SLTConfig:
#
#     SLT_TABLE_NAME = "tab_oda_slt"
#     SLT_LOG_TABLE_NAME = "tab_oda_slt_log"
#     SLT_IMAGE_TABLE_NAME = "tab_oda_slt_image"
