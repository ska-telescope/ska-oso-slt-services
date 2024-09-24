import logging
from http import HTTPStatus
from traceback import format_exc
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from psycopg import DatabaseError, DataError, InternalError

from ska_oso_slt_services.domain.app_model import ErrorDetails, ErrorResponseTraceback

LOGGER = logging.getLogger(__name__)


def error_details(
    status: HTTPStatus,
    title: str,
    detail: str,
    traceback: Optional[ErrorResponseTraceback],
):
    return ErrorDetails(
        status=status, title=title, detail=detail, traceback=traceback
    ).model_dump(mode="json", exclude_none=True)


class BadRequestError(HTTPException):
    """Custom class to ensure our errors are formatted consistently"""

    code = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        status_code = status_code or self.code
        detail = detail or self.code.description

        super().__init__(status_code=status_code, detail=detail)


class UnprocessableEntityError(BadRequestError):
    code = HTTPStatus.UNPROCESSABLE_ENTITY

    def __init__(self, detail: Optional[str] = None):
        super().__init__(detail=detail)


class NotFoundError(BadRequestError):
    code = HTTPStatus.NOT_FOUND

    def __init__(self, detail: Optional[str] = None):
        super().__init__(detail=detail)


def _make_response(
    status: HTTPStatus, detail: str, traceback: Optional[ErrorResponseTraceback] = None
) -> JSONResponse:
    """
    Utility helper to generate a JSONResponse to be returned by custom error handlers.
    """
    details = error_details(
        status, title=status.phrase, detail=detail, traceback=traceback
    )
    return JSONResponse(
        status_code=status,
        content={"detail": details},
    )


def record_not_found_handler(_: Request, err: KeyError) -> JSONResponse:
    """
    A custom handler function to deal with KeyError raised by the SLT and
    return the correct HTTP 404 response.
    """
    return _make_response(
        HTTPStatus.BAD_REQUEST,
        detail=repr(err),
        traceback=ErrorResponseTraceback(
            key=HTTPStatus.BAD_REQUEST.phrase,
            type=str(type(err)),
            full_traceback=format_exc(),
        ),
    )


def database_error_handler(
    _: Request, err: DatabaseError | DataError | InternalError
) -> JSONResponse:
    return internal_server_handler(_, err)


def internal_server_handler(_: Request, err: Exception) -> JSONResponse:
    """
    A custom handler function that returns a verbose HTTP 500 response containing
    detailed traceback information.

    This is a 'DANGEROUS' handler because it exposes internal implementation details to
    clients. Do not use in production systems!
    """
    return _make_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        detail=repr(err),
        traceback=ErrorResponseTraceback(
            key=HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            type=str(type(err)),
            full_traceback=format_exc(),
        ),
    )
