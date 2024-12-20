from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from ska_oso_slt_services import create_app  # Import your create_app function
from ska_oso_slt_services.app import API_PREFIX
from ska_oso_slt_services.common.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.common.date_utils import get_datetime_for_timezone
from ska_oso_slt_services.domain.shift_models import Shift

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


def test_create_shift(updated_shift_data):
    # Create a mock for the shift model
    mock_shift = MagicMock()
    mock_shift.shift_operator = updated_shift_data["shift_operator"]
    mock_shift.created_by = updated_shift_data["metadata"]["created_by"]
    mock_shift.created_on = updated_shift_data["metadata"]["created_on"]
    mock_shift.last_modified_by = updated_shift_data["metadata"]["last_modified_by"]
    mock_shift.last_modified_on = updated_shift_data["metadata"]["last_modified_on"]

    # Create a mock for the database session
    mock_db_session = MagicMock()

    # Set up the mock to return the existing shift when queried
    mock_db_session.get.return_value = {"max": 1}

    # Patch both database access and Shift model creation
    with (
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.insert"
        ) as mock_insert,
        patch(
            "ska_oso_slt_services.repository.postgres_shift_repository"
            ".skuid.fetch_skuid",
            return_value="sl-t0001-20241204-00004",
        ),
        patch(
            "ska_oso_slt_services.services.shift_service.Shift", return_value=mock_shift
        ),
    ):
        with patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get_one",
            return_value={"max": 5},
        ):

            # Send a POST request to the endpoint
            response = client.post(
                f"{API_PREFIX}/shifts/create", json=updated_shift_data
            )
    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert created_shift[0]["shift_operator"] == updated_shift_data["shift_operator"], (
        f"Expected shift_operator to be '{updated_shift_data['shift_operator']}',"
        "but got"
        f" '{created_shift[0]['shift_operator']}'"
    )

    # Verify metadata
    assert "metadata" in created_shift[0], "Metadata is missing in the response"
    metadata = created_shift[0]["metadata"]
    assert metadata["created_by"] == updated_shift_data["metadata"]["created_by"], (
        f"Expected created_by to be '{updated_shift_data['metadata']['created_by']}',"
        "but got"
        f" '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"]
        == updated_shift_data["metadata"]["last_modified_by"]
    ), (
        "Expected last_modified_by to be"
        f" '{updated_shift_data['metadata']['last_modified_by']}', but got"
        f" '{metadata['last_modified_by']}'"
    )

    mock_insert.assert_called_once()


def test_update_shift(existing_shift_data, updated_shift_data):

    # Expected shift data after the update
    expected_updated_shift = {**existing_shift_data, **updated_shift_data}

    # Patch ShiftService.update_shift directly to return the expected updated shift
    with patch(
        "ska_oso_slt_services.services.shift_service.ShiftService.update_shift",
        return_value=[expected_updated_shift],  # Return as a list for consistency
    ):
        # Send PUT request
        response = client.put(
            f"{API_PREFIX}/shifts/update/{existing_shift_data['shift_id']}",
            json=updated_shift_data,
        )

    # Assert the response status code is OK
    assert (
        response.status_code == HTTPStatus.OK
    ), f"Unexpected status code: {response.status_code}"

    # Extract and assert the updated response content
    updated_shift_response = response.json()

    # Check if the response is a tuple with a list and status code
    if (
        isinstance(updated_shift_response, list)
        and len(updated_shift_response) == 2
        and isinstance(updated_shift_response[1], int)
    ):
        updated_shift_response = updated_shift_response[
            0
        ]  # Extract the actual data from the tuple

    # Check if the data is wrapped in another list
    if isinstance(updated_shift_response, list):
        updated_shift_response = updated_shift_response[0]

    assert updated_shift_response["shift_id"] == existing_shift_data["shift_id"]
    assert (
        updated_shift_response["shift_operator"] == updated_shift_data["shift_operator"]
    )
    assert updated_shift_response["annotations"] == updated_shift_data["annotations"]
    assert updated_shift_response["comments"] == updated_shift_data["comments"]


