# pylint: disable=line-too-long
import json
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

from tests.unit.ska_oso_slt_services.util import load_string_from_file

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-slt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-slt-services/slt/api/v{OSO_SERVICES_MAJOR_VERSION}"


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.insert")
@mock.patch(
    "ska_oso_slt_services.infrastructure.postgresql.Postgresql.get_records_by_id_or_by_slt_ref"  # pylint: disable=line-too-long
)
@mock.patch("ska_oso_slt_services.rest.api.resources.post_shift_data")
def test_post_shift_data(
    mock_postgresql_insert, mock_postgresql_get_records, mock_post_data, client
):

    valid_post_shift_data_response = load_string_from_file(
        "files/testfile_sample_post_shift_data.json"
    )

    mock_postgresql_insert.return_value = json.loads(valid_post_shift_data_response)

    mock_postgresql_get_records.return_value = json.loads(
        valid_post_shift_data_response
    )

    mock_post_data.return_value = json.loads(valid_post_shift_data_response)

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
        "created_by": "Chandler Bing",
        "created_on": "2024-07-22T13:19:03.666933Z",
        "id": "slt-mvp01-07222024-6897",
        "last_modified_by": "Ross Geller",
        "last_modified_on": "2024-07-22T13:19:03.666933Z",
        "shift_end": "2024-07-22T13:19:03.666847Z",
        "shift_start": "2024-07-22T13:19:03.666969Z",
    }

    result = client.post(
        f"{BASE_API_URL}/shift",
        json=data,
        headers={"accept": "application/json"},
    )

    assert (
        json.loads(result.text)["created_by"]
        == mock_post_data.return_value["created_by"]
    )
    assert result.status_code == HTTPStatus.OK


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.insert")
@mock.patch(
    "ska_oso_slt_services.infrastructure.postgresql.Postgresql.get_records_by_id_or_by_slt_ref"  # pylint: disable=line-too-long
)
@mock.patch("ska_oso_slt_services.rest.api.resources.post_shift_data")
def test_invalid_post_shift_data(
    mock_postgresql_insert, mock_postgresql_get_records, mock_post_data, client
):

    valid_post_shift_data_response = load_string_from_file(
        "files/testfile_sample_post_shift_data.json"
    )

    mock_postgresql_insert.return_value = json.loads(valid_post_shift_data_response)

    mock_postgresql_get_records.return_value = json.loads(
        valid_post_shift_data_response
    )

    mock_post_data.return_value = "KeyError('created_by') with args ('created_by',)"

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
        "created_y": "Chandler Bing",
        "created_on": "2024-07-22T13:19:03.666933Z",
        "id": "slt-mvp01-07222024-6897",
        "last_modified_by": "Ross Geller",
        "last_modified_on": "2024-07-22T13:19:03.666933Z",
        "shift_end": "2024-07-22T13:19:03.666847Z",
        "shift_start": "2024-07-22T13:19:03.666969Z",
    }

    result = client.post(
        f"{BASE_API_URL}/shift",
        json=data,
        headers={"accept": "application/json"},
    )

    assert json.loads(result.text)["detail"] == mock_post_data.return_value
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.update")
@mock.patch(
    "ska_oso_slt_services.infrastructure.postgresql.Postgresql.get_records_by_id_or_by_slt_ref"  # pylint: disable=line-too-long
)
@mock.patch("ska_oso_slt_services.rest.api.resources.put_shift_data")
def test_put_shift_data(mock_postgresql_update, mock_postgresql_get_records, mock_put_data, client):

    valid_put_shift_data_response = load_string_from_file(
        "files/testfile_sample_put_shift_data.json"
    )

    mock_postgresql_update.return_value = None

    mock_postgresql_get_records.return_value = json.loads(valid_put_shift_data_response)

    # import pdb; pdb.set_trace()

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
    }

    result = client.put(
        f"{BASE_API_URL}/shift/slt-mvp01-07222024-6897",
        json=data,
        headers={"accept": "application/json"},
    )

    print(f"@@@@@@@@@@ {result.text}")
    print(f"########## {mock_postgresql_get_records.return_value}")

    assert result.text == mock_postgresql_get_records.return_value

    assert result.status_code == HTTPStatus.OK


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.update")
@mock.patch("ska_oso_slt_services.rest.api.resources.put_shift_data")
def test_invalid_put_shift_data(mock_postgresql_update, mock_put_data, client):

    valid_put_shift_data_response = load_string_from_file(
        "files/testfile_sample_put_shift_data.json"
    )

    mock_postgresql_update.return_value = json.loads(valid_put_shift_data_response)

    mock_put_data.return_value = json.loads(valid_put_shift_data_response)

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
    }

    result = client.put(
        f"{BASE_API_URL}/shif/slt-mvp01-07222024-6897",
        json=data,
        headers={"accept": "application/json"},
    )

    assert result.status_code == HTTPStatus.NOT_FOUND


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.update")
@mock.patch("ska_oso_slt_services.rest.api.resources.get_shift_history_data_with_date")
def test_invalid_get_shift_data(mock_postgresql_update, mock_get_data, client):

    valid_put_shift_data_response = load_string_from_file(
        "files/testfile_sample_put_shift_data.json"
    )

    mock_postgresql_update.return_value = json.loads(valid_put_shift_data_response)

    mock_get_data.return_value = json.loads(valid_put_shift_data_response)

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
    }

    result = client.put(
        f"{BASE_API_URL}/shift/history?entity_id",
        json=data,
        headers={"accept": "application/json"},
    )

    assert result.status_code == HTTPStatus.NOT_FOUND


@mock.patch("ska_oso_slt_services.rest.api.resources.get_eb_data_with_sbi_status")
def test_invalid_get_eb_data(mock_eb_data, client):

    mock_eb_data.return_value = "Missing query parameter 'created_after'"

    result = client.get(
        f"{BASE_API_URL}/shift_log?shift_id=1234",
        json="data",
        headers={"accept": "application/json"},
    )

    json.loads(result.text)["detail"] == mock_eb_data.return_value

    assert result.status_code == HTTPStatus.BAD_REQUEST


# @mock.patch("ska_oso_slt_services.rest.api.resources.get_eb_data_with_sbi_status")
# def test_get_eb_data(mock_eb_data, client):

#     valid_get_shift_data_response = load_string_from_file(
#             "files/testfile_sample_shift_log_data.json"
#         )

#     valid_get_ebs_data_response = load_string_from_file(
#             "files/testfile_sample_multiple_ebs_with_status.json"
#         )

#     uow_mock = mock.MagicMock()
#     mock_eb_data.uow.__enter__.return_value = uow_mock

#     start_time = "created_after=2024-07-12T15%3A43%3A53.971548%2B00%3A00&"
#     end_time = "created_before=2024-07-24T15%3A43%3A53.971548%2B00%3A00"

#     result = client.get(
#         f"{BASE_API_URL}/shift_log?{start_time}{end_time}",
#         headers={"accept": "application/json"},
#     )

#     print(f"!!!!!!!!!!!! {result.text}")

#     assert result.status_code == HTTPStatus.OK
