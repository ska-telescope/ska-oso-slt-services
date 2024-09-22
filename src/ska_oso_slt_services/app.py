"""
ska_oso_slt_services app.py
"""

import logging
import os
from importlib.metadata import version

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg import DatabaseError, DataError, InternalError

from ska_oso_slt_services.common import (
    database_error_handler,
    internal_server_handler,
    record_not_found_handler,
)
from ska_oso_slt_services.routers.shift_router import router

KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-oso-slt-services")
SLT_MAJOR_VERSION = version("ska-oso-slt-services").split(".")[0]

# The base path includes the namespace which is known at runtime
# to avoid clashes in deployments, for example in CICD
API_PREFIX = f"/{KUBE_NAMESPACE}/slt/api/v{SLT_MAJOR_VERSION}"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

LOGGER = logging.getLogger(__name__)


def create_app(production=PRODUCTION) -> FastAPI:
    """
    Create the Connexion application with required config
    """
    LOGGER.info("Creating FastAPI app")

    app = FastAPI(openapi_url=f"{API_PREFIX}/openapi.json", docs_url=f"{API_PREFIX}/ui")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(router, prefix=API_PREFIX)
    app.exception_handler(ValueError)(record_not_found_handler)
    app.exception_handler(DatabaseError)(database_error_handler)
    app.exception_handler(DataError)(database_error_handler)
    app.exception_handler(InternalError)(database_error_handler)
    if production:
        app.exception_handler(Exception)(internal_server_handler)
    return app


main = create_app()
