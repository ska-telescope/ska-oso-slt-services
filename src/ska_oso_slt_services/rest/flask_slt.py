"""
The flask_SLT module contains code used to interface Flask applications with
the SLT.
"""


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
