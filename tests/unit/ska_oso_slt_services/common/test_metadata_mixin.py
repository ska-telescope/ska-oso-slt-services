from dataclasses import dataclass
from typing import Optional
from unittest.mock import patch

import pytest

# Assuming these are your imports - adjust according to your actual implementation
from ska_oso_slt_services.common.metadata_mixin import (
    Metadata,
    set_new_metadata,
    update_metadata,
)
from ska_oso_slt_services.common.utils import get_datetime_for_timezone

current_time = get_datetime_for_timezone("UTC")


# Mock entity class for testing
@dataclass
class MockEntity:
    metadata: Optional[Metadata] = None


# Fixture for datetime
@pytest.fixture
def mock_utc_now():
    return current_time


# Fixtures for common test data
@pytest.fixture
def mock_metadata():
    return Metadata(
        created_on=current_time,
        created_by="original_user",
        last_modified_on=current_time,
        last_modified_by="original_user",
    )


@pytest.fixture
def mock_entity():
    return MockEntity()


# Tests for update_metadata function
class TestUpdateMetadata:
    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_update_metadata_with_last_modified_by(
        self, mock_datetime, mock_entity, mock_metadata, mock_utc_now
    ):
        # Arrange
        mock_datetime.return_value = mock_utc_now
        last_modified_by = "original_user"

        # Act
        result = update_metadata(mock_entity, mock_metadata)
        # Assert
        assert result.metadata.created_by == mock_metadata.created_by
        assert result.metadata.last_modified_on == mock_utc_now
        assert result.metadata.last_modified_by == last_modified_by

    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_update_metadata_without_last_modified_by(
        self, mock_datetime, mock_entity, mock_metadata, mock_utc_now
    ):
        # Arrange
        mock_datetime.return_value = mock_utc_now

        # Act
        result = update_metadata(mock_entity, mock_metadata)

        # Assert
        assert result.metadata.created_by == mock_metadata.created_by
        assert result.metadata.last_modified_on == mock_utc_now
        assert result.metadata.last_modified_by == mock_metadata.last_modified_by


# Tests for set_new_metadata function
class TestSetNewMetadata:
    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_set_new_metadata_with_created_by(
        self, mock_datetime, mock_entity, mock_utc_now
    ):
        # Arrange
        mock_datetime.return_value = mock_utc_now
        created_by = "test_user"

        # Act
        result = set_new_metadata(mock_entity, created_by)

        # Assert
        assert result.metadata.created_on == mock_utc_now
        assert result.metadata.created_by == created_by
        assert result.metadata.last_modified_on == mock_utc_now
        assert result.metadata.last_modified_by == created_by

    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_set_new_metadata_without_created_by(
        self, mock_datetime, mock_entity, mock_utc_now
    ):
        # Arrange
        mock_datetime.return_value = mock_utc_now

        # Act
        result = set_new_metadata(mock_entity)

        # Assert
        assert result.metadata.created_on == mock_utc_now
        assert result.metadata.created_by == "DefaultUser"
        assert result.metadata.last_modified_on == mock_utc_now
        assert result.metadata.last_modified_by == "DefaultUser"

    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_set_new_metadata_preserves_entity_data(self, mock_datetime, mock_utc_now):
        # Arrange
        @dataclass
        class EntityWithData:
            data: str
            metadata: Optional[Metadata] = None

        entity = EntityWithData(data="test_data")
        mock_datetime.return_value = mock_utc_now

        # Act
        result = set_new_metadata(entity)

        # Assert
        assert result.data == "test_data"
        assert result.metadata is not None
        assert result.metadata.created_on == mock_utc_now


# Edge cases and error handling tests
class TestMetadataEdgeCases:
    def test_update_metadata_with_none_entity(self, mock_metadata):
        with pytest.raises(AttributeError):
            update_metadata(None, mock_metadata)

    def test_set_new_metadata_with_none_entity(self):
        with pytest.raises(AttributeError):
            set_new_metadata(None)

    @patch("ska_oso_slt_services.common.metadata_mixin.get_datetime_for_timezone")
    def test_timezone_error_handling(self, mock_datetime, mock_entity):
        # Arrange
        mock_datetime.side_effect = ValueError("Invalid timezone")

        # Act/Assert
        with pytest.raises(ValueError):
            set_new_metadata(mock_entity)
