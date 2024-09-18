from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from ska_oso_slt_services import create_app  # Import your create_app function

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


def test_create_shift():
    # Prepare test data with metadata
    current_time = datetime.now(timezone.utc)
    shift_data = {
        "shift_operator": "test",
        "metadata": {
            "created_by": "DefaultUser",
            "created_on": current_time.isoformat(),
            "last_modified_by": "DefaultUser",
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

    # Patch both database access and Shift model creation
    with (
        patch(
            "ska_oso_slt_services.data_access"
            ".postgres_data_acess.PostgresDataAccess.insert"
        ) as mock_insert,
        patch(
            "ska_oso_slt_services.services.shift_service.Shift", return_value=mock_shift
        ),
    ):

        # Send a POST request to the endpoint
        response = client.post(
            "/ska-oso-slt-services/slt/api/v0/shift/shifts/create", json=shift_data
        )

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


def test_get_shift():
    # Mock shift data
    mock_shift = {
        "shift_id": "test-id",
        "shift_start": datetime.now(tz=timezone.utc),
        "shift_end": datetime.now(tz=timezone.utc),
        "shift_operator": "test",
        "shift_logs": [
            {"info": {}, "source": "test", "log_time": datetime.now(tz=timezone.utc)}
        ],
        "media": [{"type": "test", "path": "test"}],
        "annotations": "test",
        "comments": "test",
        "created_by": "test",
        "created_on": datetime.now(tz=timezone.utc),
        "last_modified_by": "test",
        "last_modified_on": datetime.now(tz=timezone.utc),
    }

    # Create a mock for the database session
    mock_db_session = MagicMock()

    # Set up the mock to return our mock_shift when queried
    mock_db_session.return_value = mock_shift

    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.data_access"
        ".postgres_data_acess.PostgresDataAccess.get_one",
        return_value=mock_shift,
    ):
        # Send a GET request to the endpoint
        response = client.get("/ska-oso-slt-services/slt/api/v0/shift/shift")

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response content
    retrieved_shift = response.json()
    assert retrieved_shift[0]["shift_id"] == "test-id"

    # Optionally, you can assert that the get method was called
    # This depends on how your actual implementation works
    # mock_db_session.get.assert_called_once()


def test_get_shifts():
    # Mock shifts data
    mock_shifts = [
        {
            "shift_id": "test-id-1",
            "shift_start": datetime.now(tz=timezone.utc),
            "shift_end": datetime.now(tz=timezone.utc),
            "shift_operator": "test-operator-1",
            "shift_logs": [
                {
                    "info": {},
                    "source": "test",
                    "log_time": datetime.now(tz=timezone.utc),
                }
            ],
            "media": [{"type": "test", "path": "test"}],
            "annotations": "test-annotation-1",
            "comments": "test-comment-1",
            "created_by": "test-user-1",
            "created_on": datetime.now(tz=timezone.utc),
            "last_modified_by": "test-user-1",
            "last_modified_on": datetime.now(tz=timezone.utc),
        },
        {
            "shift_id": "test-id-2",
            "shift_start": datetime.now(tz=timezone.utc),
            "shift_end": datetime.now(tz=timezone.utc),
            "shift_operator": "test-operator-2",
            "shift_logs": [],
            "media": [],
            "annotations": "test-annotation-2",
            "comments": "test-comment-2",
            "created_by": "test-user-2",
            "created_on": datetime.now(tz=timezone.utc),
            "last_modified_by": "test-user-2",
            "last_modified_on": datetime.now(tz=timezone.utc),
        },
    ]

    # Create a mock for the database session
    mock_db_session = MagicMock()

    # Set up the mock to return our mock_shifts when queried
    mock_db_session.return_value = mock_shifts

    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.data_access.postgres_data_acess.PostgresDataAccess.get",
        return_value=mock_shifts,
    ):
        # Send a GET request to the endpoint
        response = client.get("/ska-oso-slt-services/slt/api/v0/shift/shifts")

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response content
    retrieved_shifts = response.json()
    assert len(retrieved_shifts) == 2
    assert retrieved_shifts[0][0]["shift_id"] == "test-id-1"
    assert retrieved_shifts[0][1]["shift_id"] == "test-id-2"
    assert retrieved_shifts[0][0]["shift_operator"] == "test-operator-1"
    assert retrieved_shifts[0][1]["shift_operator"] == "test-operator-2"


