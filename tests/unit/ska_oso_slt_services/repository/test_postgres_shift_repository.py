import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)


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

        mock_eb_rows = [
            self._create_mock_eb("EB001", ["OK", "OK", "OK", "OK", "OK"], "Completed"),
            self._create_mock_eb("EB002", ["OK", "ERROR", "OK"], "Failed"),
            self._create_mock_eb("EB003", ["OK", "OK"], "In Progress"),
            self._create_mock_eb("EB004", [], "Created"),
        ]

        # Set up the mock
        repository.postgres_data_access.execute_query_or_update.return_value = (
            mock_eb_rows
        )
        # Call the method
        result = repository.get_oda_data(filter_date)

        self._assert_result_length(result, 4)
        self._assert_eb_status("EB001", result, "Completed", "Completed")
        self._assert_eb_status("EB002", result, "Failed", "Failed")
        self._assert_eb_status("EB003", result, "Executing", "In Progress")
        self._assert_eb_status("EB004", result, "Created", "Created")

        repository.postgres_data_access.execute_query_or_update.assert_called_once_with(
            query=unittest.mock.ANY, params=(expected_filter_date_tz,), query_type="GET"
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
