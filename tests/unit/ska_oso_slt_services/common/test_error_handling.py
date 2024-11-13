from http import HTTPStatus

import pytest
from fastapi.responses import JSONResponse
from psycopg import DatabaseError, DataError, InternalError

from ska_oso_slt_services.common.error_handling import (
    BadRequestError,
    FileExists,
    NotFoundError,
    UnprocessableEntityError,
    _make_response,
    database_error_handler,
    error_details,
    internal_server_handler,
    record_not_found_handler,
)


# Test error_details function
def test_error_details_with_all_parameters():
    status = HTTPStatus.BAD_REQUEST
    title = "Bad Request"
    detail = "Invalid input"

    result = error_details(status, title, detail, None)
    assert result["status"] == status
    assert result["title"] == title
    assert result["detail"] == detail


def test_error_details_without_traceback():
    status = HTTPStatus.BAD_REQUEST
    title = "Bad Request"
    detail = "Invalid input"

    result = error_details(status, title, detail, None)

    assert result["status"] == status
    assert result["title"] == title
    assert result["detail"] == detail
    assert "traceback" not in result


# Test BadRequestError
def test_bad_request_error_with_default_values():
    error = BadRequestError()
    assert error.status_code == HTTPStatus.BAD_REQUEST
    assert error.detail == HTTPStatus.BAD_REQUEST.description


def test_bad_request_error_with_custom_detail():
    custom_detail = "Custom error message"
    error = BadRequestError(detail=custom_detail)
    assert error.status_code == HTTPStatus.BAD_REQUEST
    assert error.detail == custom_detail


def test_bad_request_error_with_custom_status():
    custom_status = 418  # I'm a teapot
    error = BadRequestError(status_code=custom_status)
    assert error.status_code == custom_status


# Test UnprocessableEntityError
def test_unprocessable_entity_error():
    error = UnprocessableEntityError()
    assert error.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert error.detail == HTTPStatus.UNPROCESSABLE_ENTITY.description


def test_unprocessable_entity_error_with_custom_detail():
    custom_detail = "Custom unprocessable entity error"
    error = UnprocessableEntityError(detail=custom_detail)
    assert error.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert error.detail == custom_detail


# Test NotFoundError
def test_not_found_error():
    error = NotFoundError()
    assert error.status_code == HTTPStatus.NOT_FOUND
    assert error.detail == HTTPStatus.NOT_FOUND.description


# Test FileExists
def test_file_exists_error():
    error = FileExists()
    assert error.status_code == HTTPStatus.FOUND
    assert error.detail == HTTPStatus.FOUND.description


# Test _make_response
def test_make_response():
    status = HTTPStatus.BAD_REQUEST
    detail = "Test error"
    response = _make_response(status, detail)

    assert isinstance(response, JSONResponse)
    assert response.status_code == status
    assert response.body is not None


# Test record_not_found_handler
def test_record_not_found_handler():
    key_error = KeyError("Record not found")
    response = record_not_found_handler(None, key_error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == HTTPStatus.BAD_REQUEST


# Test database_error_handler
@pytest.mark.parametrize("error", [DatabaseError(), DataError(), InternalError()])
def test_database_error_handler(error):
    response = database_error_handler(None, error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


# Test internal_server_handler
def test_internal_server_handler():
    error = Exception("Test internal error")
    response = internal_server_handler(None, error)

    assert isinstance(response, JSONResponse)
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
