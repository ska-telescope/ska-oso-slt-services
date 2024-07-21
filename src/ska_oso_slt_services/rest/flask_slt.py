"""
The flask_SLT module contains code used to interface Flask applications with
the SLT.
"""

import logging
from os import getenv

from flask import _app_ctx_stack  # pylint: disable=no-name-in-module

from ska_oso_slt_services.infrastructure.postgresql import Postgresql

LOGGER = logging.getLogger(__name__)

ODA_BACKEND_TYPE = getenv("ODA_BACKEND_TYPE", "postgres")
BACKEND_VAR = "ODA_BACKEND_TYPE"


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

        app.extensions["slt"] = self

    @property
    def slt_uow(self):
        # Lazy creation of one UnitOfWork instance per HTTP request
        # UoW instances are not shared as concurrent modification of a single
        # UoW could easily lead to corruption
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "slt_uow"):

                slt_uow = Postgresql()
                ctx.slt_uow = slt_uow

                return ctx.slt_uow
