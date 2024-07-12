"""
The flask_SLT module contains code used to interface Flask applications with
the SLT.
"""

import logging

from flask import _app_ctx_stack, current_app  # pylint: disable=no-name-in-module

# from ska_db_oda.unit_of_work.postgresunitofwork import (
#     create_connection_pool,
# )
from flask_sqlalchemy import SQLAlchemy

LOGGER = logging.getLogger(__name__)

BACKEND_VAR = "SLT_BACKEND_TYPE"


class FlaskSLT(object):
    """
    FlaskSLT is a small Flask extension that makes the SLT backend available to
    Flask apps.

    This extension present two properties that can be used by Flask code to access
    the SLT. The extension should ensure that the correct scope is used; that is,
    one unique repository per Flask app and a unique UnitOfWork per HTTP request.

    The backend type is set by the SLT_BACKEND_TYPE environment variable.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialise SLT Flask extension.
        """
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            "https://k8s-cicd.skao.int/integration-ska-db-oda/api/v5/"
        )
        app.config["SQLALCHEMY_BINDS"] = {
            "ED": "sqlite:////path/2/uk.db",
            "Log DB": "sqlite:////path/2/us.db",
        }

        app = SQLAlchemy(app)

    @property
    def uow(self):
        # Lazy creation of one UnitOfWork instance per HTTP request
        # UoW instances are not shared as concurrent modification of a single
        # UoW could easily lead to corruption
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "uow"):

                return ctx.uow

    @property
    def connection_pool(self):
        # Lazy creation of one psycopg ConnectionPool instance per Flask application
        if not hasattr(current_app, "connection_pool"):
            current_app.connection_pool = create_connection_pool()
        return current_app.connection_pool