def test_update_shift_after_end():
    existing_shift = MagicMock()
    existing_shift.shift_id = "test-id-1"
    existing_shift.shift_start = get_datetime_for_timezone("UTC")
    existing_shift.shift_end = get_datetime_for_timezone("UTC")  # Shift has ended
    existing_shift.shift_operator = "test-operator"
    existing_shift.shift_logs = {
        "logs": [
            {
                "info": {},
                "source": "test",
                "log_time": get_datetime_for_timezone("UTC"),
            }
        ]
    }
    existing_shift.media = []
    existing_shift.annotations = "existing-annotation"
    existing_shift.comments = "existing-comment"
    existing_shift.created_by = "test-user"
    existing_shift.created_on = get_datetime_for_timezone("UTC")
    existing_shift.last_modified_by = "test-user"
    existing_shift.last_modified_on = get_datetime_for_timezone("UTC")

    with patch(
        "ska_oso_slt_services.services.shift_service.ShiftService.get_shift",
        return_value=existing_shift,
    ):
        invalid_update_data = {
            "shift_id": "test-id-1",
            "shift_start": "2024-09-14T16:49:54.889Z",
            "shift_operator": "new-operator",
            "annotations": "updated-annotation",
        }

        with pytest.raises(ShiftEndedException):
            client.put(
                f"{API_PREFIX}/shifts/update/test-id-1",
                json=invalid_update_data,
            )

        valid_update_data = {
            "shift_id": "test-id-1",
            "annotations": "updated-annotation",
            "shift_start": "2024-09-14T16:49:54.889Z",
        }

        with patch(
            "ska_oso_slt_services." "services.shift_service.ShiftService.update_shift",
            return_value={**existing_shift.__dict__, **valid_update_data},
        ):
            response = client.put(
                f"{API_PREFIX}/shifts/update/test-id-1",
                json=valid_update_data,
            )

        assert (
            response.status_code == 200
        ), "Expected status code 200 for valid update with annotations only"
        updated_shift = response.json()
        assert updated_shift[0]["annotations"] == valid_update_data["annotations"], (
            f"Expected annotations to be '{valid_update_data['annotations']}',"
            f" but got '{updated_shift[0]['annotations']}'"
        )


@patch(
    "ska_oso_slt_services.services.shift_service.ShiftService.get_shift_logs_comments"
)
def test_get_shift_log_comments(mock_get_shift_comments, shift_log_comment_data):
    # Prepare test data

    mock_get_shift_comments.return_value = shift_log_comment_data

    # Send a POST request to create a comment
    response = client.get(
        f"{API_PREFIX}/shift_log_comments?shift_id=test-shift-id&eb_id=string"
    )

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


def test_update_shift_log_comment(shift_initial_comment_data):
    # Existing comment data with initial metadata
    current_time = get_datetime_for_timezone("UTC")

    # Updated comment data
    updated_comment_data = {
        "log_comment": "This is the updated comment",
        "operator_name": "updated_operator",
        "metadata": {
            "last_modified_by": "updated_operator",
            "last_modified_on": current_time.isoformat(),
        },
    }

    # Mock for the updated ShiftLogComment model instance
    mock_comment = MagicMock()
    mock_comment.log_comment = updated_comment_data["log_comment"]
    mock_comment.operator_name = updated_comment_data["operator_name"]
    mock_comment.shift_id = shift_initial_comment_data["shift_id"]
    mock_comment.eb_id = shift_initial_comment_data["eb_id"]
    # mock_comment.image = updated_comment_data["image"]
    mock_comment.metadata = {
        **shift_initial_comment_data["metadata"],
        **updated_comment_data["metadata"],
    }

    # Patch database access methods to return initial and updated data
    with (
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get",
            return_value=[
                shift_initial_comment_data
            ],  # Ensures get_shift_logs_comment returns data
        ),
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get_one",
            return_value=shift_initial_comment_data,  # Ensures individual
            # comment retrieval works
        ),
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.update",
            return_value=mock_comment,  # Simulates successful update
        ),
    ):
        # Send a PUT request to update the comment
        comment_id = shift_initial_comment_data["id"]
        response = client.put(
            f"{API_PREFIX}/shift_log_comments/{comment_id}",
            json=updated_comment_data,
        )

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    # Verify the response data matches the update
    updated_comment_response = response.json()[0]
    assert (
        updated_comment_response["log_comment"] == updated_comment_data["log_comment"]
    ), (
        f"Expected log_comment to be '{updated_comment_data['log_comment']}', but got "
        f"'{updated_comment_response['log_comment']}'"
    )
    assert (
        updated_comment_response["operator_name"]
        == updated_comment_data["operator_name"]
    ), (
        f"Expected operator_name to be '{updated_comment_data['operator_name']}',"
        f" but got "
        f"'{updated_comment_response['operator_name']}'"
    )

    # Verify metadata, inlining the normalization
    assert "metadata" in updated_comment_response, "Metadata is missing in the response"
    metadata = updated_comment_response["metadata"]

    # Inline normalization for datetime format comparison
    expected_last_modified_on = datetime.fromisoformat(
        updated_comment_data["metadata"]["last_modified_on"].replace("Z", "+00:00")
    ).isoformat()
    actual_last_modified_on = datetime.fromisoformat(
        metadata["last_modified_on"].replace("Z", "+00:00")
    ).isoformat()

    assert (
        metadata["last_modified_by"]
        == updated_comment_data["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be "
        f"'{updated_comment_data['metadata']['last_modified_by']}', but got "
        f"'{metadata['last_modified_by']}'"
    )
    assert actual_last_modified_on == expected_last_modified_on, (
        f"Expected last_modified_on to be '{expected_last_modified_on}', but got "
        f"'{actual_last_modified_on}'"
    )


def test_get_current_shift(current_shift_data):

    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.services." "shift_service.ShiftService.get_current_shift",
        return_value=current_shift_data,
    ):
        # Send a GET request to the endpoint
        response = client.get(f"{API_PREFIX}/current_shift")
    # Assert the response status code
    assert response.status_code == 200

    # Assert the response content
    retrieved_shift = response.json()
    assert retrieved_shift[0]["shift_id"] == "test-id"


@patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift_comment")
def test_create_shift_comments(mock_create_shift_comment, shift_comment_data):
    # Prepare test data

    mock_create_shift_comment.return_value = shift_comment_data[0]

    # Send a POST request to create a comment
    response = client.post(f"{API_PREFIX}/shift_comment", json=shift_comment_data[0])

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]

    assert created_comment["comment"] == shift_comment_data[0]["comment"], (
        f"Expected comment to be '{shift_comment_data[0]['comment']}'"
        f", but got '{created_comment['comment']}'"
    )

    # Add more assertions as needed
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]
    assert metadata["created_by"] == shift_comment_data[0]["metadata"]["created_by"], (
        f"Expected created_by to be '{shift_comment_data[0]['metadata']['created_by']}'"
        f", but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"]
        == shift_comment_data[0]["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{shift_comment_data[0]['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )

    # Verify that the mocked function was called with the correct arguments
    # mock_create_shift_comment.assert_called_once_with(comment_data)


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift_comments")
def test_get_shift_comments(mock_get_shift_comments, shift_comment_data):

    mock_get_shift_comments.return_value = shift_comment_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shift_comment?shift_id=test-shift-id")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0][0]
    assert created_comment["comment"] == shift_comment_data[0]["comment"], (
        f"Expected comment to be '{shift_comment_data[0]['comment']}',"
        f" but got '{created_comment['comment']}'"
    )

    # Add more assertions as needed
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]
    assert metadata["created_by"] == shift_comment_data[0]["metadata"]["created_by"], (
        f"Expected created_by to be "
        f"'{shift_comment_data[0]['metadata']['created_by']}',"
        f" but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"]
        == shift_comment_data[0]["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{shift_comment_data[0]['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.update_shift_comments")
def test_update_shift_comments(mock_update_shift_comment, shift_comment_data):
    # Prepare test data
    data_to_be_updated = {"comment": "This is a test comment"}

    mock_update_shift_comment.return_value = shift_comment_data[0]

    # Send a POST request to create a comment
    response = client.put(f"{API_PREFIX}/shift_comment/1", json=data_to_be_updated)

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]
    assert created_comment["comment"] == data_to_be_updated["comment"], (
        f"Expected comment to be '{created_comment['comment']}',"
        f" but got '{created_comment['comment']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.post_media")
@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
def test_create_shift_comment_image(
    mock_get_shift, mock_shift_comment_image, shift_comment_image_data
):

    test_file = {"file": ("test_image.png", b"dummy image content", "image/png")}
    mock_shift_comment_image.return_value = shift_comment_image_data

    mock_shift_data = Mock(spec=Shift)
    mock_shift_data.shift_id = "shift-123"
    mock_shift_data.shift_operator = "John Doe"
    mock_get_shift.return_value = mock_shift_data
    # Send a POST request to the endpoint
    response = client.post(
        f"{API_PREFIX}/shift_comment/upload_image?shift_id=shift-20241111-2"
        "&shift_operator=test",
        files=test_file,
    )

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert (
        created_shift[0]["operator_name"] == shift_comment_image_data["operator_name"]
    ), (
        f"Expected operator_name to be '{shift_comment_image_data['operator_name']}'"
        ", but got"
        f" '{created_shift[0]['operator_name']}'"
    )
    assert created_shift[0]["shift_id"] == shift_comment_image_data["shift_id"], (
        f"Expected shift_id to be '{shift_comment_image_data['shift_id']}', but got"
        f" '{created_shift[0]['shift_id']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.add_media")
