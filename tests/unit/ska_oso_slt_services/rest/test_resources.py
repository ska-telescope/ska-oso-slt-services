# pylint: disable=line-too-long
from datetime import datetime, timezone
import json
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

from ska_oso_pdm import OSOExecutionBlock

from tests.unit.ska_oso_slt_services.util import assert_json_is_equal, load_string_from_file

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-slt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-slt-services/slt/api/v{OSO_SERVICES_MAJOR_VERSION}"


@mock.patch("ska_oso_slt_services.infrastructure.postgresql.create_connection_pool")
@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.insert")
@mock.patch(
    "ska_oso_slt_services.infrastructure.postgresql.Postgresql.get_records_by_id_or_by_slt_ref"  # pylint: disable=line-too-long
)
@mock.patch("ska_oso_slt_services.rest.api.resources.post_shift_data")
def test_post_shift_data(
    mock_conn_pool, mock_postgresql_insert, mock_postgresql_get_records, mock_post_data, client
):

    valid_post_shift_data_response = load_string_from_file(
        "files/testfile_sample_post_shift_data.json"
    )

    mock_postgresql_insert.return_value = json.loads(valid_post_shift_data_response)

    mock_postgresql_get_records.return_value = json.loads(
        valid_post_shift_data_response
    )

    mock_conn_pool.return_value = None

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

    assert json.loads(result.text)['created_by'] == mock_postgresql_get_records.return_value['created_by']
    assert result.status_code == HTTPStatus.OK

@mock.patch("ska_oso_slt_services.infrastructure.postgresql.create_connection_pool")
@mock.patch("ska_oso_slt_services.infrastructure.postgresql.Postgresql.update")
@mock.patch(
    "ska_oso_slt_services.infrastructure.postgresql.Postgresql.get_records_by_id_or_by_slt_ref"  # pylint: disable=line-too-long
)
@mock.patch("ska_oso_slt_services.rest.api.resources.post_shift_data")
def test_put_shift_data(
    mock_conn_pool, mock_postgresql_insert, mock_postgresql_get_records, mock_post_data, client
):

    valid_post_shift_data_response = load_string_from_file(
        "files/testfile_sample_put_shift_data.json"
    )

    mock_postgresql_insert.return_value = [{

            "annotation":"There was error in EB execution in the project., There was error in EB execution in the project.",
            "comments":"There was error in EB execution in the project, There was error in EB execution in the project",
            "created_by":"Chandler Bing",
            "created_on": datetime.now(),
            "id":"slt-mvp01-07222024-6897", 
            "last_modified_by":"Ross Geller",
            "last_modified_on": datetime.now(),
            "shift_end": datetime.now(),
            "shift_start": datetime.now()
        }]

    mock_postgresql_get_records.return_value = [{

            "annotation":"There was error in EB execution in the project., There was error in EB execution in the project.",
            "comments":"There was error in EB execution in the project, There was error in EB execution in the project",
            "created_by":"Chandler Bing",
            "created_on": datetime.now(),
            "id":"slt-mvp01-07222024-6897", 
            "last_modified_by":"Ross Geller",
            "last_modified_on": datetime.now(),
            "shift_end": datetime.now(),
            "shift_start": datetime.now()
        }]
    

    mock_conn_pool.return_value = None

    data = {
        "annotation": "There was error in EB execution in the project.",
        "comments": "There was error in EB execution in the project",
        "created_by": "Chandler Bing",
        "created_on": datetime.now(),
        "id": "slt-mvp01-07222024-6897",
        "last_modified_by": "Ross Geller",
        "last_modified_on": datetime.now(),
        "shift_end": datetime.now(),
        "shift_start": datetime.now()
    }

    result = client.put(
        f"{BASE_API_URL}/shift/slt-mvp01-07222024-6897",
        json=data,
        headers={"accept": "application/json"},
    )

    exclude_paths = [
            "root['last_modified_on']",
            "root['shift_end']",
            "root['shift_start']",
            "root['created_on']",
        ]

    # print(f"@@@@@@@@@@@@@@@@ { json.loads(result.text)[0]}")
    # print(f"!!!!!!!!!!!!!!!!!!!!!!! { mock_postgresql_get_records.return_value[0]}")


    # assert_json_is_equal(json.loads(result.text)[0], mock_postgresql_get_records.return_value[0], exclude_paths)
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
def test_get_shift_data(mock_postgresql_update, mock_get_data, client):

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



