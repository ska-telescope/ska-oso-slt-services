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
from infra.postgresql import create_connection_pool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import Pool

LOGGER = logging.getLogger(__name__)

BACKEND_VAR = "SLT_BACKEND_TYPE"


def get_conn(pool):
    return pool.getconn()


class Psycopg3ConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self, *args, **kwargs):
        return self.conn.cursor(*args, **kwargs)

    def commit(self):
        return self.conn.commit()

    def rollback(self):
        return self.conn.rollback()

    def close(self):
        return self.conn.close()


class Psycopg3ConnectionPool(Pool):
    def __init__(self, creator, *args, **kwargs):
        self._creator = creator
        super().__init__(creator, *args, **kwargs)

    def _create_connection(self):
        return Psycopg3ConnectionWrapper(self._creator())

    def _do_get(self):
        return self._create_connection()

    def _do_return_conn(self, conn):
        pool.putconn(conn.conn)

    def _do_close(self, conn):
        conn.close()


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

        pool = create_connection_pool()

        engine = create_engine(
            "postgresql+psycopg://", poolclass=Psycopg3ConnectionPool, creator=get_conn
        )
        session_pool = sessionmaker(bind=engine)

        # app.config["SQLALCHEMY_DATABASE_URI"] = (
        #     "https://k8s-cicd.skao.int/integration-ska-db-oda/api/v5/"
        # )
        # app.config["SQLALCHEMY_BINDS"] = {
        #     "ED": "sqlite:////path/2/uk.db",
        #     "Log DB": "sqlite:////path/2/us.db",
        # }

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
