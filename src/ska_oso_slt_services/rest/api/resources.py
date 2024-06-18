"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""


def get_slts() -> dict:
    """This function takes query parameters and SLT data source objects
      to generate a response containing matching SLT data.

    :param query_params (QueryParams): The query parameters.
    :param tm_data_sources (list): A list of SLT data source objects.

    :returns dict: A dictionary with SLT data satisfying the query.
    """
    return {"test": "test"}
