from unittest.mock import Mock

import pytest

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.domain.shift_models import Shift
from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService


class TestShiftService:
    @pytest.fixture
    def shift_service(self):
        service = ShiftService([PostgresShiftRepository])
        service.postgres_repository = Mock()
        service.merge_comments = Mock()
        service.merge_shift_comments = Mock()
        service._prepare_shift_with_metadata = Mock()
        service._prepare_shift_comment_with_metadata = Mock()
        service._prepare_shift_log_comment_with_metadata = Mock()
        return service

    def test_get_shift_successful(self, shift_service):
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

        # Set up mock returns
        shift_service.postgres_repository.get_shift.return_value = mock_shift
        shift_service.merge_comments.return_value = [mock_shift]
        shift_service.merge_shift_comments.return_value = [mock_shift]

        mock_shift_obj = Mock(spec=Shift)
        mock_shift_obj.id = shift_id
        mock_shift_obj.shift_logs = [Mock(comments=[])]
        mock_shift_obj.comments = []

        shift_service._prepare_shift_with_metadata.return_value = mock_shift_obj
        shift_service._prepare_shift_comment_with_metadata.return_value = {
            "id": "comment1"
        }
        shift_service._prepare_shift_log_comment_with_metadata.return_value = {
            "id": "log_comment1"
        }

        # Act
        result = shift_service.get_shift(shift_id)

        # Assert
        assert isinstance(result, Mock)  # Since we're using a Mock object
        assert result.id == shift_id
        shift_service.postgres_repository.get_shift.assert_called_once_with(shift_id)

    def test_get_shift_not_found(self, shift_service):
        # Arrange
        shift_id = "non-existent-shift"
        shift_service.postgres_repository.get_shift.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            shift_service.get_shift(shift_id)
        assert str(exc_info.value) == f"404: No shift found with ID: {shift_id}"

    def test_get_shift_without_comments(self, shift_service):
        # Arrange
        shift_id = "test-shift-123"
        mock_shift = {"id": shift_id, "shift_logs": []}

        shift_service.postgres_repository.get_shift.return_value = mock_shift
        shift_service.merge_comments.return_value = [mock_shift]
        shift_service.merge_shift_comments.return_value = [mock_shift]

        mock_shift_obj = Mock(spec=Shift)
        mock_shift_obj.id = shift_id
        mock_shift_obj.comments = []
        mock_shift_obj.shift_logs = []

        shift_service._prepare_shift_with_metadata.return_value = mock_shift_obj

        # Act
        result = shift_service.get_shift(shift_id)

        # Assert
        assert isinstance(result, Mock)
        assert result.id == shift_id
        assert result.comments == []

    def test_get_shift_without_shift_logs(self, shift_service):
        # Arrange
        shift_id = "test-shift-123"
        mock_shift = {
            "id": shift_id,
            "comments": [{"id": "comment1", "comment": "Test comment"}],
        }

        shift_service.postgres_repository.get_shift.return_value = mock_shift
        shift_service.merge_comments.return_value = [mock_shift]
        shift_service.merge_shift_comments.return_value = [mock_shift]

        mock_shift_obj = Mock(spec=Shift)
        mock_shift_obj.id = shift_id
        mock_shift_obj.comments = []
        mock_shift_obj.shift_logs = None

        shift_service._prepare_shift_with_metadata.return_value = mock_shift_obj
        shift_service._prepare_shift_comment_with_metadata.return_value = {
            "id": "comment1"
        }

        # Act
        result = shift_service.get_shift(shift_id)

        # Assert
        assert isinstance(result, Mock)
        assert result.id == shift_id
        assert hasattr(result, "comments")

    def test_get_shifts_successful(self, shift_service):
        # Arrange
        mock_shifts = [
            {
                "id": "shift-1",
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
            {"id": "shift-2", "comments": [], "shift_logs": []},
        ]

        shift_service.postgres_repository.get_shifts.return_value = mock_shifts

        # Mock the merge methods to return the same shift
        shift_service.merge_comments.side_effect = lambda x: x
        shift_service.merge_shift_comments.side_effect = lambda x: x

        # Create mock Shift objects for return values
        mock_shift_objs = []
        for shift in mock_shifts:
            mock_shift_obj = Mock(spec=Shift)
            mock_shift_obj.id = shift["id"]
            mock_shift_obj.comments = []
            mock_shift_obj.shift_logs = (
                [Mock(comments=[])] if shift.get("shift_logs") else []
            )
            mock_shift_objs.append(mock_shift_obj)

        shift_service._prepare_shift_with_metadata.side_effect = mock_shift_objs
        shift_service._prepare_shift_comment_with_metadata.return_value = {
            "id": "comment1"
        }
        shift_service._prepare_shift_log_comment_with_metadata.return_value = {
            "id": "log_comment1"
        }

        # Act
        result = shift_service.get_shifts(
            shift=Mock(spec=Shift),
            match_type="exact",  # Use string value instead of enum
            status="active",  # Use string value instead of enum
        )

        # Assert
        assert len(result) == 2
        assert isinstance(result[0], Mock)
        assert result[0].id == "shift-1"
        assert isinstance(result[1], Mock)
        assert result[1].id == "shift-2"
        shift_service.postgres_repository.get_shifts.assert_called_once()

    def test_get_shifts_with_no_results(self, shift_service):
        # Arrange
        shift_service.postgres_repository.get_shifts.return_value = []

        # Act & Assert
        with pytest.raises(NotFoundError) as exc_info:
            shift_service.get_shifts()
        assert str(exc_info.value) == "404: No shifts found for the given query."

    @pytest.fixture
    def service_mock(self):
        # Create a mock postgres repository
        postgres_repository = Mock()

        # Create the shift service instance
        from ska_oso_slt_services.services.shift_service import ShiftService

        service = ShiftService([PostgresShiftRepository])
        # Set the postgres_repository attribute directly
        service.postgres_repository = postgres_repository
        return service

    def test_merge_comments_empty_shifts(self, service_mock):
        """Test merging comments with empty shifts list"""
        # Arrange
        shifts = []

        # Act
        result = service_mock.merge_comments(shifts)

        # Assert
        assert result == []
        assert service_mock.postgres_repository.get_shift_logs_comments.call_count == 0

    def test_merge_comments_no_shift_logs(self, service_mock):
        """Test merging comments when shifts have no shift_logs"""
        # Arrange
        shifts = [{"shift_id": "123", "other_data": "value"}]

        # Act
        result = service_mock.merge_comments(shifts)

        # Assert
        assert result == shifts
        assert service_mock.postgres_repository.get_shift_logs_comments.call_count == 1
        service_mock.postgres_repository.get_shift_logs_comments.assert_called_with(
            shift_id="123"
        )

    def test_merge_comments_with_matching_comments(self, service_mock):
        """Test merging comments with matching eb_ids"""
        # Arrange
        shifts = [
            {
                "shift_id": "123",
                "shift_logs": [
                    {"info": {"eb_id": "eb1"}, "data": "log1"},
                    {"info": {"eb_id": "eb2"}, "data": "log2"},
                ],
            }
        ]

        comments = [
            {"eb_id": "eb1", "comment": "Comment 1"},
            {"eb_id": "eb2", "comment": "Comment 2"},
            {"eb_id": "eb3", "comment": "Comment 3"},
        ]

        service_mock.postgres_repository.get_shift_logs_comments.return_value = comments

        # Act
        result = service_mock.merge_comments(shifts)

        # Assert
        assert len(result) == 1
        assert len(result[0]["shift_logs"]) == 2
        assert result[0]["shift_logs"][0]["comments"] == [
            {"eb_id": "eb1", "comment": "Comment 1"}
        ]
        assert result[0]["shift_logs"][1]["comments"] == [
            {"eb_id": "eb2", "comment": "Comment 2"}
        ]

    def test_merge_comments_no_matching_comments(self, service_mock):
        """Test merging comments when there are no matching eb_ids"""
        # Arrange
        shifts = [
            {
                "shift_id": "123",
                "shift_logs": [{"info": {"eb_id": "eb1"}, "data": "log1"}],
            }
        ]

        comments = [
            {"eb_id": "eb2", "comment": "Comment 2"},
            {"eb_id": "eb3", "comment": "Comment 3"},
        ]

        service_mock.postgres_repository.get_shift_logs_comments.return_value = comments

        # Act
        result = service_mock.merge_comments(shifts)

        # Assert
        assert len(result) == 1
        assert len(result[0]["shift_logs"]) == 1
        assert result[0]["shift_logs"][0]["comments"] == []

    def test_merge_comments_multiple_shifts(self, service_mock):
        """Test merging comments for multiple shifts"""
        # Arrange
        shifts = [
            {
                "shift_id": "123",
                "shift_logs": [{"info": {"eb_id": "eb1"}, "data": "log1"}],
            },
            {
                "shift_id": "456",
                "shift_logs": [{"info": {"eb_id": "eb2"}, "data": "log2"}],
            },
        ]

        def get_comments(shift_id):
            comments_map = {
                "123": [{"eb_id": "eb1", "comment": "Comment 1"}],
                "456": [{"eb_id": "eb2", "comment": "Comment 2"}],
            }
            return comments_map.get(shift_id, [])

        service_mock.postgres_repository.get_shift_logs_comments.side_effect = (
            get_comments
        )

        # Act
        result = service_mock.merge_comments(shifts)

        # Assert
        assert len(result) == 2
        assert result[0]["shift_logs"][0]["comments"] == [
            {"eb_id": "eb1", "comment": "Comment 1"}
        ]
        assert result[1]["shift_logs"][0]["comments"] == [
            {"eb_id": "eb2", "comment": "Comment 2"}
        ]
        assert service_mock.postgres_repository.get_shift_logs_comments.call_count == 2

    def test_merge_shift_comments_empty_shifts(self, service_mock):
        """Test merging shift comments with empty shifts list"""
        # Arrange
        shifts = []

        # Act
        result = service_mock.merge_shift_comments(shifts)

        # Assert
        assert result == []
        assert service_mock.postgres_repository.get_shift_comments.call_count == 0

    def test_merge_shift_comments_single_shift(self, service_mock):
        """Test merging comments for a single shift"""
        # Arrange
        shifts = [{"shift_id": "123", "other_data": "value"}]
        comments = [
            {"comment_id": "1", "comment": "Comment 1"},
            {"comment_id": "2", "comment": "Comment 2"},
        ]
        service_mock.postgres_repository.get_shift_comments.return_value = comments

        # Act
        result = service_mock.merge_shift_comments(shifts)

        # Assert
        assert len(result) == 1
        assert result[0]["comments"] == comments
        assert result[0]["shift_id"] == "123"
        assert result[0]["other_data"] == "value"
        service_mock.postgres_repository.get_shift_comments.assert_called_once_with(
            shift_id="123"
        )

    def test_merge_shift_comments_multiple_shifts(self, service_mock):
        """Test merging comments for multiple shifts"""
        # Arrange
        shifts = [
            {"shift_id": "123", "data": "shift1"},
            {"shift_id": "456", "data": "shift2"},
        ]

        def get_comments(shift_id):
            comments_map = {
                "123": [{"comment_id": "1", "comment": "Comment 1"}],
                "456": [{"comment_id": "2", "comment": "Comment 2"}],
            }
            return comments_map.get(shift_id, [])

        service_mock.postgres_repository.get_shift_comments.side_effect = get_comments

        # Act
        result = service_mock.merge_shift_comments(shifts)

        # Assert
        assert len(result) == 2
        assert result[0]["comments"] == [{"comment_id": "1", "comment": "Comment 1"}]
        assert result[1]["comments"] == [{"comment_id": "2", "comment": "Comment 2"}]
        assert service_mock.postgres_repository.get_shift_comments.call_count == 2
        service_mock.postgres_repository.get_shift_comments.assert_any_call(
            shift_id="123"
        )
        service_mock.postgres_repository.get_shift_comments.assert_any_call(
            shift_id="456"
        )

    def test_merge_shift_comments_no_comments(self, service_mock):
        """Test merging when there are no comments for a shift"""
        # Arrange
        shifts = [{"shift_id": "123", "data": "shift1"}]
        service_mock.postgres_repository.get_shift_comments.return_value = []

        # Act
        result = service_mock.merge_shift_comments(shifts)

        # Assert
        assert len(result) == 1
        assert result[0]["comments"] == []
        assert result[0]["shift_id"] == "123"
        assert result[0]["data"] == "shift1"
        service_mock.postgres_repository.get_shift_comments.assert_called_once_with(
            shift_id="123"
        )

    def test_merge_shift_comments_preserves_existing_data(self, service_mock):
        """Test that merging comments preserves all existing shift data"""
        # Arrange
        shifts = [
            {
                "shift_id": "123",
                "data": "shift1",
                "additional_field": "value",
                "nested": {"key": "value"},
            }
        ]
        comments = [{"comment_id": "1", "text": "Comment 1"}]
        service_mock.postgres_repository.get_shift_comments.return_value = comments

        # Act
        result = service_mock.merge_shift_comments(shifts)

        # Assert
        assert len(result) == 1
        assert result[0]["comments"] == comments
        assert result[0]["shift_id"] == "123"
        assert result[0]["data"] == "shift1"
        assert result[0]["additional_field"] == "value"
        assert result[0]["nested"] == {"key": "value"}
        service_mock.postgres_repository.get_shift_comments.assert_called_once_with(
            shift_id="123"
        )