def test_add_shift_comment_image(mock_shift_comment_image, shift_comment_image_data):
    # Prepare test data with metadata
    test_file = {"files": ("test_image.png", b"dummy image content", "image/png")}

    mock_shift_comment_image.return_value = shift_comment_image_data["image"]

    # Send a POST request to the endpoint
    response = client.put(f"{API_PREFIX}/shift_comment/upload_image/2", files=test_file)

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch(
    "ska_oso_slt_services.services."
    "shift_comments_service.ShiftComments.get_media_for_comment"
)
def test_get_shift_comment_image(
    mock_shift_comment_image, get_shift_comment_image_data
):

    mock_shift_comment_image.return_value = get_shift_comment_image_data
    # Send a POST request to the endpoint
    response = client.get(f"{API_PREFIX}/shift_comment/download_images/3")

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
def test_get_shift(mock_get_shift_comments, shift_data):

    mock_get_shift_comments.return_value = shift_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shift?shift_id='shift-20241112-1'")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()[0][0]

    assert (
        created_shift["comments"][0]["comment"]
        == shift_data[0]["comments"][0]["comment"]
    )
    assert (
        created_shift["shift_logs"][0]["comments"][0]["log_comment"]
        == shift_data[0]["shift_logs"][0]["comments"][0]["log_comment"]
    )
    # Add more assertions as needed
    assert "metadata" in created_shift, "Metadata is missing in the response"
    metadata = created_shift["metadata"]
    assert metadata["created_by"] == shift_data[0]["metadata"]["created_by"], (
        f"Expected created_by to be '{shift_data[0]['metadata']['created_by']}',"
        f" but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"] == shift_data[0]["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{shift_data[0]['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shifts")
def test_get_shifts(mock_get_shift_log_comments, shift_history_data):

    mock_get_shift_log_comments.return_value = shift_history_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shifts?match_type=equals&sbi_status=Created")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()[0][0]

    assert (
        created_shift["comments"][0]["comment"]
        == shift_history_data[0]["comments"][0]["comment"]
    )
    assert (
        created_shift["shift_logs"][0]["comments"][0]["log_comment"]
        == shift_history_data[0]["shift_logs"][0]["comments"][0]["log_comment"]
    )
    # Add more assertions as needed
    assert "metadata" in created_shift, "Metadata is missing in the response"
    metadata = created_shift["metadata"]
    assert metadata["created_by"] == shift_history_data[0]["metadata"]["created_by"], (
        f"Expected created_by to be "
        f"'{shift_history_data[0]['metadata']['created_by']}',"
        f" but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"]
        == shift_history_data[0]["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{shift_history_data[0]['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )
    response = client.get(
        f"{API_PREFIX}/shifts?match_type=contains&sbi_id=sbi-t0001-20240822-00009"
    )
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()[0][0]
    assert (
        created_shift["comments"][0]["comment"]
        == shift_history_data[0]["comments"][0]["comment"]
    )
    response = client.get(
        f"{API_PREFIX}/shifts?match_type=contains&eb_id=eb-t0001-20241022-00002"
    )
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"
    created_shift = response.json()[0][0]

    assert (
        created_shift["comments"][0]["comment"]
        == shift_history_data[0]["comments"][0]["comment"]
    )


@patch(
    "ska_oso_slt_services.services.shift_service.ShiftService.create_shift_logs_comment"
)
def test_create_shift_log_comment(mock_create_shift_comment, shift_log_comment_data):

    mock_create_shift_comment.return_value = shift_log_comment_data[0]

    # Send a POST request to create a comment
    response = client.post(
        f"{API_PREFIX}/shift_log_comments", json=shift_log_comment_data[0]
    )

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]
    assert created_comment["log_comment"] == shift_log_comment_data[0]["log_comment"], (
        f"Expected log_comment to be '{shift_log_comment_data[0]['log_comment']}',"
        "but got"
        f" '{created_comment['log_comment']}'"
    )
    assert (
        created_comment["operator_name"] == shift_log_comment_data[0]["operator_name"]
    ), (
        f"Expected operator_name to be '{shift_log_comment_data[0]['operator_name']}',"
        "but got"
        f" '{created_comment['operator_name']}'"
    )
    assert (
        created_comment["image"][0]["path"]
        == shift_log_comment_data[0]["image"][0]["path"]
    ), (
        f"Expected image path to be '{shift_log_comment_data[0]['image']['path']}',"
        "but got"
        f" '{created_comment['image']['path']}'"
    )

    # Verify metadata
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]

    assert (
        metadata["created_by"] == shift_log_comment_data[0]["metadata"]["created_by"]
    ), (
        f"Expected created_by to be "
        f"'{shift_log_comment_data[0]['metadata']['created_by']}'"
        f", but got '{metadata['created_by']}'"
    )

    assert (
        metadata["last_modified_by"]
        == shift_log_comment_data[0]["metadata"]["last_modified_by"]
    ), (
        "Expected last_modified_by to be"
        f" '{shift_log_comment_data[0]['metadata']['last_modified_by']}', but got"
        f" '{metadata['last_modified_by']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.post_media")
