import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

from psycopg import DatabaseError

from ska_oso_slt_services.common.custom_exceptions import ShiftEndedException
from ska_oso_slt_services.domain.shift_models import Media, Shift, ShiftLogComment
from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)


def mocked_postgres_repository():
    """Fixture that provides a PostgresShiftRepository with mocked dependencies."""
    repository = PostgresShiftRepository()
    repository.postgres_data_access = Mock()
    repository.crud = Mock()
    return repository


class TestPostgressShiftRepository(unittest.TestCase):

    def test_get_oda_data(self):
        """
        Test case for the get_oda_data method.
        It mocks the database query and checks if the method returns the expected data.
        """
        # Create an instance of PostgressShiftRepository
        repository = PostgresShiftRepository()

        # Mock the postgres_data_access attribute
        repository.postgres_data_access = Mock()

        filter_date = "2023-01-01T00:00:00"
        expected_filter_date_tz = datetime.fromisoformat(filter_date).replace(
            tzinfo=timezone(timedelta(hours=0, minutes=0))
        )

        mock_eb_rows = (
            self._create_mock_eb("EB001", ["OK", "OK", "OK", "OK", "OK"], "Completed"),
            self._create_mock_eb("EB002", ["OK", "ERROR", "OK"], "Failed"),
            self._create_mock_eb("EB003", ["OK", "OK"], "In Progress"),
            self._create_mock_eb("EB004", [], "Created"),
        )

        # Set up the mock
        repository.postgres_data_access.get.return_value = mock_eb_rows
        # Call the method
        result = repository.get_oda_data(filter_date)

        self._assert_result_length(result, 4)
        self._assert_eb_status("EB001", result, "Completed", "Completed")
        self._assert_eb_status("EB002", result, "Failed", "Failed")
        self._assert_eb_status("EB003", result, "Executing", "In Progress")
        self._assert_eb_status("EB004", result, "Created", "Created")

        repository.postgres_data_access.get.assert_called_once_with(
            query=unittest.mock.ANY, params=(expected_filter_date_tz,)
        )

    def _create_mock_eb(self, eb_id, statuses, current_status):
        """
        Helper method to create a mock EB row.
        It takes the EB ID, a list of statuses, and the current status as input.
        It returns a dictionary representing the EB row.
        """
        return {
            "eb_id": eb_id,
            "info": {"request_responses": [{"status": s} for s in statuses]},
            "current_status": current_status,
        }

    def _assert_result_length(self, result, expected_length):
        """
        Helper method to assert the length of the result.
        It checks if the length of the result matches the expected length.
        If the lengths don't match, it raises an
        AssertionError with a descriptive message.
        :param result: The result to be checked.
        :param expected_length: The expected length of the result.
        :raises AssertionError: If the lengths don't match.
        """
        self.assertEqual(
            len(result),
            expected_length,
            f"Expected {expected_length} items, but got {len(result)}",
        )

    def _assert_eb_status(self, eb_id, result, expected_sbi_status, expected_eb_status):
        """
        Helper method to assert the SBI status and EB status of an EB.
        It checks if the SBI status and EB status of the given
        EB ID match the expected values.
        If the values don't match, it raises an AssertionError
        with a descriptive message.
        :param eb_id: The EB ID to be checked.
        :param result: The result containing the EB data.
        :param expected_sbi_status: The expected SBI status.
        :param expected_eb_status: The expected EB status.
        :raises AssertionError: If the SBI status or EB status
            doesn't match the expected values.
        """
        self.assertIn(
            eb_id, result, f"Expected {eb_id} in result, but it was not found"
        )
        self.assertEqual(result[eb_id]["sbi_status"], expected_sbi_status)
        self.assertEqual(result[eb_id]["eb_status"], expected_eb_status)

    def test_get_shifts(self):
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        repository.crud.get_entities = Mock(return_value={"shift_id": "test-shift"})
        result = repository.get_shifts()
        # Assert the result
        self._assert_result_length(result, 1)
        self.assertEqual(result, {"shift_id": "test-shift"})

    def test_get_shift(self):
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        repository.crud.get_entity = Mock(return_value={"shift_id": "test-shift"})
        result = repository.get_shift("test-shift")
        # Assert the result
        self._assert_result_length(result, 1)
        self.assertEqual(result, {"shift_id": "test-shift"})

    def test_update_shift_end_time(self):
        """Test successful shift end time update"""
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        # Create test data
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        existing_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )

        # Mock get_shift to return our test shift
        repository.get_shift = Mock(return_value=existing_shift)

        # Call the method
        result = repository.update_shift_end_time(test_shift)

        # Verify the results
        self.assertIsInstance(result, Shift)
        self.assertEqual(result.shift_id, "test-shift")
        self.assertIsNotNone(result.shift_end)
        repository.crud.update_entity.assert_called_once()

    def test_update_shift_end_time_already_ended(self):
        """Test updating an already ended shift"""
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        # Create test data with end time already set
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        existing_shift = Shift(
            shift_id="test-shift",
            shift_start="2023-01-01T00:00:00",
            shift_end="2023-01-01T08:00:00",
        )

        # Mock get_shift to return already ended shift
        repository.get_shift = Mock(return_value=existing_shift)

        # Call the method
        result = repository.update_shift_end_time(test_shift)

        # Verify it returns ShiftEndedException
        self.assertIsInstance(result, ShiftEndedException)
        repository.crud.update_entity.assert_not_called()

    def test_update_shift_end_time_database_error(self):
        """Test database error handling during shift end time update"""
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        # Create test data
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        existing_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )

        # Mock get_shift to return our test shift
        repository.get_shift = Mock(return_value=existing_shift)

        # Mock database error
        db_error = DatabaseError("Test database error")
        repository.crud.update_entity.side_effect = db_error

        # Verify it raises the error
        with self.assertRaises(DatabaseError) as context:
            repository.update_shift_end_time(test_shift)

        self.assertEqual(str(context.exception), "Test database error")

    def test_update_shift(self):
        """Test successful shift update"""
        # Get mocked repository from fixture
        repository = mocked_postgres_repository()

        # Create test data
        test_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )
        existing_shift = Shift(
            shift_id="test-shift", shift_start="2023-01-01T00:00:00", shift_end=None
        )

        # Mock get_shift to return our test shift
        repository.get_shift = Mock(return_value=existing_shift)

        # Call the method
        result = repository.update_shift(test_shift)

        # Verify the results
        self.assertIsInstance(result, Shift)
        self.assertEqual(result.shift_id, "test-shift")

    def test_get_media(self):
        """Test getting media files for a comment."""
        # Mock the get_shift_logs_comment method
        mock_comment = MagicMock()
        mock_comment.image = [MagicMock(unique_id="test_file_key")]
        self.repository = mocked_postgres_repository()
        self.repository.get_shift_logs_comment = MagicMock(
            return_value=ShiftLogComment(
                id=1,
                log_comment="Test comment",
                image=[Media(path="test_file_key", unique_id="test_file_key")],
            )
        )

        # Mock the get_file_object_from_s3 function
        with patch(
            "ska_oso_slt_services.repository.postgres_shift_repository."
            "get_file_object_from_s3"
        ) as mock_s3:
            mock_s3.return_value = ("test_file_key", "base64_content", "image/jpeg")

            # Test successful case
            result = self.repository.get_media(1, ShiftLogComment)

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["file_key"], "test_file_key")

            # Verify the mocks were called correctly
            self.repository.get_shift_logs_comment.assert_called_once_with(
                comment_id=1, entity=ShiftLogComment
            )
            mock_s3.assert_called_once_with(file_key="test_file_key")

        # Test case where comment has no images
        mock_comment.image = []
        self.repository.get_shift_logs_comment = MagicMock(return_value=mock_comment)
