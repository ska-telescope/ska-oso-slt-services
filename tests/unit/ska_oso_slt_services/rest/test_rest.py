from datetime import datetime
from http import HTTPStatus
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ska_oso_slt_services import create_app  # Import your create_app function
from ska_oso_slt_services.app import API_PREFIX
from ska_oso_slt_services.utils.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.utils.date_utils import get_datetime_for_timezone

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


def test_create_shift():
    # Prepare test data with metadata
    current_time = get_datetime_for_timezone("UTC")
    shift_data = {
        "shift_operator": "test",
        "metadata": {
            "created_by": "test",
            "created_on": current_time.isoformat(),
            "last_modified_by": "test",
            "last_modified_on": current_time.isoformat(),
        },
    }
    # Create a mock for the shift model
    mock_shift = MagicMock()
    mock_shift.shift_operator = shift_data["shift_operator"]
    mock_shift.created_by = shift_data["metadata"]["created_by"]
    mock_shift.created_on = current_time
    mock_shift.last_modified_by = shift_data["metadata"]["last_modified_by"]
    mock_shift.last_modified_on = current_time

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
            "ska_oso_slt_services.services.shift_service.Shift", return_value=mock_shift
        ),
    ):
        with patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get_one",
            return_value={"max": 5},
        ):

            # Send a POST request to the endpoint
            response = client.post(f"{API_PREFIX}/shifts/create", json=shift_data)
    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert created_shift[0]["shift_operator"] == shift_data["shift_operator"], (
        f"Expected shift_operator to be '{shift_data['shift_operator']}', but got"
        f" '{created_shift[0]['shift_operator']}'"
    )

    # Verify metadata
    assert "metadata" in created_shift[0], "Metadata is missing in the response"
    metadata = created_shift[0]["metadata"]
    assert metadata["created_by"] == shift_data["metadata"]["created_by"], (
        f"Expected created_by to be '{shift_data['metadata']['created_by']}', but got"
        f" '{metadata['created_by']}'"
    )
    assert metadata["last_modified_by"] == shift_data["metadata"]["last_modified_by"], (
        "Expected last_modified_by to be"
        f" '{shift_data['metadata']['last_modified_by']}', but got"
        f" '{metadata['last_modified_by']}'"
    )

    mock_insert.assert_called_once()


