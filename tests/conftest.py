# """
# pytest fixtures to be used by unit tests
# """

# import datetime
# from unittest.mock import patch

# import pytest

# from ska_oso_slt_services.models.shiftmodels import Shift, ShiftLogs
# from ska_oso_slt_services.rest import get_openapi_spec, init_app


# @pytest.fixture(scope="module")
# def spec():
#     """
#     Module scoped fixture so $refs are only resolved once
#     """
#     return get_openapi_spec()


# @pytest.fixture()
# def test_app(spec):  # pylint: disable=redefined-outer-name
#     """
#     Fixture to configure a test app instance
#     """
#     app = init_app(spec)
#     app.config.update({
#         "TESTING": True,
#     })
#     yield app


# @pytest.fixture()
# def client(test_app):  # pylint: disable=redefined-outer-name
#     """
#     Create a test client from the app instance, without running a live server
#     """
#     return test_app.test_client()


# @pytest.fixture()
# def valid_shift_data():
#     """Valid Create Shift Request Fixture"""
#     return {
#         "shift_operator": {"name": "John Doe"},
#         "annotations": "Routine maintenance shift.",
#         "comments": "All systems operational.",
#     }


# @pytest.fixture()
# def invalid_shift_data():
#     """Invalid Create Shift Request Fixture"""
#     return {
#         "ann1otations": "Routine maintenance shift.",
#         "c1omments": "At shift start All systems operational.",
#         "sh1ift_operator": {"name": "John Doe"},
#     }


# @pytest.fixture
# def invalid_create_shift_response():
#     """Invalid Create Shift Response Fixture"""
#     return {
#         "errors": [
#             {
#                 "input": "Routine maintenance shift.",
#                 "loc": ["ann1otations"],
#                 "msg": "Extra inputs are not permitted",
#                 "type": "extra_forbidden",
#                 "url": "https://errors.pydantic.dev/2.8/v/extra_forbidden",
#             },
#             {
#                 "input": "At shift start All systems operational.",
#                 "loc": ["c1omments"],
#                 "msg": "Extra inputs are not permitted",
#                 "type": "extra_forbidden",
#                 "url": "https://errors.pydantic.dev/2.8/v/extra_forbidden",
#             },
#             {
#                 "input": {"name": "John Doe"},
#                 "loc": ["sh1ift_operator"],
#                 "msg": "Extra inputs are not permitted",
#                 "type": "extra_forbidden",
#                 "url": "https://errors.pydantic.dev/2.8/v/extra_forbidden",
#             },
#         ]
#     }


# @pytest.fixture()
# def valid_update_shift_data():
#     """Valid Update Shift Request Fixture"""
#     return {
#         "annotations": "Updated maintenance shift.",
#         "comments": "All systems operational.",
#         "media": [
#             {"type": "image", "path": "/path/to/image1.png"},
#             {"type": "image", "path": "/path/to/image2.png"},
#         ],
#     }


# @pytest.fixture()
# def shift_logs_data():
#     """Shift Logs Fixture"""
#     return {
#         "info": {
#             "eb_id": "eb-t0001-20240801-00004",
#             "sbd_ref": "sbd-t0001-20240801-00002",
#             "sbi_ref": "sbi-t0001-20240801-00003",
#             "metadata": {
#                 "version": 1,
#                 "created_by": "DefaultUser",
#                 "created_on": "2024-08-01T17:24:38.004027Z",
#                 "last_modified_by": "DefaultUser",
#                 "last_modified_on": "2024-08-01T17:24:38.004027Z",
#             },
#             "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
#             "telescope": "ska_mid",
#             "sbi_status": "observed",
#             "sbd_version": 1,
#             "request_responses": [],
#         },
#         "log_time": "2024-08-02T17:13:41.388305",
#         "source": "ODA",
#     }


# @pytest.fixture()
# def shift_data_with_logs(shift_logs_data):  # pylint: disable=redefined-outer-name
#     """Shift Fixture with logs"""
#     return Shift(
#         sid=1,
#         shift_operator={"name": "John Doe"},
#         annotations="Routine maintenance shift.",
#         comments="All systems operational.",
#         shift_logs=[ShiftLogs(**shift_logs_data)],
#         shift_start=datetime.datetime.utcnow(),
#     )


# @pytest.fixture()
# def updated_shift_data_with_logs(
#     shift_logs_data,
# ):  # pylint: disable=redefined-outer-name
#     """Updated Shift Fixture with logs"""
#     updated_shift_logs = shift_logs_data.copy()
#     updated_shift_logs["info"]["sbi_status"] = "updated"
#     return Shift(
#         sid=1,
#         shift_operator={"name": "John Doe"},
#         annotations="Routine maintenance shift.",
#         comments="All systems operational.",
#         shift_logs=[ShiftLogs(**updated_shift_logs)],
#     )


# @pytest.fixture(autouse=True)
# def mock_db():
#     """Mock postgres db for unit tests"""
#     with patch(
#         "ska_oso_slt_services.data_access.postgres_data_acess.PostgresDataAccess"
#     ) as mock_data_access:
#         with patch(
#             "ska_oso_slt_services.data_access.postgres_data_acess.PostgresConnection"
#         ) as mock_connection:
#             with patch(
#                 "ska_oso_slt_services.data_access.postgres_data_acess."
#                 "PostgresConnection.get_connection"
#             ) as mock_add_conn:
#                 yield mock_data_access, mock_connection, mock_add_conn
