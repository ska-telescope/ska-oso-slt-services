"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import json
import logging
import traceback
from datetime import datetime
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, TypeVar, Union

import requests
from pydantic import ValidationError
from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import validation_response
from ska_db_oda.rest.flask_oda import FlaskODA

from ska_oso_slt_services.database.config import EDAConfig, LogDBConfig, ODAConfig
from ska_oso_slt_services.database.eda_db import EDADB
from ska_oso_slt_services.database.log_db import LogDB
from ska_oso_slt_services.infrastructure.mapping import (
    SLTImageRepository,
    SLTLogRepository,
    SLTRepository,
)
from ska_oso_slt_services.models.metadata import _set_new_metadata
from ska_oso_slt_services.models.slt import SLT

# from ska_oso_slt_services.models.slt_image import SLTImage
# from ska_oso_slt_services.models.slt_log import SLTLog
# from ska_oso_slt_services.rest import slt

LOGGER = logging.getLogger(__name__)

Response = Tuple[Union[dict, list], int]

T = TypeVar("T")

log_db = LogDB(LogDBConfig)
eda_db = EDADB(EDAConfig)
oda_db = ODAConfig()
oda = FlaskODA()

slt_repo = SLTRepository()
slt_log_repo = SLTLogRepository()
slt_image_repo = SLTImageRepository()

# ODA_BACKEND_TYPE = getenv("ODA_BACKEND_TYPE", "postgres")


def get_response(url):
    return requests.get(url).json()


def error_handler(api_fn: Callable[[str], Response]) -> Callable[[str], Response]:
    """
    A decorator function to catch general errors and wrap in the correct HTTP
    response

    :param api_fn: A function which accepts an entity identifier and returns
    an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError:

            return {
                "detail": (
                    "Not Found. The requested identifier"
                    f" {next(iter(kwargs.values()))} could not be found."
                ),
            }, HTTPStatus.NOT_FOUND
        except (ValueError, ValidationError) as e:
            LOGGER.exception(
                "ValueError occurred when adding entity, likely some semantic"
                " validation failed"
            )

            return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

        except Exception as e:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper


class SLTQueryParamsFactory(QueryParamsFactory):
    """
    Class for checking Query Parameters
    overrides QueryParamsFactory
    """

    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        """
        Returns QueryParams instance if validation successful
        param kwargs: Parameters Passed
        raises: ValueError for incorrect values
        """

        return SLTQueryParamsFactory.from_dict(kwargs=kwargs)


def get_qry_params(kwargs: dict) -> Union[QueryParams, Response]:
    """
    Convert the parameters from the request into QueryParams.

    Currently only a single instance of QueryParams is supported, so
    subsequent parameters will be ignored.

    :param kwargs: Dict with parameters from HTTP GET request
    :return: An instance of QueryParams
    :raises: TypeError if a supported QueryParams cannot be extracted
    """

    try:
        return QueryParamsFactory.from_dict(kwargs)
    except ValueError as err:
        return validation_response(
            "Not Supported",
            err.args[0],
            HTTPStatus.BAD_REQUEST,
        )


def slt_get_qry_params(kwargs: dict) -> Union[SLTQueryParamsFactory, Response]:
    """
    Convert the parameters from the request into SLTQueryParamsFactory.

    Currently only a single instance of SLTQueryParamsFactory is supported, so
    subsequent parameters will be ignored.

    :param kwargs: Dict with parameters from HTTP GET request
    :return: An instance of SLTQueryParamsFactory
    :raises: TypeError if a supported SLTQueryParamsFactory cannot be extracted
    """

    try:
        return SLTQueryParamsFactory.from_dict(kwargs)
    except ValueError as err:
        return validation_response(
            "Not Supported",
            err.args[0],
            HTTPStatus.BAD_REQUEST,
        )


@error_handler
def put_shift_data(shift_id: str, body: dict) -> Response:
    """
    Function that a PUT /slt request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """
    try:
        slt_comment_data = SLT(annotation=body["annotation"], comments=body["comments"])
        slt_comment_data = _set_new_metadata(slt_comment_data)

    except KeyError as e:
        return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

    insert_record = slt_repo.insert(record=slt_comment_data)
    slt_comment_data.id = insert_record["id"]

    print(slt_comment_data)

    return json.loads(slt_comment_data.model_dump_json()), HTTPStatus.OK


@error_handler
def get_shift_history_data_with_id(shift_id: str) -> Response:
    """
    Function that a GET /shift/history/<shift_id> request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """

    slt_records = slt_repo.get_records_by_id_or_by_slt_ref(record_id=shift_id)

    return slt_records, HTTPStatus.OK


@error_handler
def get_shift_history_data_with_date(
    start_time: datetime, end_time: datetime
) -> Response:
    """
    Function that a GET /shift/history/<shift_id> request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """

    slt_records = slt_repo.get_records_by_shift_time(
        start_time=start_time, end_time=end_time
    )

    return slt_records, HTTPStatus.OK


@error_handler
def get_eb_data_with_sbi_status(shift_id: str) -> Response:
    """
    Function that a GET /ebs request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
         or appropriate error Response
    """

    slt_log_records = slt_log_repo.get_records_by_id_or_by_slt_ref(slt_ref=shift_id)

    if slt_log_records:

        for entity in slt_log_records:

            sbi_id = entity["info"]["sbi_ref"]

            entity["info"]["sbi_status"] = get_response(
                url=f"{ODAConfig.DB_URL}{ODAConfig.STATUS_API}{sbi_id}?version=1"
            )["current_status"]

    else:

        raise KeyError("No EB found")

    # try:

    #     with oda.uow as uow:

    #         status = uow.sbis_status_history.get(
    #         entity_id=sbi_id, version=1, is_status_history=False)
    #         print(f"#################### {status}")

    # except Exception as e:
    #     return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

    return slt_log_records, HTTPStatus.OK


def error_response(
    err: Exception, http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
) -> Response:
    """
    Creates a general server error response from an exception

    :return: HTTP response server error
    """
    response_body = {
        "title": http_status.phrase,
        "detail": f"{repr(err)} with args {err.args}",
        "traceback": {
            "key": "Internal Server Error",
            "type": str(type(err)),
            "full_traceback": traceback.format_exc(),
        },
    }

    return response_body, http_status