def test_update_shift():
    # Existing shift data structure
    existing_shift = {
        "shift_id": "test-id-1",
        "shift_start": get_datetime_for_timezone("UTC"),
        "shift_end": None,
        "shift_operator": "old-operator",
        "shift_logs": [
            {
                "info": {},
                "source": "test",
                "log_time": get_datetime_for_timezone("UTC"),
                "comments": [],
            }
        ],
        "media": [],
        "annotations": "old-annotation",
        "comments": [
            {
                "id": 1,
                "comment": "test-comment-1",
                "shift_id": "test-id-1",
                "image": {
                    "path": "file_path",
                    "timestamp": get_datetime_for_timezone("UTC"),
                },
                "metadata": {},
            }
        ],
        "created_by": "test-user-1",
        "created_on": get_datetime_for_timezone("UTC"),
        "last_modified_by": "test-user-1",
        "last_modified_on": get_datetime_for_timezone("UTC"),
    }

    # Updated shift data for the test
    update_data = {
        "shift_id": "test-id-1",
        "shift_start": "2024-09-14T16:49:54.889Z",
        "shift_operator": "old-operator",
        "shift_logs": [],
        "media": [],
        "annotations": "updated-annotation",
        "comments": [
            {
                "id": 2,
                "comment": "test-comment-1",
                "shift_id": "test-id-1",
                "image": [
                    {"path": "file_path", "timestamp": "2024-09-14T16:49:54.889Z"}
                ],
                "metadata": {},
            }
        ],
        "metadata": {
            "created_by": "test-user-1",
            "created_on": "2024-09-14T16:49:54.889Z",
            "last_modified_by": "test-user-1",
            "last_modified_on": "2024-09-14T16:49:54.889Z",
        },
    }

    # Expected shift data after the update
    expected_updated_shift = {**existing_shift, **update_data}

    # Patch ShiftService.update_shift directly to return the expected updated shift
    with patch(
        "ska_oso_slt_services.services.shift_service.ShiftService.update_shift",
        return_value=[expected_updated_shift],  # Return as a list for consistency
    ):
        # Send PUT request
        response = client.put(
            f"{API_PREFIX}/shifts/update/{existing_shift['shift_id']}",
            json=update_data,
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

    assert updated_shift_response["shift_id"] == existing_shift["shift_id"]
    assert updated_shift_response["shift_operator"] == update_data["shift_operator"]
    assert updated_shift_response["annotations"] == update_data["annotations"]
    assert updated_shift_response["comments"] == update_data["comments"]


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


def test_update_shift_log_comment():
    # Existing comment data with initial metadata
    current_time = get_datetime_for_timezone("UTC")
    initial_comment_data = {
        "id": 1,
        "log_comment": "This is the original comment",
        "operator_name": "original_operator",
        "shift_id": "test-shift-id",
        "eb_id": "test-eb-id",
        "metadata": {
            "created_by": "original_operator",
            "created_on": current_time.isoformat(),
            "last_modified_by": "original_operator",
            "last_modified_on": current_time.isoformat(),
        },
    }

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
    mock_comment.id = initial_comment_data["id"]
    mock_comment.log_comment = updated_comment_data["log_comment"]
    mock_comment.operator_name = updated_comment_data["operator_name"]
    mock_comment.shift_id = initial_comment_data["shift_id"]
    mock_comment.eb_id = initial_comment_data["eb_id"]
    # mock_comment.image = updated_comment_data["image"]
    mock_comment.metadata = {
        **initial_comment_data["metadata"],
        **updated_comment_data["metadata"],
    }

    # Patch database access methods to return initial and updated data
    with (
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get",
            return_value=[
                initial_comment_data
            ],  # Ensures get_shift_logs_comment returns data
        ),
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.get_one",
            return_value=initial_comment_data,  # Ensures individual
            # comment retrieval works
        ),
        patch(
            "ska_oso_slt_services.data_access.postgres"
            ".execute_query.PostgresDataAccess.update",
            return_value=mock_comment,  # Simulates successful update
        ),
    ):
        # Send a PUT request to update the comment
        comment_id = initial_comment_data["id"]
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


def test_get_current_shift():
    # Mock shift data
    mock_shift = {
        "shift_id": "test-id",
        "shift_start": get_datetime_for_timezone("UTC"),
        "shift_operator": "test",
        "shift_logs": [
            {
                "info": {},
                "source": "test",
                "log_time": get_datetime_for_timezone("UTC"),
            }
        ],
        "media": [{"type": "test", "path": "test"}],
        "annotations": "test",
        "comments": "test",
        "created_by": "test",
        "created_on": get_datetime_for_timezone("UTC"),
        "last_modified_by": "test",
        "last_modified_on": get_datetime_for_timezone("UTC"),
    }
    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.services." "shift_service.ShiftService.get_current_shift",
        return_value=mock_shift,
    ):
        # Send a GET request to the endpoint
        response = client.get(f"{API_PREFIX}/current_shift")
    # Assert the response status code
    assert response.status_code == 200

    # Assert the response content
    retrieved_shift = response.json()
    assert retrieved_shift[0]["shift_id"] == "test-id"


@patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift_comment")
def test_create_shift_comments(mock_create_shift_comment):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")
    comment_data = {
        "comment": "This is a test comment",
        "shift_id": "test-shift-id",
        "image": [{"path": "https://example.com/image.png"}],
        "metadata": {
            "created_by": "test_user",
            "created_on": current_time.isoformat(),
            "last_modified_by": "test_user",
            "last_modified_on": current_time.isoformat(),
        },
    }

    mock_create_shift_comment.return_value = comment_data

    # Send a POST request to create a comment
    response = client.post(f"{API_PREFIX}/shift_comments/create", json=comment_data)

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]
    print(f"created_comment['comment'] {created_comment['comment']}")
    print(f"comment_data['comment'] {comment_data['comment']}")
    assert created_comment["comment"] == comment_data["comment"], (
        f"Expected comment to be '{comment_data['comment']}'"
        f", but got '{created_comment['comment']}'"
    )

    # Add more assertions as needed
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]
    assert metadata["created_by"] == comment_data["metadata"]["created_by"], (
        f"Expected created_by to be '{comment_data['metadata']['created_by']}'"
        f", but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"] == comment_data["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{comment_data['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )

    # Verify that the mocked function was called with the correct arguments
    # mock_create_shift_comment.assert_called_once_with(comment_data)


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift_comments")
def test_get_shift_comments(mock_get_shift_comments):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")

    comment_data = [
        {
            "comment": "This is a test comment",
            "shift_id": "test-shift-id",
            "image": {"path": "https://example.com/image.png"},
            "metadata": {
                "created_by": "test_user",
                "created_on": current_time.isoformat(),
                "last_modified_by": "test_user",
                "last_modified_on": current_time.isoformat(),
            },
        },
        {
            "comment": "This is a test comment",
            "shift_id": "test-shift-id",
            "image": {"path": "https://example.com/image.png"},
            "metadata": {
                "created_by": "test_user",
                "created_on": current_time.isoformat(),
                "last_modified_by": "test_user",
                "last_modified_on": current_time.isoformat(),
            },
        },
    ]

    mock_get_shift_comments.return_value = comment_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shift_comments?shift_id=test-shift-id")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0][0]
    assert created_comment["comment"] == comment_data[0]["comment"], (
        f"Expected comment to be '{comment_data[0]['comment']}',"
        f" but got '{created_comment['comment']}'"
    )

    # Add more assertions as needed
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]
    assert metadata["created_by"] == comment_data[0]["metadata"]["created_by"], (
        f"Expected created_by to be '{comment_data[0]['metadata']['created_by']}',"
        f" but got '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"] == comment_data[0]["metadata"]["last_modified_by"]
    ), (
        f"Expected last_modified_by to be"
        f" '{comment_data[0]['metadata']['last_modified_by']}'"
        f", but got '{metadata['last_modified_by']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.update_shift_comments")
def test_update_shift_comments(mock_update_shift_comment):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")

    data_to_be_updated = {"comment": "This is a updated test comment"}

    updated_comment_data = {
        "comment": "This is a updated test comment",
        "shift_id": "test-shift-id",
        "image": {"path": "https://example.com/image.png"},
        "metadata": {
            "created_by": "test_user",
            "created_on": current_time.isoformat(),
            "last_modified_by": "test_user",
            "last_modified_on": current_time.isoformat(),
        },
    }

    mock_update_shift_comment.return_value = updated_comment_data

    # Send a POST request to create a comment
    response = client.put(
        f"{API_PREFIX}/shift_comments/update/1", json=data_to_be_updated
    )

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]
    assert created_comment["comment"] == data_to_be_updated["comment"], (
        f"Expected comment to be '{created_comment['comment']}',"
        f" but got '{created_comment['comment']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.post_media")
def test_create_shift_comment_image(mock_shift_comment_image):
    # Prepare test data with metadata
    test_file = {"file": ("test_image.png", b"dummy image content", "image/png")}
    shift_data = {
        "operator_name": "Monica",
        "shift_id": "shift-20241111-2",
        "image": [
            {
                "path": "https://skao-611985328822-shift-log-tool-storage.s3."
                "amazonaws.com/4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "unique_id": "4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "timestamp": "2024-11-11T15:46:13.223618Z",
            }
        ],
        "metadata": {
            "created_by": "Monica",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_by": "Monica",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
        },
    }

    mock_shift_comment_image.return_value = shift_data

    # Send a POST request to the endpoint
    response = client.post(
        f"{API_PREFIX}/shift_comments/upload_image?shift_id=shift-20241111-2"
        "&shift_operator=test",
        files=test_file,
    )

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert created_shift[0]["operator_name"] == shift_data["operator_name"], (
        f"Expected operator_name to be '{shift_data['operator_name']}', but got"
        f" '{created_shift[0]['operator_name']}'"
    )
    assert created_shift[0]["shift_id"] == shift_data["shift_id"], (
        f"Expected shift_id to be '{shift_data['shift_id']}', but got"
        f" '{created_shift[0]['shift_id']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.add_media")
