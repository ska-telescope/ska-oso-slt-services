import os
from os import getenv

AWS_SERVER_PUBLIC_KEY = os.getenv("AWS_SERVER_PUBLIC_KEY", "AWS_SERVER_PUBLIC_KEY")
AWS_SERVER_SECRET_KEY = os.getenv("AWS_SERVER_SECRET_KEY", "AWS_SERVER_SECRET_KEY")
AWS_SLT_BUCKET_NAME = os.getenv("AWS_SERVER_BUCKET_NAME", "AWS_SERVER_BUCKET_NAME")
AWS_REGION_NAME = os.getenv("AWS_SERVER_BUCKET_REGION", "AWS_SERVER_BUCKET_REGION")
ODA_DATA_POLLING_TIME = int(os.getenv("ODA_DATA_POLLING_TIME", "20"))
AWS_SERVICE_NAME = "s3"
AWS_BUCKET_URL = "s3.amazonaws.com"

SKUID_URL = getenv("SKUID_URL", "http://ska-ser-skuid-test-svc:9870")

SKUID_ENTITY_TYPE = "sl"
TELESCOPE_TYPE = getenv("telescope", "l")
