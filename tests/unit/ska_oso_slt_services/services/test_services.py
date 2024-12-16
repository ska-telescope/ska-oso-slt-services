from unittest.mock import Mock, patch

import pytest

from ska_oso_slt_services.domain.shift_models import Shift
from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService


class TestShiftService:
    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_shift_log_comment_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_shift_comment_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services."
        "shift_service.ShiftService._prepare_shift_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services."
        "shift_service.ShiftService.merge_shift_comments"
    )
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_shift"
    )
    @patch("ska_oso_slt_services.services." "shift_service.ShiftService.merge_comments")
    def test_get_shift_successful(
        self,
        mock_merge_comments,
        mock_get_shift,
        mock_merge_shift_comments,
        mock_prepare_metadata,
        prepare_comment,
        mock_log,
    ):
        # Arrange
        shift_id = "test-shift-123"
        mock_shift = {
            "id": shift_id,
            "comments": [{"id": "comment1", "comment": "Test comment"}],
            "shift_logs": [
                {
                    "id": "log1",
                    "comments": [{"id": "log_comment1", "comment": "Test log comment"}],
                }
            ],
        }
        mock_merge_comments.return_value = [mock_shift]
        # # Set up mock returns
        mock_get_shift.return_value = mock_shift
        mock_merge_shift_comments.return_value = [mock_shift]

        mock_shift_obj = Mock(spec=Shift)
        mock_shift_obj.id = shift_id
        mock_shift_obj.shift_logs = [Mock(comments=[])]
        mock_shift_obj.comments = []

        mock_prepare_metadata.return_value = mock_shift_obj
        prepare_comment.return_value = {"id": "comment1"}
        (mock_log._prepare_shift_log_comment_with_metadata.return_value) = {
            "id": "log_comment1"
        }

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.get_shift(shift_id)

        # Assert
        assert isinstance(result, Mock)  # Since we're using a Mock object
        assert result.id == shift_id
        mock_get_shift.assert_called_once_with(shift_id)

    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_shift_log_comment_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_shift_comment_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_shift_with_metadata"
    )
    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService.merge_shift_comments"
    )
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_shifts"
    )
    @patch("ska_oso_slt_services.services." "shift_service.ShiftService.merge_comments")
    def test_get_shifts_successful(
        self,
        mock_merge_comments,
        mock_get_shifts,
        mock_merge_shift_comments,
        mock_prepare_metadata,
        prepare_comment,
        mock_log,
    ):
        # Arrange
        mock_shifts = [
            {
                "id": "shift-123",
                "comments": [{"id": "comment1", "comment": "Test comment"}],
                "shift_logs": [
                    {
                        "id": "log1",
                        "comments": [
                            {"id": "log_comment1", "comment": "Test log comment"}
                        ],
                    }
                ],
            },
            {
                "id": "shift-124",
                "comments": [{"id": "comment2", "comment": "Test comment 2"}],
                "shift_logs": [
                    {
                        "id": "log2",
                        "comments": [
                            {"id": "log_comment2", "comment": "Test log comment 2"}
                        ],
                    }
                ],
            },
        ]

        # Set up mock returns
        mock_merge_comments.return_value = mock_shifts
        mock_get_shifts.return_value = mock_shifts
        mock_merge_shift_comments.return_value = mock_shifts

        mock_shift_obj1 = Mock(spec=Shift)
        mock_shift_obj1.id = "shift-123"
        mock_shift_obj1.shift_logs = [Mock(comments=[])]
        mock_shift_obj1.comments = []

        mock_shift_obj2 = Mock(spec=Shift)
        mock_shift_obj2.id = "shift-124"
        mock_shift_obj2.shift_logs = [Mock(comments=[])]
        mock_shift_obj2.comments = []

        mock_prepare_metadata.side_effect = [mock_shift_obj1, mock_shift_obj2]
        prepare_comment.return_value = {"id": "comment1"}
        mock_log._prepare_shift_log_comment_with_metadata.return_value = {
            "id": "log_comment1"
        }

        # Define test parameters
        params = {"status": "equals"}

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        results = shift_service.get_shifts(**params)

        # Assert
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(result, Mock) for result in results)
        assert results[0].id == "shift-123"
        assert results[1].id == "shift-124"

    @patch("ska_oso_slt_services.services.shift_service.set_new_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.create_shift"
    )
    def test_create_shift_successful(self, mock_create_shift, mock_set_new_metadata):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.shift_id = "shift-123"
        mock_shift_data.shift_operator = "John Doe"
        mock_shift_data.shift_start = "2024-01-01T08:00:00"
        mock_shift_data.shift_end = None
        mock_shift_data.annotations = []
        mock_shift_data.shift_logs = []
        mock_shift_data.comments = []

        # Mock the return value for set_new_metadata
        mock_metadata_shift = Mock(spec=Shift)
        mock_metadata_shift.shift_id = "shift-123"
        mock_set_new_metadata.return_value = mock_metadata_shift

        # Mock the return value for create_shift
        mock_create_shift.return_value = mock_metadata_shift

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.create_shift(mock_shift_data)

        # Assert
        assert isinstance(result, Mock)
        assert result.shift_id == "shift-123"

        # Verify method calls
        mock_set_new_metadata.assert_called_once_with(
            mock_shift_data, created_by=mock_shift_data.shift_operator
        )
        mock_create_shift.assert_called_once_with(mock_metadata_shift)

    @patch("ska_oso_slt_services.services.shift_service.set_new_metadata")
    @patch(
        "ska_oso_slt_services.repository.postgres_shift_repository."
        "PostgresShiftRepository.create_shift"
    )
    def test_create_shift_with_full_data(
        self, mock_create_shift, mock_set_new_metadata
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.shift_id = "shift-123"
        mock_shift_data.shift_operator = "John Doe"
        mock_shift_data.shift_start = "2024-01-01T08:00:00"
        mock_shift_data.shift_end = "2024-01-01T16:00:00"
        mock_shift_data.annotations = ["annotation1", "annotation2"]
        mock_shift_data.shift_logs = [
            {"id": "log1", "info": {"eb_id": "eb1"}, "comments": []}
        ]
        mock_shift_data.comments = [{"id": "comment1", "text": "Test comment"}]

        # Mock the return value for set_new_metadata
        mock_metadata_shift = Mock(spec=Shift)
        mock_metadata_shift.shift_id = "shift-123"
        mock_metadata_shift.shift_operator = "John Doe"
        mock_metadata_shift.shift_start = "2024-01-01T08:00:00"
        mock_metadata_shift.shift_end = "2024-01-01T16:00:00"
        mock_metadata_shift.annotations = ["annotation1", "annotation2"]
        mock_metadata_shift.shift_logs = mock_shift_data.shift_logs
        mock_metadata_shift.comments = mock_shift_data.comments

        mock_set_new_metadata.return_value = mock_metadata_shift
        mock_create_shift.return_value = mock_metadata_shift

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.create_shift(mock_shift_data)

        # Assert
        assert isinstance(result, Mock)
        assert result.shift_id == "shift-123"
        assert result.shift_operator == "John Doe"
        assert result.shift_start == "2024-01-01T08:00:00"
        assert result.shift_end == "2024-01-01T16:00:00"
        assert len(result.annotations) == 2
        assert len(result.shift_logs) == 1
        assert len(result.comments) == 1

        # Verify method calls
        mock_set_new_metadata.assert_called_once_with(
            mock_shift_data, created_by=mock_shift_data.shift_operator
        )
        mock_create_shift.assert_called_once_with(mock_metadata_shift)

    @patch("ska_oso_slt_services.services.shift_service.set_new_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.create_shift"
    )
    def test_create_shift_handles_repository_error(
        self, mock_create_shift, mock_set_new_metadata
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.shift_id = "shift-123"
        mock_shift_data.shift_operator = "John Doe"

        mock_metadata_shift = Mock(spec=Shift)
        mock_set_new_metadata.return_value = mock_metadata_shift

        # Mock repository error
        mock_create_shift.side_effect = Exception("Database error")

        # Act & Assert
        shift_service = ShiftService([PostgresShiftRepository])
        with pytest.raises(Exception) as exc_info:
            shift_service.create_shift(mock_shift_data)

        assert "Database error" in str(exc_info.value)
        mock_create_shift.assert_called_once_with(mock_metadata_shift)

    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_latest_metadata"
    )
    @patch("ska_oso_slt_services.services.shift_service.update_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.update_shift"
    )
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    def test_update_shift_successful(
        self,
        mock_get_shift,
        mock_update_shift,
        mock_update_metadata,
        mock_latest_metadata,
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.shift_id = "XXXXXXXXX"
        mock_shift_data.shift_operator = "John Doe"
        mock_shift_data.shift_start = "2024-01-01T08:00:00"
        mock_shift_data.shift_end = None
        mock_shift_data.annotations = []
        mock_shift_data.shift_logs = []
        mock_shift_data.comments = []

        # Mock the return value for get_shift
        mock_get_shift.return_value = mock_shift_data

        # Mock the return value for update_metadata
        mock_metadata_shift = Mock(spec=Shift)
        mock_metadata_shift.shift_id = "XXXXXXXXX"
        mock_latest_metadata.return_value = mock_metadata_shift
        mock_update_metadata.return_value = mock_metadata_shift

        # Mock the return value for update_shift
        mock_update_shift.return_value = mock_metadata_shift

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.update_shift(
            shift_id="XXXXXXXXX", shift_data=mock_shift_data
        )

        # Assert
        assert isinstance(result, Mock)
        assert result.shift_id == "XXXXXXXXX"

        # Verify method calls
        mock_get_shift.assert_called_once_with(shift_id=mock_shift_data.shift_id)