def test_add_shift_comment_image(mock_shift_comment_image):
    # Prepare test data with metadata
    test_file = {"files": ("test_image.png", b"dummy image content", "image/png")}
    shift_data = [
        {
            "path": "https://skao-611985328822-shift-log-tool-storage.s3."
            "amazonaws.com/d03269ecb544276928aad4916b0a1f5c11d6ebe9e2439d"
            "b4708369f72fcf1746.jpeg",
            "unique_id": "d03269ecb544276928aad4916b0a1f5c11d6ebe9e2439db"
            "4708369f72fcf1746.jpeg",
            "timestamp": "2024-11-11T15:42:58.481265Z",
        }
    ]

    mock_shift_comment_image.return_value = shift_data

    # Send a POST request to the endpoint
    response = client.put(
        f"{API_PREFIX}/shift_comments/upload_image/2", files=test_file
    )

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_media")
def test_get_shift_comment_image(mock_shift_comment_image):

    shift_data = [
        {
            "file_key": "4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
            "53284f533d34e0b5f6.jpeg",
            "media_content": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxIQEh"
            "UQEBIVFRUVFRcVFRUXFRUVGBgXFRUWFhgVFRUYHSggGBolGxUYITIhJSkrLi"
            "4uFx8zODMtNygtLisBCgoKDg0OGBAQGi0fHx8tLS0tLS0tLS0tLS0tLS0tLS0"
            "tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAOAA4QMBIgAC"
            "EQEDEQH/xAAbAAABBQEBAAAAAAAAAAAAAAADAAECBAUGB//EAD0QAAEDAgQEA"
            "wcDAwMCBwAAAAEAAhEDIQQSMUEFUWFxBiKBE5GhscHR8DJC4RQjUgcVYpLxM1"
            "NUcoKTov/EABkBAQEBAQEBAAAAAAAAAAAAAAABAgMEBf/EAB8RAQEBAQACAgMB"
            "AAAAAAAAAAABEQISITFBE1FhA//aAAwDAQACEQMRAD8AohqWVGyp8i+Vj0A5Us"
            "qNkSyJgBlSyo+RNlTAHKnyouRPlTFCDU+VFDU4amAYapBqIGpw1MAw1SDUQNUg"
            "1MMQDUQNThqmAmGGAUgE4CkAmCMJQpQnhXEQhNCJCUKgRCiQjZVEtTAAtQy1WS"
            "1QLVcFZzUJzVac1Cc1BXyp0TKnQFyp8qLlSypi4FlSyomVKFMAoSyouVNlTALK"
            "nyouVLKrihhqkGqYapBqYIBqkGogYpBiuAYanDUUMT5UwDDU+VEyp4TBABOApwk"
            "ApiIwlCnCeFcEMqWVThPCYB5VEtRsqYtTDAC1QLVYIUCFcMVi1Dc1WnNQnNUMV8"
            "qSLlSRBsqWVThPCuNBFqbKiwllTAPKllRcqfKmAWVLKi5UoTAMNUg1TATgKiIap"
            "AKQCcNTBGE4CmGp8quCEJ4UgE8KYIQnAU4TwmCEJ4UoShMEYSU4ShMEITEIiZXAM"
            "tUC1GITEJgruahuarJahuCgrwkiwkgJCaEXKllVwChKETKnypgGGp8qJCeEA8qWV"
            "EhPCAYanDVOE8KiIanAUgFIBFRDU8KcJQghCUKcJQgjCUKUJ4REITwpJQgjCUKUJ"
            "4QQhNCnCUIBwmIRCFGEAyENzUchQcEAcqSJCSYJwlClCaEVGEymoqIUJ0ydA6SaUp",
            "content_type": "image/jpeg",
        }
    ]

    mock_shift_comment_image.return_value = shift_data

    # Send a POST request to the endpoint
    response = client.get(f"{API_PREFIX}/shift_comments/download_images/3")

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
def test_get_shift(mock_get_shift_comments):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")
    shift_comments = [
        {
            "id": 1,
            "comment": "This is updated comment",
            "operator_name": "johnny",
            "shift_id": "shift-20241112-1",
            "metadata": {
                "created_by": "john",
                "created_on": current_time,
                "last_modified_by": "john",
                "last_modified_on": current_time,
            },
        }
    ]
    shift_log_comments = [
        {
            "id": 1,
            "log_comment": "This is log comment",
            "operator_name": "max",
            "shift_id": "shift-20241112-1",
            "eb_id": "eb-t0001-20241022-00002",
            "metadata": {
                "created_by": "max",
                "created_on": "2024-11-12T14:21:47.447462+05:30",
                "last_modified_by": "max",
                "last_modified_on": "2024-11-12T14:21:47.447462+05:30",
            },
        }
    ]
    shift_data = [
        {
            "shift_id": "shift-20241112-1",
            "shift_start": "2024-11-12T13:04:55.874585+05:30",
            "shift_operator": "john",
            "comments": shift_comments,
            "shift_logs": [
                {
                    "info": {
                        "eb_id": "eb-t0001-20241022-00002",
                        "sbd_ref": "sbd-t0001-20240822-00008",
                        "sbi_ref": "sbi-t0001-20240822-00009",
                        "metadata": {
                            "version": 1,
                            "created_by": "DefaultUser",
                            "created_on": "2024-10-22T11:25:36.953526Z",
                            "pdm_version": "15.4.0",
                            "last_modified_by": "DefaultUser",
                            "last_modified_on": "2024-10-22T11:25:36.953526Z",
                        },
                        "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                        "telescope": "ska_mid",
                        "sbi_status": "failed",
                        "sbd_version": 1,
                        "request_responses": [
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.assign_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting."
                                "functions.devicecontrol.configure_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.scan",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions."
                                "devicecontrol.release_all_resources",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "error": {"detail": "this is an error"},
                                "status": "ERROR",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.end",
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            },
                        ],
                    },
                    "source": "ODA",
                    "log_time": "2024-10-22T11:24:14.406107Z",
                    "comments": shift_log_comments,
                }
            ],
            "metadata": {
                "created_by": "john",
                "created_on": "2024-11-12T13:04:55.860503+05:30",
                "last_modified_by": "max1",
                "last_modified_on": "2024-11-12T20:52:10.208101+05:30",
            },
        },
        200,
    ]

    mock_get_shift_comments.return_value = shift_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shift?shift_id='shift-20241112-1'")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()[0][0]

    assert created_shift["comments"][0]["comment"] == shift_comments[0]["comment"]
    assert (
        created_shift["shift_logs"][0]["comments"][0]["log_comment"]
        == shift_log_comments[0]["log_comment"]
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
def test_get_shifts(mock_get_shift_log_comments):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")

    current_time = get_datetime_for_timezone("UTC")
    shift_comments = [
        {
            "id": 1,
            "comment": "This is updated comment",
            "operator_name": "johnny",
            "shift_id": "shift-20241112-1",
            "metadata": {
                "created_by": "john",
                "created_on": current_time,
                "last_modified_by": "john",
                "last_modified_on": current_time,
            },
        },
        {
            "id": 2,
            "comment": "This is updated comment",
            "operator_name": "johnny",
            "shift_id": "shift-20241112-2",
            "metadata": {
                "created_by": "john",
                "created_on": current_time,
                "last_modified_by": "john",
                "last_modified_on": current_time,
            },
        },
    ]
    shift_log_comments = [
        {
            "id": 1,
            "log_comment": "This is log comment",
            "operator_name": "max",
            "shift_id": "shift-20241112-1",
            "eb_id": "eb-t0001-20241022-00002",
            "metadata": {
                "created_by": "max",
                "created_on": "2024-11-12T14:21:47.447462+05:30",
                "last_modified_by": "max",
                "last_modified_on": "2024-11-12T14:21:47.447462+05:30",
            },
        },
        {
            "id": 2,
            "log_comment": "This is log comment",
            "operator_name": "max",
            "shift_id": "shift-20241112-2",
            "eb_id": "eb-t0001-20241022-00002",
            "metadata": {
                "created_by": "max",
                "created_on": "2024-11-12T14:21:47.447462+05:30",
                "last_modified_by": "max",
                "last_modified_on": "2024-11-12T14:21:47.447462+05:30",
            },
        },
    ]

    shift_data = [
        {
            "shift_id": "shift-20241112-1",
            "shift_start": "2024-11-12T13:04:55.874585+05:30",
            "shift_operator": "john",
            "comments": shift_comments,
            "shift_logs": [
                {
                    "info": {
                        "eb_id": "eb-t0001-20241022-00002",
                        "sbd_ref": "sbd-t0001-20240822-00008",
                        "sbi_ref": "sbi-t0001-20240822-00009",
                        "metadata": {
                            "version": 1,
                            "created_by": "DefaultUser",
                            "created_on": "2024-10-22T11:25:36.953526Z",
                            "pdm_version": "15.4.0",
                            "last_modified_by": "DefaultUser",
                            "last_modified_on": "2024-10-22T11:25:36.953526Z",
                        },
                        "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                        "telescope": "ska_mid",
                        "sbi_status": "failed",
                        "sbd_version": 1,
                        "request_responses": [
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.assign_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting."
                                "functions.devicecontrol.configure_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.scan",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol"
                                ".release_all_resources",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "error": {"detail": "this is an error"},
                                "status": "ERROR",
                                "request": "ska_oso_scripting."
                                "functions.devicecontrol.end",
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            },
                        ],
                    },
                    "source": "ODA",
                    "log_time": "2024-10-22T11:24:14.406107Z",
                    "comments": shift_log_comments,
                }
            ],
            "metadata": {
                "created_by": "john",
                "created_on": "2024-11-12T13:04:55.860503+05:30",
                "last_modified_by": "max1",
                "last_modified_on": "2024-11-12T20:52:10.208101+05:30",
            },
        },
        {
            "shift_id": "shift-20241112-2",
            "shift_start": "2024-11-12T13:04:55.874585+05:30",
            "shift_operator": "john",
            "comments": shift_comments,
            "shift_logs": [
                {
                    "info": {
                        "eb_id": "eb-t0001-20241022-00002",
                        "sbd_ref": "sbd-t0001-20240822-00008",
                        "sbi_ref": "sbi-t0001-20240822-00009",
                        "metadata": {
                            "version": 1,
                            "created_by": "DefaultUser",
                            "created_on": "2024-10-22T11:25:36.953526Z",
                            "pdm_version": "15.4.0",
                            "last_modified_by": "DefaultUser",
                            "last_modified_on": "2024-10-22T11:25:36.953526Z",
                        },
                        "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                        "telescope": "ska_mid",
                        "sbi_status": "failed",
                        "sbd_version": 1,
                        "request_responses": [
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting."
                                "functions.devicecontrol.assign_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting"
                                ".functions"
                                ".devicecontrol.configure_resource",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting."
                                "functions.devicecontrol.scan",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "status": "OK",
                                "request": "ska_oso_scripting."
                                "functions"
                                ".devicecontrol.release_all_resources",
                                "response": {"result": "this is a result"},
                                "request_args": {"kwargs": {"subarray_id": "1"}},
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                                "response_received_at": "2022-09-23T15:43:53.971548Z",
                            },
                            {
                                "error": {"detail": "this is an error"},
                                "status": "ERROR",
                                "request": "ska_oso_scripting"
                                ".functions.devicecontrol.end",
                                "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            },
                        ],
                    },
                    "source": "ODA",
                    "log_time": "2024-10-22T11:24:14.406107Z",
                    "comments": shift_log_comments,
                }
            ],
            "metadata": {
                "created_by": "john",
                "created_on": "2024-11-12T13:04:55.860503+05:30",
                "last_modified_by": "max1",
                "last_modified_on": "2024-11-12T20:52:10.208101+05:30",
            },
        },
        200,
    ]

    mock_get_shift_log_comments.return_value = shift_data

    # Send a POST request to create a comment
    response = client.get(f"{API_PREFIX}/shifts?match_type=equals&sbi_status=Created")

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()[0][0]

    assert created_shift["comments"][0]["comment"] == shift_comments[0]["comment"]
    assert (
        created_shift["shift_logs"][0]["comments"][0]["log_comment"]
        == shift_log_comments[0]["log_comment"]
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


@patch(
    "ska_oso_slt_services.services.shift_service.ShiftService.create_shift_logs_comment"
)
def test_create_shift_log_comment(mock_create_shift_comment):
    # Prepare test data
    current_time = get_datetime_for_timezone("UTC")
    comment_data = {
        "log_comment": "This is a test comment",
        "operator_name": "test_operator",
        "shift_id": "test-shift-id",
        "eb_id": "test-eb-id",
        "image": [
            {
                "path": "https://skao-611985328822-shift-log-tool-storage.s3."
                "amazonaws.com/4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "unique_id": "4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "timestamp": "2024-11-11T15:46:13.223618Z",
            }
        ],
        "metadata": {
            "created_by": "test_operator",
            "created_on": current_time.isoformat(),
            "last_modified_by": "test_operator",
            "last_modified_on": current_time.isoformat(),
        },
    }

    mock_create_shift_comment.return_value = comment_data

    # Send a POST request to create a comment
    response = client.post(f"{API_PREFIX}/shift_log_comments", json=comment_data)

    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_comment = response.json()[0]
    assert created_comment["log_comment"] == comment_data["log_comment"], (
        f"Expected log_comment to be '{comment_data['log_comment']}', but got"
        f" '{created_comment['log_comment']}'"
    )
    assert created_comment["operator_name"] == comment_data["operator_name"], (
        f"Expected operator_name to be '{comment_data['operator_name']}', but got"
        f" '{created_comment['operator_name']}'"
    )
    assert created_comment["image"][0]["path"] == comment_data["image"][0]["path"], (
        f"Expected image path to be '{comment_data['image']['path']}', but got"
        f" '{created_comment['image']['path']}'"
    )

    # Verify metadata
    assert "metadata" in created_comment, "Metadata is missing in the response"
    metadata = created_comment["metadata"]
    assert metadata["created_by"] == comment_data["metadata"]["created_by"], (
        f"Expected created_by to be '{comment_data['metadata']['created_by']}', but got"
        f" '{metadata['created_by']}'"
    )
    assert (
        metadata["last_modified_by"] == comment_data["metadata"]["last_modified_by"]
    ), (
        "Expected last_modified_by to be"
        f" '{comment_data['metadata']['last_modified_by']}', but got"
        f" '{metadata['last_modified_by']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.post_media")
def test_post_shift_log_comment_image(mock_shift_comment_image):
    # Prepare test data with metadata
    test_file = {"file": ("test_image.png", b"dummy image content", "image/png")}
    shift_data = {
        "operator_name": "Monica",
        "shift_id": "shift-20241111-2",
        "eb_id": "test-id",
        "image": [
            {
                "path": "https://skao-611985328822-shift-log-tool-storage.s3."
                "amazonaws.com/4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "unique_id": "4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
                "53284f533d34e0b5f6.jpeg",
                "timestamp": "2024-11-11T15:46:13.223618Z",
            }
        ],
        "metadata": {
            "created_by": "Monica",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_by": "Monica",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
        },
    }

    mock_shift_comment_image.return_value = shift_data

    # Send a POST request to the endpoint
    response = client.post(
        f"{API_PREFIX}/shift_comments/upload_image?shift_id=shift-20241111-2"
        "&shift_operator=test",
        files=test_file,
    )

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"

    created_shift = response.json()
    assert created_shift[0]["operator_name"] == shift_data["operator_name"], (
        f"Expected operator_name to be '{shift_data['operator_name']}', but got"
        f" '{created_shift[0]['operator_name']}'"
    )
    assert created_shift[0]["shift_id"] == shift_data["shift_id"], (
        f"Expected shift_id to be '{shift_data['shift_id']}', but got"
        f" '{created_shift[0]['shift_id']}'"
    )


@patch("ska_oso_slt_services.services.shift_service.ShiftService.get_media")
def test_get_shift_log_comment_image(mock_shift_comment_image):

    shift_data = [
        {
            "file_key": "4164416f58f6daaddb7c8a2bbad3897844ba7ab3b898ac"
            "53284f533d34e0b5f6.jpeg",
            "media_content": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxIQEh"
            "UQEBIVFRUVFRcVFRUXFRUVGBgXFRUWFhgVFRUYHSggGBolGxUYITIhJSkrLi"
            "4uFx8zODMtNygtLisBCgoKDg0OGBAQGi0fHx8tLS0tLS0tLS0tLS0tLS0tLS0"
            "tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLf/AABEIAOAA4QMBIgAC"
            "EQEDEQH/xAAbAAABBQEBAAAAAAAAAAAAAAADAAECBAUGB//EAD0QAAEDAgQEA"
            "wcDAwMCBwAAAAEAAhEDIQQSMUEFUWFxBiKBE5GhscHR8DJC4RQjUgcVYpLxM1"
            "NUcoKTov/EABkBAQEBAQEBAAAAAAAAAAAAAAABAgMEBf/EAB8RAQEBAQACAgMB"
            "AAAAAAAAAAABEQISITFBE1FhA//aAAwDAQACEQMRAD8AohqWVGyp8i+Vj0A5Us"
            "qNkSyJgBlSyo+RNlTAHKnyouRPlTFCDU+VFDU4amAYapBqIGpw1MAw1SDUQNUg"
            "1MMQDUQNThqmAmGGAUgE4CkAmCMJQpQnhXEQhNCJCUKgRCiQjZVEtTAAtQy1WS"
            "1QLVcFZzUJzVac1Cc1BXyp0TKnQFyp8qLlSypi4FlSyomVKFMAoSyouVNlTALK"
            "nyouVLKrihhqkGqYapBqYIBqkGogYpBiuAYanDUUMT5UwDDU+VEyp4TBABOApwk"
            "ApiIwlCnCeFcEMqWVThPCYB5VEtRsqYtTDAC1QLVYIUCFcMVi1Dc1WnNQnNUMV8"
            "qSLlSRBsqWVThPCuNBFqbKiwllTAPKllRcqfKmAWVLKi5UoTAMNUg1TATgKiIap"
            "AKQCcNTBGE4CmGp8quCEJ4UgE8KYIQnAU4TwmCEJ4UoShMEYSU4ShMEITEIiZXAM"
            "tUC1GITEJgruahuarJahuCgrwkiwkgJCaEXKllVwChKETKnypgGGp8qJCeEA8qWV"
            "EhPCAYanDVOE8KiIanAUgFIBFRDU8KcJQghCUKcJQgjCUKUJ4REITwpJQgjCUKUJ"
            "4QQhNCnCUIBwmIRCFGEAyENzUchQcEAcqSJCSYJwlClCaEVGEymoqIUJ0ydA6SaUp",
            "content_type": "image/jpeg",
        }
    ]

    mock_shift_comment_image.return_value = shift_data

    # Send a POST request to the endpoint
    response = client.get(f"{API_PREFIX}/shift_log_comments/download_images/3")

    # Assertions
    assert (
        response.status_code == 200
    ), f"Expected status code 200, but got {response.status_code}"
