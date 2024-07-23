"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-exception-caught
import json
import logging
import traceback
from datetime import datetime, timezone
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, TypeVar, Union

import requests
from pydantic import ValidationError
from ska_db_oda.domain.query import QueryParams
from ska_db_oda.rest.api.resources import get_qry_params
from ska_db_oda.unit_of_work.postgresunitofwork import PostgresUnitOfWork

from ska_oso_slt_services.database.config import EDAConfig, LogDBConfig, ODAConfig
from ska_oso_slt_services.database.eda_db import EDADB
from ska_oso_slt_services.database.log_db import LogDB
from ska_oso_slt_services.infrastructure.mapping import (
    SLTImageRepository,
    SLTLogRepository,
    SLTRepository,
)
from ska_oso_slt_services.infrastructure.postgresql import conn_pool
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

uow = PostgresUnitOfWork(conn_pool)

slt_repo = SLTRepository()
slt_log_repo = SLTLogRepository()
slt_image_repo = SLTImageRepository()


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
        except KeyError as err:

            return {"detail": str(err.args[0])}, HTTPStatus.NOT_FOUND

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


@error_handler
def post_shift_data(body: dict) -> Response:
    """
    Function that a POST /shift/{shift_id} request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """
    try:

        slt_entity = SLT(
            annotation=body["annotation"],
            comments=body["comments"],
            metadata={
                "created_by": body["created_by"],
                "last_modified_by": body["last_modified_by"],
            },
        )

    except KeyError as err:

        return error_response(err, HTTPStatus.UNPROCESSABLE_ENTITY)

    slt_entity_id = slt_repo.insert(slt_entity=slt_entity)
    persisted_entity = slt_repo.get_records_by_id_or_by_slt_ref(
        record_id=slt_entity_id["id"]
    )

    return persisted_entity, HTTPStatus.OK


@error_handler
def put_shift_data(shift_id: str, body: dict) -> Response:
    """
    Function that a PUT /shift/{shift_id} request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """
    try:

        slt_entity = slt_repo.get_records_by_id_or_by_slt_ref(record_id=shift_id)

        if not slt_entity:
            raise KeyError(
                f"Not found. The requested Shift Id {shift_id} could not be found."
            )

        else:

            comments = f"{body['comments']}, {slt_entity[0]['comments']}"
            annotation = f"{body['annotation']}, {slt_entity[0]['annotation']}"

            slt_entity = SLT(
                id=slt_entity[0]["id"],
                shift_start=slt_entity[0]["shift_start"].astimezone(tz=timezone.utc),
                annotation=annotation,
                comments=comments,
                metadata={
                    "created_by": slt_entity[0]["created_by"],
                    "created_on": slt_entity[0]["created_on"].astimezone(
                        tz=timezone.utc
                    ),
                    "last_modified_by": slt_entity[0]["last_modified_by"],
                },
            )

    except KeyError as err:

        raise KeyError(err)  # pylint: disable=raise-missing-from
    
    import pdb; set_trace()

    slt_entity = json.loads(slt_entity.model_dump_json())
    slt_entity_without_id = {**slt_entity}
    slt_entity_without_id.pop("id")

    slt_repo.update(slt_entity=slt_entity_without_id, slt_entity_id=shift_id)
    persisted_entity = slt_repo.get_records_by_id_or_by_slt_ref(record_id=shift_id)

    return persisted_entity, HTTPStatus.OK


# @error_handler
# def get_shift_history_data_with_id(shift_id: str) -> Response:
#     """
#     Function that a GET /shift/history/<shift_id> request is routed to.

#     :param shift_id: Requested identifier from the path parameter
#     :return: The Shift History Data with status wrapped in a Response,
#              or appropriate error
#      Response
#     """

#     slt_records = slt_repo.get_records_by_id_or_by_slt_ref(record_id=shift_id)

#     return slt_records, HTTPStatus.OK


@error_handler
def get_shift_history_data_with_date(
    shift_start_time: datetime, shift_end_time: datetime, shift_id: str = None
) -> Response:
    """
    Function that a GET /shift/history request is routed to.

    :param shift_start_time: Start time of the shift Required
    :param shift_end_time: End time of the shift
    :param shift_id: Unique Shift Id
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """

    if shift_id:

        slt_records = slt_repo.get_records_by_id_or_by_slt_ref(record_id=shift_id)

    else:

        slt_records = slt_repo.get_records_by_shift_time(
            start_time=shift_start_time, end_time=shift_end_time
        )

    return slt_records, HTTPStatus.OK


@error_handler
def get_eb_data_with_sbi_status(**kwargs) -> Response:
    """
    Function that a GET /shift_log request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
         or appropriate error Response
    """

    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with uow:

        ebs = uow.ebs.query(maybe_qry_params)

        info = {}

        for eb in ebs:

            info_single_record = eb.model_dump(mode="json")
            sbi_current_status = uow.sbis_status_history.get(
                entity_id=eb.sbi_ref
            ).model_dump(mode="json")["current_status"]
            info_single_record["sbi_status"], info_single_record["source"] = (
                sbi_current_status,
                "ODA",
            )
            info_single_record["request_responses"][:] = [
                record
                for record in info_single_record["request_responses"]
                if record.get("status")
                in (
                    "observed",
                    "failed",
                )
            ]
            info[eb.eb_id] = info_single_record
    return info, HTTPStatus.OK


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



@error_handler
def get_eb_sbi_status(**kwargs) -> Response:
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with uow:
        ebs = uow.ebs.query(maybe_qry_params)

        info = {}
        for eb in ebs:
            info_single_record = eb.model_dump(mode="json")
            sbi_current_status = uow.sbis_status_history.get(entity_id=eb.sbi_ref).model_dump(mode="json")["current_status"]
            info_single_record["sbi_status"] = sbi_current_status
            info_single_record["source"] = "ODA"
            info_single_record["request_responses"][:] = [record for record in info_single_record["request_responses"] if record.get('status') in ('observed', 'failed',)]
            info[eb.eb_id] = info_single_record
    return info, HTTPStatus.OK

