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
BASE_API_URL = f"/ska-oso-slt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"


class TestSLTAPI:
    """This class contains unit tests for the SBInstanceAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Insatnces.
    """

    @mock.patch("ska_oso_slt_services.rest.api.resources.put_shift_data")
    def test_put_shift_data(self, mock_slt, client):
        """Verifying that put_shift_data updates the shift comments correctly"""
        valid_put_shift_data_response = load_string_from_file(
            "files/testfile_sample_shift_data.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.id = ["3560"]

        shift_history_mock = mock.MagicMock()

        shift_history_mock.add.return_value = (
            SLT.model_validate_json(valid_put_shift_data_response)
        )
        uow_mock.shift_history = shift_history_mock
        uow_mock.commit.return_value = "200"
        mock_slt.uow.__enter__.return_value = uow_mock

        data = {"comments": "There was error in EB execution in the project", 
                "annotation": "There was error in EB execution in the project."}

        result = client.put(
            f"{BASE_API_URL}/shift/3560",
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_shift_data_response)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_shift(self, client):
        """Verifying that put_shift error if invalid data passed"""
        
        data = {"comment": "There was error in EB execution in the project", 
                "annotation": "There was error in EB execution in the project."}

        error = {
            "detail": "KeyError('comment') with args ('comment',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{BASE_API_URL}/shift/3560",
            json=data,
            headers={"accept": "application/json"},
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

