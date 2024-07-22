import json
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

from ska_oso_slt_services.models.slt import SLT
from tests.unit.ska_oso_slt_services.util import (
    assert_json_is_equal,
    load_string_from_file,
)

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-slt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-slt-services/slt/api/v{OSO_SERVICES_MAJOR_VERSION}"


class TestSLTAPI:
    """This class contains unit tests for the SLT API resource,
    which is responsible for handling requests related to
    Shift Log Tool.
    """

    @mock.patch("ska_oso_slt_services.rest.api.resources.post_shift_data")
    def test_post_shift_data(self, mock_slt, client):
        """Verifying that post_shift_data updates the shift comments correctly"""
        valid_post_shift_data_response = load_string_from_file(
            "files/testfile_sample_post_shift_data.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.id = ["slt-mvp01-07222024-6897"]

        shift_history_mock = mock.MagicMock()

        shift_history_mock.add.return_value = SLT.model_validate_json(
            valid_post_shift_data_response
        )
        uow_mock.shift_history = shift_history_mock
        uow_mock.commit.return_value = "200"
        mock_slt.uow.__enter__.return_value = uow_mock

        data = {
                "annotation": "There was error in EB execution in the project.",
                "comments": "There was error in EB execution in the project",
                "created_by": "Chandler Bing",
                "created_on": "2024-07-22T13:19:03.666933Z",
                "id": "slt-mvp01-07222024-6897",
                "last_modified_by": "Ross Geller",
                "last_modified_on": "2024-07-22T13:19:03.666933Z",
                "shift_end": "2024-07-22T13:19:03.666847Z",
                "shift_start": "2024-07-22T13:19:03.666969Z"
            }

        result = client.post(
            f"{BASE_API_URL}/shift",
            json=data,
            headers={"accept": "application/json"},
        )

        result_data = json.loads(result.text)[0]
        valid_data = json.loads(valid_post_shift_data_response)

        print(f"!!!!!!!!!!!!!!! {result_data['id']} {valid_data['id']}")

        assert result_data['id'] == valid_data['id']

        # assert_json_is_equal(json.dumps(json.loads(result.text)[0]), valid_post_shift_data_response)
        assert result.status_code == HTTPStatus.OK


    # @mock.patch("ska_oso_slt_services.rest.api.resources.put_shift_data")
    # def test_put_shift_data(self, mock_slt, client):
    #     """Verifying that put_shift_data updates the shift comments correctly"""
    #     valid_put_shift_data_response = load_string_from_file(
    #         "files/testfile_sample_shift_data.json"
    #     )

    #     uow_mock = mock.MagicMock()
    #     uow_mock.id = ["slt-mvp01-07222024-000"]

    #     shift_history_mock = mock.MagicMock()

    #     shift_history_mock.add.return_value = SLT.model_validate_json(
    #         valid_put_shift_data_response
    #     )
    #     uow_mock.shift_history = shift_history_mock
    #     uow_mock.commit.return_value = "200"
    #     mock_slt.uow.__enter__.return_value = uow_mock

    #     data = {
    #         "comments": "There was error in EB execution in the project",
    #         "annotation": "There was error in EB execution in the project.",
    #     }

    #     result = client.put(
    #         f"{BASE_API_URL}/shift/slt-mvp01-07222024-000",
    #         json=data,
    #         headers={"accept": "application/json"},
    #     )

    #     print(f"@@@@@@@@@@@@@ {result.text[0]}")
    #     assert_json_is_equal(result.text[0], valid_put_shift_data_response)
    #     assert result.status_code == HTTPStatus.OK

    # @mock.patch("ska_oso_slt_services.rest.api.resources.get_shift_history_data_with_date")
    # def test_get_shift_data(self, mock_slt, client):
    #     """Verifying that get_shift_data updates the shift comments correctly"""
    #     valid_get_shift_data_response = load_string_from_file(
    #         "files/testfile_sample_shift_data.json"
    #     )

    #     uow_mock = mock.MagicMock()
    #     uow_mock.id = ["slt-mvp01-07222024-947"]

    #     shift_history_mock = mock.MagicMock()

    #     shift_history_mock.add.return_value = SLT.model_validate_json(
    #         valid_get_shift_data_response
    #     )
    #     uow_mock.shift_history = shift_history_mock
    #     uow_mock.commit.return_value = "200"
    #     mock_slt.uow.__enter__.return_value = uow_mock

    #     data = {
    #         "comments": "There was error in EB execution in the project",
    #         "annotation": "There was error in EB execution in the project.",
    #     }

    #     result = client.put(
    #         f"{BASE_API_URL}/shift/slt-mvp01-07222024-947",
    #         json=data,
    #         headers={"accept": "application/json"},
    #     )

    #     print(f"@@@@@@@@@@@@@ {result.text[0]}")
    #     assert_json_is_equal(result.text[0], valid_get_shift_data_response)
    #     assert result.status_code == HTTPStatus.OK


    def test_invalid_put_shift(self, client):
        """Verifying that put_shift error if invalid data passed"""

        data = {
            "comment": "There was error in EB execution in the project",
            "annotation": "There was error in EB execution in the project.",
        }

        error = {
                "detail": "'Not found. The requested Shift Id 3560 could not be found.'"
                }

        result = client.put(
            f"{BASE_API_URL}/shift/3560",
            json=data,
            headers={"accept": "application/json"},
        )
        
        assert_json_is_equal(result.text, json.dumps(error))
        assert result.status_code == HTTPStatus.NOT_FOUND
