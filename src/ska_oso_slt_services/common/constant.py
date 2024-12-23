from os import getenv

AWS_SERVER_PUBLIC_KEY = getenv("AWS_SERVER_PUBLIC_KEY", "AWS_SERVER_PUBLIC_KEY")
AWS_SERVER_SECRET_KEY = getenv("AWS_SERVER_SECRET_KEY", "AWS_SERVER_SECRET_KEY")
AWS_SLT_BUCKET_NAME = getenv("AWS_SERVER_BUCKET_NAME", "AWS_SERVER_BUCKET_NAME")
AWS_REGION_NAME = getenv("AWS_SERVER_BUCKET_REGION", "AWS_SERVER_BUCKET_REGION")
ODA_DATA_POLLING_TIME = int(getenv("ODA_DATA_POLLING_TIME", "20"))
AWS_SERVICE_NAME = "s3"
AWS_BUCKET_URL = "s3.amazonaws.com"

SKUID_URL = getenv("SKUID_URL", "http://ska-ser-skuid-test-svc:9870")

SKUID_ENTITY_TYPE = "sl"


def set_telescope_type(env_variable: str):

    TELESCOPE_TYPE = getenv(env_variable, "m")

    if "mid" in TELESCOPE_TYPE.lower():
        return "m"
    if "low" in TELESCOPE_TYPE.lower():
        return "l"
    return "m"
