"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""
import requests
import logging
from datetime import datetime
from http import HTTPStatus
from typing import Tuple, Union

from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import error_handler, validation_response

LOGGER = logging.getLogger(__name__)


Response = Tuple[Union[dict, list], int]



BASE_URL = "http://172.20.10.2:5001/ska-db-oda/oda/api/v4/"


def get_response(url):
    response = requests.get(url)
    return response.json()


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
def get_eb_data_with_sbi_status(start_time: datetime, end_time: datetime) -> Response:
    """
    Function that a GET /eb/history/ request is routed to.

    :param start_time: Requested start time from the path parameter
    :param end_time: Requested end time from the path parameter
    :return: The Shift History Data with status wrapped in a Response,
             or appropriate error
     Response
    """
    response = get_response(
        url=f"{BASE_URL}/ebs?created_before={end_time}&created_after={start_time}"
    )
    # print("lllllllllllllllllllll",response[0]['sbi_ref'])
    if response:
        if isinstance(response, list):
            for res in response:
                status_response = get_response(
                    url=f"{BASE_URL}/status/sbis/{res[0]['sbi_ref']}?version=1"
                )
        else:
            status_response = get_response(
                url=f"{BASE_URL}/status/sbis/{response[0]['sbi_ref']}?version=1"
            )
    else:
        print("NO EB found")

    print("kkkkkkkkkkkkkkkkk", status_response)

    return response, HTTPStatus.OK


# response = get_response(url=f"{BASE_URL}/ebs?match_type=contains&entity_id=eb")
# print(response)
