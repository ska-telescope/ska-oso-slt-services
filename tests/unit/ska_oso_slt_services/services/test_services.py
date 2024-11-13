from unittest.mock import Mock

import pytest

from ska_oso_slt_services.repository.postgress_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService


@pytest.fixture
def shift_service():
    return ShiftService([PostgresShiftRepository])


def test_validate_postgres_repository_when_repository_is_none(shift_service):
    # Arrange
    shift_service.postgres_repository = None

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        shift_service._validate_postgres_repository()

    assert str(exc_info.value) == "PostgresShiftRepository is required"


def test_merge_comments_empty_shifts(shift_service):
    # Arrange
    shifts = []

    # Act
    result = shift_service.merge_comments(shifts)

    # Assert
    assert result == []


def test_merge_comments_no_shift_logs(shift_service):
    # Arrange
    shifts = [{"shift_id": "shift1"}]
    shift_service.postgres_repository = Mock()
    shift_service.postgres_repository.get_shift_logs_comments.return_value = []

    # Act
    result = shift_service.merge_comments(shifts)

    # Assert
    assert result == shifts
    shift_service.postgres_repository.get_shift_logs_comments.assert_called_once_with(
        shift_id="shift1"
    )


def test_merge_comments_with_matching_comments(shift_service):
    # Arrange
    shifts = [
        {
            "shift_id": "shift1",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb1"},
                },
                {
                    "info": {"eb_id": "eb2"},
                },
            ],
        }
    ]

    comments = [
        {"eb_id": "eb1", "text": "Comment 1"},
        {"eb_id": "eb2", "text": "Comment 2"},
    ]

    shift_service.postgres_repository = Mock()
    shift_service.postgres_repository.get_shift_logs_comments.return_value = comments

    # Act
    result = shift_service.merge_comments(shifts)

    # Assert
    expected_result = [
        {
            "shift_id": "shift1",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb1"},
                    "comments": [{"eb_id": "eb1", "text": "Comment 1"}],
                },
                {
                    "info": {"eb_id": "eb2"},
                    "comments": [{"eb_id": "eb2", "text": "Comment 2"}],
                },
            ],
        }
    ]

    assert result == expected_result
    shift_service.postgres_repository.get_shift_logs_comments.assert_called_once_with(
        shift_id="shift1"
    )


def test_merge_comments_with_no_matching_comments(shift_service):
    # Arrange
    shifts = [
        {
            "shift_id": "shift1",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb1"},
                }
            ],
        }
    ]

    shift_service.postgres_repository = Mock()
    shift_service.postgres_repository.get_shift_logs_comments.return_value = [
        {"eb_id": "eb2", "text": "Comment for different eb"}
    ]

    # Act
    result = shift_service.merge_comments(shifts)

    # Assert
    expected_result = [
        {
            "shift_id": "shift1",
            "shift_logs": [{"info": {"eb_id": "eb1"}, "comments": []}],
        }
    ]

    assert result == expected_result
    shift_service.postgres_repository.get_shift_logs_comments.assert_called_once_with(
        shift_id="shift1"
    )


def test_merge_comments_multiple_shifts(shift_service):
    # Arrange
    shifts = [
        {
            "shift_id": "shift1",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb1"},
                }
            ],
        },
        {
            "shift_id": "shift2",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb2"},
                }
            ],
        },
    ]

    shift_service.postgres_repository = Mock()
    shift_service.postgres_repository.get_shift_logs_comments.side_effect = [
        [{"eb_id": "eb1", "text": "Comment 1"}],
        [{"eb_id": "eb2", "text": "Comment 2"}],
    ]

    # Act
    result = shift_service.merge_comments(shifts)

    # Assert
    expected_result = [
        {
            "shift_id": "shift1",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb1"},
                    "comments": [{"eb_id": "eb1", "text": "Comment 1"}],
                }
            ],
        },
        {
            "shift_id": "shift2",
            "shift_logs": [
                {
                    "info": {"eb_id": "eb2"},
                    "comments": [{"eb_id": "eb2", "text": "Comment 2"}],
                }
            ],
        },
    ]

    assert result == expected_result
    assert shift_service.postgres_repository.get_shift_logs_comments.call_count == 2
    shift_service.postgres_repository.get_shift_logs_comments.assert_any_call(
        shift_id="shift1"
    )
    shift_service.postgres_repository.get_shift_logs_comments.assert_any_call(
        shift_id="shift2"
    )


def test_merge_shift_comments_empty_shifts(shift_service):
    # Arrange
    shifts = []

    # Act
    result = shift_service.merge_shift_comments(shifts)

    # Assert
    assert result == []
    assert isinstance(result, list)
