"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import logging
from http import HTTPStatus
from typing import Any, Dict, Tuple, Union

from ska_db_oda.domain.query import QueryParams, QueryParamsFactory

from ska_db_oda.rest.api.resources import (
    error_handler,
    validation_response,
)

LOGGER = logging.getLogger(__name__)


Response = Tuple[Union[dict, list], int]


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

        return QueryParamsFactory.from_dict(kwargs=kwargs)


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
        return SLTQueryParamsFactory.from_dict(kwargs)
    except ValueError as err:
        return validation_response(
            "Not Supported",
            err.args[0],
            HTTPStatus.BAD_REQUEST,
        )


@error_handler
def get_shift_history_data(shift_id: str) -> Response:
    """
    Function that a GET /shift/history/<shift_id> request is routed to.

    :param shift_id: Requested identifier from the path parameter
    :return: The Shift History Data with status wrapped in a Response, or appropriate error
     Response
    """
    with oda.uow as uow:
        sbd = uow.sbds.get(sbd_id)
        sbd_json = sbd.model_dump(mode="json")
        sbd_json["status"] = _get_sbd_status(
            uow=uow, sbd_id=sbd_id, version=sbd_json["metadata"]["version"]
        )["current_status"]
    return sbd_json, HTTPStatus.OK

