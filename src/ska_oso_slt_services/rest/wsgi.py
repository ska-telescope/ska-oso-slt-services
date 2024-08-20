"""
SLT REST server entry point.
"""

import logging

from ska_db_oda.rest.wsgi import UniformLogger  # noqa: F401

from ska_oso_slt_services.rest import init_app

app = init_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
else:
    # presume being run from gunicorn
    # use gunicorn logging level for app and module loggers
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.setLevel(gunicorn_logger.level)
    logger = logging.getLogger("ska_oso_slt_services")
    logger.setLevel(gunicorn_logger.level)