@mock.patch("ska_oso_slt_services.infrastructure.postgresql.create_connection_pool")
@mock.patch("ska_db_oda.infrastructure.postgres.repository.PostgresBridge.query")
@mock.patch("ska_db_oda.unit_of_work.postgresunitofwork.PostgresUnitOfWork")
@mock.patch("ska_oso_slt_services.rest.api.resources.get_eb_data_with_sbi_status")
def test_get_eb_data(mock_conn_pool, mock_postgresql_query, mock_postgresql_uow, mock_eb_data, client):

    mock_conn_pool.return_value = None

    valid_eb_data = load_string_from_file(
        "files/testfile_sample_eb.json"
    )

    execution_block = [OSOExecutionBlock(**x) for x in json.loads(valid_eb_data)]

    print(execution_block)

    # uow_mock = mock.MagicMock()
    # uow_mock.ebs.query.return_value = execution_block
    
    ebs_mock = mock.MagicMock()
    ebs_mock.query.return_value = execution_block
    uow_mock = mock.MagicMock()
    uow_mock.ebs = ebs_mock

    mock_postgresql_uow.__enter__.return_value = uow_mock

    

    # mock_postgresql_query.return_value = [{
    #   "eb_id": "eb-mvp01-20240426-8481",
    #   "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
    #   "metadata": {
    #     "created_by": "DefaultUser",
    #     "created_on": "2024-07-01T10:00:49.094768Z",
    #     "last_modified_by": "DefaultUser",
    #     "last_modified_on": "2024-07-01T10:00:49.094768Z",
    #     "version": 1
    #   },
    #   "request_responses": [
    #     {
    #       "request": "ska_oso_scripting.functions.devicecontrol.release_all_resources",
    #       "request_args": {
    #         "kwargs": {
    #           "subarray_id": "1"
    #         }
    #       },
    #       "request_sent_at": "2022-09-23T15:43:53.971548Z",
    #       "response": {
    #         "result": "this is a result"
    #       },
    #       "response_received_at": "2022-09-23T15:43:53.971548Z",
    #       "status": "OK"
    #     },
    #     {
    #       "error": {
    #         "detail": "this is an error"
    #       },
    #       "request": "ska_oso_scripting.functions.devicecontrol.scan",
    #       "request_sent_at": "2022-09-23T15:43:53.971548Z",
    #       "status": "ERROR"
    #     }
    #   ],
    #   "sbd_ref": "sbd-mvp01-20220923-00001",
    #   "sbd_version": 1,
    #   "sbi_ref": "sbi-mvp01-20220923-00001",
    #   "status": "fully_observed",
    #   "telescope": "ska_mid"
    # }]
    # # mock_postgresql_uow.uow.__enter__.return_value = json.loads(valid_post_shift_data_response)
    # mock_eb_data.return_value = [{
    #   "eb_id": "eb-mvp01-20240426-8481",
    #   "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
    #   "metadata": {
    #     "created_by": "DefaultUser",
    #     "created_on": "2024-07-01T10:00:49.094768Z",
    #     "last_modified_by": "DefaultUser",
    #     "last_modified_on": "2024-07-01T10:00:49.094768Z",
    #     "version": 1
    #   },
    #   "request_responses": [
    #     {
    #       "request": "ska_oso_scripting.functions.devicecontrol.release_all_resources",
    #       "request_args": {
    #         "kwargs": {
    #           "subarray_id": "1"
    #         }
    #       },
    #       "request_sent_at": "2022-09-23T15:43:53.971548Z",
    #       "response": {
    #         "result": "this is a result"
    #       },
    #       "response_received_at": "2022-09-23T15:43:53.971548Z",
    #       "status": "OK"
    #     },
    #     {
    #       "error": {
    #         "detail": "this is an error"
    #       },
    #       "request": "ska_oso_scripting.functions.devicecontrol.scan",
    #       "request_sent_at": "2022-09-23T15:43:53.971548Z",
    #       "status": "ERROR"
    #     }
    #   ],
    #   "sbd_ref": "sbd-mvp01-20220923-00001",
    #   "sbd_version": 1,
    #   "sbi_ref": "sbi-mvp01-20220923-00001",
    #   "status": "fully_observed",
    #   "telescope": "ska_mid"
    # }]

    start_time = f"created_after={datetime.now()}&"
    end_time = f"created_before={datetime.now()}"

    result = client.get(
        f"{BASE_API_URL}/shift_log?{start_time}{end_time}",
        headers={"accept": "application/json"},
    )

    print(f"!!!!!!!!!!!!!!! {result.text}")
    # print(f"@@@@@@@@@@@@@@@@ {mock_postgresql_query.return_value}")

    assert result.status_code == HTTPStatus.O