@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
def test_post_shift_log_comment_image(
    mock_get_shift, mock_shift_comment_image, shift_log_comment_image_data
):
    # Prepare test data with metadata
    test_file = {"file": ("test_image.png", b"dummy image content", "image/png")}

    mock_shift_comment_image.return_value = shift_log_comment_image_data
    mock_shift_data = Mock(spec=Shift)
    mock_shift_data.shift_id = "shift-123"
    mock_shift_data.shift_operator = "John Doe"
    mock_get_shift.return_value = mock_shift_data
    # Send a POST request to the endpoint
    response = client.post(
        f"{API_PREFIX}/shift_log_comments/upload_image?shift_id=shift-20241111-2"
        "&shift_operator=test&eb_id=test-id",
        files=test_file,
    )
    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert (
        created_shift[0]["operator_name"]
        == shift_log_comment_image_data["operator_name"]
    ), (
        f"Expected operator_name to be "
        f"'{shift_log_comment_image_data['operator_name']}'"
        f", but got '{created_shift[0]['operator_name']}'"
    )

    assert created_shift[0]["shift_id"] == shift_log_comment_image_data["shift_id"], (
        f"Expected shift_id to be '{shift_log_comment_image_data['shift_id']}', but got"
        f" '{created_shift[0]['shift_id']}'"
    )


@patch(
    "ska_oso_slt_services.repository."
    "postgres_shift_repository.PostgresShiftRepository.get_media"
)
def test_get_shift_log_comment_image(
    mock_shift_comment_image, get_shift_comment_image_data
):

    mock_shift_comment_image.return_value = get_shift_comment_image_data

    # Send a POST request to the endpoint
    response = client.get(f"{API_PREFIX}/shift_log_comments/download_images/3")

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch(
    "ska_oso_slt_services.services.shift_service.ShiftService.updated_shift_log_info"
)
def test_patch_shift_log_info_success(mock_update_shift, shift_patch_log_data):
    """Test successful update of shift log info."""

    # Configure mock to return the expected response
    mock_update_shift.return_value = shift_patch_log_data

    # Create test client
    client = TestClient(app)

    # Make request to the endpoint
    response = client.patch(
        f"{API_PREFIX}/shifts/patch/update_shift_log_info/shift-20241112-1"
    )

    # Assertions
    assert response.status_code == HTTPStatus.OK
    assert response.json()[0] == shift_patch_log_data

    # Verify mock was called with correct arguments
    mock_update_shift.assert_called_once_with(
        current_shift_id=shift_patch_log_data["shift_id"]
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService." "add_media")
def test_add_shift_log_comment_image(
    mock_shift_comment_image, shift_log_comment_image_data
):

    test_file = {"files": ("test_image.png", b"dummy image content", "image/png")}
    mock_shift_comment_image.return_value = shift_log_comment_image_data["image"]

    # Send a POST request to the endpoint
    response = client.put(
        f"{API_PREFIX}/shift_log_comments/upload_image/2",
        files=test_file,
    )
    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch("ska_oso_slt_services.routers.shift_router.ShiftService.update_shift_end_time")
def test_update_shift_end_time(mock_shift_end_data):

    current_time = get_datetime_for_timezone("UTC")

    shift_data = {
        "operator_name": "Ross",
        "metadata": {
            "created_by": "test",
            "created_on": current_time.isoformat(),
            "last_modified_by": "Ross",
            "last_modified_on": current_time.isoformat(),
        },
    }

    mock_shift_end_data.return_value = shift_data

    response = client.put(
        f"{API_PREFIX}/shift/end/sl-t0001-20241204-00004", json=shift_data
    )

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()

    print(f"@@@@@@@@@@@@ {created_shift}")

    print(f"!!!!!!!!!!!! {created_shift[0]}")

    assert created_shift[0]["operator_name"] == shift_data["operator_name"], (
        f"Expected operator_name to be "
        f"'{shift_data['operator_name']}'"
        f", but got '{created_shift[0]['operator_name']}'"
    )
