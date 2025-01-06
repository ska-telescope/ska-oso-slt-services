from unittest.mock import Mock, patch

import pytest

from ska_oso_slt_services.domain.shift_models import Shift, ShiftAnnotation
from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService


class TestShiftService:
    @patch(
        "ska_oso_slt_services.services."
        "shift_service.ShiftService._prepare_entity_with_metadata"
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

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.get_shift(shift_id)

        # Assert
        assert isinstance(result, Mock)  # Since we're using a Mock object
        assert result.id == shift_id
        mock_get_shift.assert_called_once_with(shift_id)

    @patch(
        "ska_oso_slt_services.services.shift_service."
        "ShiftService._prepare_entity_with_metadata"
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
    @patch(
        "ska_oso_slt_services.services."
        "shift_service.ShiftService.merge_shift_annotations"
    )
    def test_get_shifts_successful(
        self,
        mock_merge_comments,
        mock_get_shifts,
        mock_merge_shift_comments,
        mock_merge_shift_annotations,
        mock_prepare_metadata,
    ):
        # Arrange
        mock_shifts = [
            {
                "id": "shift-123",
                "comments": [{"id": "comment1", "comment": "Test comment"}],
                "annotations": [{"id": "annotation1", "annotation": "Test annotation"}],
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
                "annotations": [{"id": "annotation1", "annotation": "Test annotation"}],
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
        mock_merge_shift_annotations.return_value = mock_shifts

        mock_shift_obj1 = Mock(spec=Shift)
        mock_shift_obj1.id = "shift-123"
        mock_shift_obj1.shift_logs = [Mock(comments=[])]
        mock_shift_obj1.comments = []
        mock_shift_obj1.annotations = []

        mock_shift_obj2 = Mock(spec=Shift)
        mock_shift_obj2.id = "shift-124"
        mock_shift_obj2.shift_logs = [Mock(comments=[])]
        mock_shift_obj2.comments = []
        mock_shift_obj2.annotations = []

        # Define test parameters
        params = {"status": "equals"}

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        results = shift_service.get_shifts(**params)
        # Assert
        assert isinstance(results, list)
        assert len(results) == 2
        assert all(isinstance(result, Mock) for result in results)

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

    @patch("ska_oso_slt_services.services.base_repository_service.get_latest_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_entity_metadata"
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
        mock_get_entity_metadata,
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.shift_id = "test-shift"
        mock_shift_data.shift_operator = "John Doe"
        mock_shift_data.shift_start = "2024-01-01T08:00:00"
        mock_shift_data.shift_end = None
        mock_shift_data.annotations = []
        mock_shift_data.shift_logs = []
        mock_shift_data.comments = []

        mock_get_entity_metadata.return_value = {
            "created_by": "test",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_by": "test",
        }
        # Mock the return value for get_shift
        mock_get_shift.return_value = mock_shift_data

        # Mock the return value for update_metadata
        mock_metadata_shift = Mock(spec=Shift)
        mock_metadata_shift.shift_id = "test-shift"
        mock_latest_metadata.return_value = mock_metadata_shift
        mock_update_metadata.return_value = mock_metadata_shift

        # Mock the return value for update_shift
        mock_update_shift.return_value = mock_metadata_shift

        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        result = shift_service.update_shift(
            shift_id="test-shift", shift_data=mock_shift_data
        )

        # Assert
        assert isinstance(result, Mock)
        assert result.shift_id == "test-shift"

        # Verify method calls
        mock_get_shift.assert_called_once_with(shift_id=mock_shift_data.shift_id)


class TestCreateShiftAnnotations:

    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.insert_entity")
    def test_create_shift_annotations_successful(self, mock_insert_shift_to_database):
        # Arrange

        mock_shift_annotations = ShiftAnnotation(id=1, annotation="Annotation 1")

        # Act
        mock_insert_shift_to_database.return_value = {"id": 10}
        repository = PostgresShiftRepository()

        # Mock get_shift to return our test shift
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        repository.get_shift = Mock(return_value=test_shift)
        result = repository.create_shift_annotation(mock_shift_annotations)

        # Assert
        assert result.id == 10

    @patch("ska_oso_slt_services.services.base_repository_service.get_latest_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_entity_metadata"
    )
    @patch("ska_oso_slt_services.services.shift_service.update_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.update_shift"
    )
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.insert_entity")
    def test_create_annotations(
        self,
        mock_insert_shift_to_database,
        mock_get_shift,
        mock_update_shift,
        mock_update_metadata,
        mock_latest_metadata,
        mock_get_entity_metadata,
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.id = "test-shift"
        mock_shift_data.shift_operator = "test-operator"
        mock_insert_shift_to_database.return_value = {"id": 10}
        mock_get_entity_metadata.return_value = {
            "created_by": "test",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_by": "test",
        }
        # Mock the return value for get_shift
        mock_get_shift.return_value = mock_shift_data

        # Mock the return value for update_metadata
        mock_metadata_shift = Mock(spec=Shift)
        mock_metadata_shift.shift_id = "test-shift"
        mock_latest_metadata.return_value = mock_metadata_shift
        mock_update_metadata.return_value = mock_metadata_shift

        # Mock the return value for update_shift
        mock_update_shift.return_value = mock_metadata_shift
        mock_shift_annotations = ShiftAnnotation(
            id=1, shift_id="1-test", annotation="Annotation 1"
        )
        # Act
        shift_service = ShiftService([PostgresShiftRepository])
        shift_service.crud_shift_repository.create_shift_annotation
        result = shift_service.create_shift_annotation(mock_shift_annotations)

        # Assert
        assert result.id == 10

    @patch("ska_oso_slt_services.services.base_repository_service.get_latest_metadata")
    @patch(
        "ska_oso_slt_services.repository."
        "postgres_shift_repository.PostgresShiftRepository.get_entity_metadata"
    )
    @patch(
        "ska_oso_slt_services.services.base_repository_service."
        "BaseRepositoryService._prepare_entity_with_metadata"
    )
    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.get_entity")
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.insert_entity")
    def test_get_shift_annotation(
        self,
        mock_insert_shift_to_database,
        mock_get_shift,
        get_annotation,
        mock_entity_metadata,
        mock_latest_metadata,
        mock_get_entity_metadata,
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.id = "test-shift"
        mock_shift_data.shift_operator = "test-operator"
        mock_insert_shift_to_database.return_value = {"id": 10}
        mock_get_entity_metadata.return_value = {
            "created_by": "test",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_by": "test",
        }
        # Mock the return value for get_shift
        mock_get_shift.return_value = mock_shift_data

        # Mock the return value for update_metadata
        mock_annotatios = Mock(spec=ShiftAnnotation)
        mock_annotatios.id = "10"
        # Mock the return value for update_shift
        get_annotation.return_value = mock_annotatios
        mock_shift_annotations = ShiftAnnotation(
            id=1, shift_id="1-test", annotation="Annotation 1"
        )
        # Act
        mock_entity_metadata.return_value = mock_shift_annotations
        shift_service = ShiftService([PostgresShiftRepository])

        shift_service.crud_shift_repository.create_shift_annotation
        result = shift_service.get_shift_annotation(annotation_id=10)

        # Assert
        assert result.id == 1

    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.get_entities")
    def test_get_shift_annotations(
        self,
        mock_entity_metadata,
    ):
        # Arrange
        mock_shift_data = Mock(spec=Shift)
        mock_shift_data.id = "test-shift"
        mock_shift_data.shift_operator = "test-operator"

        # Mock the return value for get_shift

        # Mock the return value for update_metadata
        # Mock the return value for update_shift
        mock_shift_annotations = {
            "id": 1,
            "shift_id": "1-test",
            "annotation": "Annotation 1",
            "created_by": "test",
            "last_modified_by": "test",
            "created_on": "2024-11-11T15:46:12.378390Z",
            "last_modified_on": "2024-11-11T15:46:12.378390Z",
        }
        # Act
        mock_entity_metadata.return_value = [mock_shift_annotations]
        shift_service = ShiftService([PostgresShiftRepository])

        shift_service.crud_shift_repository.create_shift_annotation
        result = shift_service.get_shift_annotations(shift_id="1-test")

        # Assert
        assert result[0].id == 1

    @patch("ska_oso_slt_services.data_access.postgres.shift_crud.DBCrud.insert_entity")
    def test_error_to_create_shift_annotations(self, mock_insert_shift_to_database):
        # Arrange
        mock_shift_annotations = ShiftAnnotation(id=1, annotation="Annotation 1")

        # Act
        mock_insert_shift_to_database.return_value = {"id": 10}
        repository = PostgresShiftRepository()

        # Mock get_shift to return our test shift
        test_shift = Shift(
            shift="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        repository.get_shift = Mock(return_value=test_shift)
        result = repository.create_shift_annotation(mock_shift_annotations)

        # Assert
        assert result.id == 10

    def test_get_shift_annotations_successful(self):
        # Arrange
        mock_shift_annotations = {"id": 1, "annotation": "Annotation 1"}
        # Act
        repository = PostgresShiftRepository()
        # Mock dependencies
        repository.postgres_data_access = Mock()
        repository.crud.get_entities = Mock(return_value=[mock_shift_annotations])

        # Mock get_shift to return our test shift
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        repository.get_shift = Mock(return_value=test_shift)
        result = repository.get_shift_annotations(1)
        # Assert
        assert result[0]["annotation"] == "Annotation 1"