def test_update_shift():
    # Existing shift data
    existing_shift = {
        "shift_id": "test-id-1",
        "shift_start": datetime.now(tz=timezone.utc),
        "shift_end": None,
        "shift_operator": "old-operator",
        "shift_logs": [],
        "media": [],
        "annotations": "old-annotation",
        "comments": "old-comment",
        "created_by": "test-user-1",
        "created_on": datetime.now(tz=timezone.utc),
        "last_modified_by": "test-user-1",
        "last_modified_on": datetime.now(tz=timezone.utc),
    }

    # Updated shift data
    update_data = {
        "shift_id": "test-id-1",
        "shift_start": "2024-09-14T16:49:54.889Z",
        "shift_operator": "old-operator",
        "shift_logs": [],
        "media": [],
        "annotations": "old-annotation",
        "comments": "old-comment",
        "metadata": {
            "created_by": "test-user-1",
            "created_on": "2024-09-14T16:49:54.889Z",
            "last_modified_by": "test-user-1",
            "last_modified_on": "2024-09-14T16:49:54.889Z",
        },
    }

    # Create a mock for the database session
    mock_db_session = MagicMock()

    # Set up the mock to return the existing shift when queried
    mock_db_session.get.return_value = existing_shift

    # Set up the mock to return the updated shift after update
    updated_shift = {**existing_shift, **update_data}
    mock_db_session.update.return_value = updated_shift

    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.data_access."
        "postgres_data_acess.PostgresDataAccess.get_one",
        return_value=existing_shift,
    ):
        with patch(
            "ska_oso_slt_services.data_access.postgres_data_acess"
            ".PostgresDataAccess.update",
            return_value=updated_shift,
        ):
            # Send a PUT request to the endpoint
            response = client.put(
                "/ska-oso-slt-services/slt/api/v0/shift/shifts/update",
                json=update_data,
            )

    # Assert the response status code
    assert response.status_code == 200

    # Assert the response content
    updated_shift_response = response.json()
    assert updated_shift_response[0]["shift_id"] == existing_shift["shift_id"]
    assert updated_shift_response[0]["shift_operator"] == update_data["shift_operator"]
    assert updated_shift_response[0]["annotations"] == update_data["annotations"]


# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


def test_patch_shift():
    # Existing shift data
    existing_shift = {
        "shift_id": "test-id-1",
        "shift_start": "2024-09-14T16:49:54.889Z",
        "shift_operator": "old-operator",
        "shift_logs": [],
        "media": [],
        "annotations": "old-annotation",
        "comments": "old-comment",
        "metadata": {
            "created_by": "test-user-1",
            "created_on": "2024-09-14T16:49:54.889Z",
            "last_modified_by": "test-user-1",
            "last_modified_on": "2024-09-14T16:49:54.889Z",
        },
    }

    # Patch data (only updating a subset of fields)
    patch_data = {
        "shift_id": "test-id-1",
        "shift_operator": "new-operator",
        "annotations": "new-annotation",
    }

    # Create a mock for the database session
    mock_db_session = MagicMock()

    # Set up the mock to return the existing shift when queried
    mock_db_session.get_one.return_value = existing_shift

    # Set up the mock to return the patched shift after update
    patched_shift = {**existing_shift, **patch_data}
    mock_db_session.update.return_value = patched_shift

    # Patch the database session to use our mock
    with patch(
        "ska_oso_slt_services.data_access."
        "postgres_data_acess.PostgresDataAccess.get_one",
        return_value=existing_shift,
    ):
        with patch(
            "ska_oso_slt_services.data_access.postgres_data_acess."
            "PostgresDataAccess.update",
            return_value=patched_shift,
        ):
            # Send a PATCH request to the endpoint
            response = client.patch(
                "/ska-oso-slt-services/slt/api/v0/shift/shifts/patch/test-id-1",
                json=patch_data,
            )

    # Assert the response status code
    assert response.status_code == 422
