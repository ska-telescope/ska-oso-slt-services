import json
import unittest
from datetime import datetime
from enum import Enum

from psycopg import sql
from ska_oso_pdm.entity_status_history import SBIStatus

from ska_oso_slt_services.data_access.postgres.mapping import (
    ShiftCommentMapping,
    ShiftLogMapping,
)
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    build_search_query,
    insert_query,
    patch_query,
    select_by_date_query,
    select_latest_shift_query,
    select_logs_by_status,
    update_query,
)
from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    Filter,
    MatchType,
    SbiEntityStatus,
    Shift,
    ShiftLogs,
)


class TestShiftQueries(unittest.TestCase):

    def setUp(self):
        # Create a mock TableDetails object
        self.table_details = ShiftLogMapping()
        self.comment_table_details = ShiftCommentMapping()
        self.entity_id = "test"

        # Create a mock Shift object
        self.shift = Shift(
            shift_id="123",
            shift_start=datetime(2023, 1, 1, 9, 0),
            shift_end=datetime(2023, 1, 1, 17, 0),
            shift_type="Day",
            shift_operator="test",
            status="Active",
            metadata={
                "created_by": "Jimmy                                             ",
                "created_on": "2024-10-15T12:03:50.680859+05:30",
                "last_modified_by": "Jimmy               ",
                "last_modified_on": "2024-10-15T12:03:50.680859+05:30",
            },
        )

    def test_insert_query(self):
        query, params = insert_query(self.table_details, self.shift)

        # Check if the query is of the correct type
        self.assertIsInstance(query, sql.Composed)

        # Check if the query contains the correct table name
        self.assertIn("tab_oda_slt", query.as_string())

        # Check if the query is an INSERT query
        self.assertIn("INSERT INTO", query.as_string())

        # Check if the parameters are correct
        self.assertIn(self.shift.shift_id, params)
        self.assertIn(self.shift.shift_start, params)
        self.assertIn(self.shift.shift_end, params)

    def test_update_query(self):
        query, params = update_query(self.entity_id, self.table_details, self.shift)

        # Check if the query is of the correct type
        self.assertIsInstance(query, sql.Composed)

        # Check if the query contains the correct table name
        self.assertIn("tab_oda_slt", query.as_string())

        # Check if the query is an UPDATE query
        self.assertIn("UPDATE", query.as_string())

        # Check if the parameters are correct
        self.assertIn(self.shift.shift_id, params)
        self.assertIn(self.shift.shift_start, params)
        self.assertIn(self.shift.shift_end, params)

    def test_select_by_date_query(self):
        """Test the select_by_date_query function."""
        # Call the function with test data
        query, params = select_by_date_query(
            self.table_details, self.shift  # Using the shift object from setUp
        )

        # Check if the query is of the correct type
        self.assertIsInstance(query, sql.Composed)

        # Convert query to string for assertions
        query_string = query.as_string()

        # Check if the query contains the correct table name
        self.assertIn("tab_oda_slt", query_string)

        # Check if the query is a SELECT query
        self.assertIn("SELECT", query_string)

        # Check if the query has the correct comparison operators
        if self.shift.shift_start and self.shift.shift_end:
            self.assertIn(">=", query_string)
            self.assertIn("<=", query_string)
            self.assertEqual(params, (self.shift.shift_start, self.shift.shift_end))
        elif self.shift.shift_start:
            self.assertIn(">=", query_string)
            self.assertEqual(params, (self.shift.shift_start,))
        elif self.shift.shift_end:
            self.assertIn("<=", query_string)
            self.assertEqual(params, (self.shift.shift_end,))

    def test_build_search_query_unsupported_match_type(self):
        """Test build_search_query raises ValueError for unsupported match type."""
        # Test data
        columns = ["column1", "column2"]
        search_columns = ["column1"]
        search_text = "test search"

        # Create an Enum member that's not one of the expected values
        class TestFilter(Enum):
            INVALID = "invalid"

        match_type = MatchType(match_type=Filter.EQUALS)

        match_type.match_type = TestFilter.INVALID

        # Assert that ValueError is raised
        with self.assertRaises(ValueError) as context:
            build_search_query(
                self.table_details, columns, search_columns, match_type, search_text
            )

        # Check if the error message is correct
        self.assertEqual(
            str(context.exception), f"Unsupported match_type: {match_type.match_type}"
        )

    def test_patch_query_edge_cases(self):
        """Test patch_query with edge cases."""
        # Test with empty column names and params
        query, params = patch_query(
            self.table_details,
            [],
            tuple([]),  # Convert empty list to tuple
            123,
            self.shift,
        )
        self.assertIsInstance(query, sql.Composed)
        # Should still include metadata params
        self.assertEqual(len(params), 5)  # 2 metadata params + shift_id

        # Test without shift parameter (when shift=None)
        query, params = patch_query(
            self.table_details,
            ["status"],
            tuple(["Active"]),  # Convert list to tuple
            123,
            self.shift,
        )
        self.assertIsInstance(query, sql.Composed)
        self.assertEqual(len(params), 6)  # 1 input param + shift_id

        # Test with multiple columns
        columns = ["status", "shift_type", "operator"]
        values = tuple(["Active", "Day", "John"])  # Convert list to tuple
        query, params = patch_query(
            self.table_details, columns, values, 123, self.shift
        )
        self.assertIsInstance(query, sql.Composed)

        for column in columns:
            self.assertIn(column, query.as_string())

        # Check if the query has the correct structure
        query_string = query.as_string()
        self.assertIn("UPDATE", query_string)
        self.assertIn("SET", query_string)
        self.assertIn("WHERE", query_string)
        self.assertIn("RETURNING id", query_string)

    def test_patch_query_with_none_shift_error_try_except(self):
        """Test patch_query with None shift using try-except block."""
        # Test data
        column_names = ["status"]
        params = tuple(["Active"])
        shift_id = 123
        error_caught = False

        try:
            patch_query(self.table_details, column_names, params, shift_id, shift=None)
        except AttributeError as e:
            error_caught = True
            # Verify it's the expected error
            self.assertEqual(str(e), "'NoneType' object has no attribute 'metadata'")

        # Verify that the error was actually caught
        self.assertTrue(
            error_caught, "AttributeError should have been raised when shift is None"
        )

    def test_select_latest_shift_query(self):
        """Test select_latest_shift_query function"""
        # Execute the function
        query, params = select_latest_shift_query(self.table_details)

        # Check if the query is of the correct type
        self.assertIsInstance(query, sql.Composed)

        # Convert query to string for assertion checks
        query_string = query.as_string()

        # Check basic SQL structure
        self.assertIn("SELECT shift_id", query_string)  # Only shift_id is selected
        self.assertIn('FROM "tab_oda_slt"', query_string)
        self.assertIn("WHERE shift_end IS NULL", query_string)
        self.assertIn("ORDER BY id DESC", query_string)
        self.assertIn("LIMIT 1", query_string)

        # Check if parameters tuple is empty as expected
        self.assertEqual(params, ())

        # Expected query structure
        expected_query_parts = [
            "SELECT shift_id",
            'FROM "tab_oda_slt"',
            "WHERE shift_end IS NULL",
            "ORDER BY id DESC",
            "LIMIT 1",
        ]

        # Check each part is in the query
        for part in expected_query_parts:
            self.assertIn(part, query_string)

    def test_get_shift_log_columns(self):
        """Test get_shift_log_columns returns correct column names"""
        # Create an instance of the class containing get_shift_log_columns
        table_details = self.table_details  # or your actual class name

        # Call the method
        columns = table_details.get_shift_log_columns()

        # Assert the return value is correct
        self.assertEqual(columns, ["shift_logs"])

        # Assert it returns a list
        self.assertIsInstance(columns, list)

        # Assert it contains exactly one element
        self.assertEqual(len(columns), 1)

        # Assert the element is a string
        self.assertIsInstance(columns[0], str)

    def test_get_shift_log_params(self):
        """Test get_shift_log_params returns correct parameter values"""
        # Create mock shift logs
        # shift_logs = ShiftLogs(
        #     info={"message": "Test log"},
        #     source="operator",
        #     log_time=datetime(2024, 1, 1, 12, 0),
        #     comments=[],
        # )

        shift_logs_dict = [
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
                            "request": "ska_oso_scripting."
                            "functions.devicecontrol.configure_resource",
                            "response": {"result": "this is a result"},
                            "request_args": {"kwargs": {"subarray_id": "1"}},
                            "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            "response_received_at": "2022-09-23T15:43:53.971548Z",
                        },
                        {
                            "status": "OK",
                            "request": "ska_oso_scripting.functions.devicecontrol.scan",
                            "response": {"result": "this is a result"},
                            "request_args": {"kwargs": {"subarray_id": "1"}},
                            "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            "response_received_at": "2022-09-23T15:43:53.971548Z",
                        },
                        {
                            "status": "OK",
                            "request": "ska_oso_scripting."
                            "functions.devicecontrol.release_all_resources",
                            "response": {"result": "this is a result"},
                            "request_args": {"kwargs": {"subarray_id": "1"}},
                            "request_sent_at": "2022-09-23T15:43:53.971548Z",
                            "response_received_at": "2022-09-23T15:43:53.971548Z",
                        },
                        {
                            "error": {"detail": "this is an error"},
                            "status": "ERROR",
                            "request": "ska_oso_scripting.functions.devicecontrol.end",
                            "request_sent_at": "2022-09-23T15:43:53.971548Z",
                        },
                    ],
                },
                "source": "ODA",
                "log_time": "2024-10-22T11:24:14.406107Z",
                "comments": [
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
                        "shift_id": "shift-20241112-1",
                        "eb_id": "eb-t0001-20241022-00002",
                        "metadata": {
                            "created_by": "max",
                            "created_on": "2024-11-12T14:22:07.328322+05:30",
                            "last_modified_by": "max",
                            "last_modified_on": "2024-11-12T14:22:07.328322+05:30",
                        },
                    },
                    {
                        "id": 3,
                        "log_comment": "This is log comment",
                        "operator_name": "max",
                        "shift_id": "shift-20241112-1",
                        "eb_id": "eb-t0001-20241022-00002",
                        "metadata": {
                            "created_by": "max",
                            "created_on": "2024-11-12T20:46:26.631930+05:30",
                            "last_modified_by": "max",
                            "last_modified_on": "2024-11-12T20:46:26.631930+05:30",
                        },
                    },
                ],
            }
        ]
        shift_logs_obj = ShiftLogs.model_validate(shift_logs_dict[0])
        shift = Shift(shift_logs=[shift_logs_obj])

        # # Create mock shift object
        # mock_shift = Mock()
        # mock_shift.shift_logs = shift_logs

        # Create an instance of the class containing get_shift_log_params
        table_details = self.table_details  # or your actual class name

        # Call the method
        params = table_details.get_shift_log_params(shift)

        # Assert it returns a tuple
        self.assertIsInstance(params, tuple)

        # Assert tuple length is 1 (as we have one column_map_extra_keys entry)
        self.assertEqual(len(params), 1)

        # Assert the parameter is a JSON string
        json_param = params[0]
        self.assertIsInstance(json_param, str)

        # Parse and verify JSON content
        parsed_json = json.loads(json_param)[0]
        self.assertIsInstance(parsed_json, dict)

        # Verify expected fields in JSON
        expected_fields = ["info", "source", "log_time", "comments"]
        for field in expected_fields:
            self.assertIn(field, parsed_json)

        # Verify specific values
        self.assertEqual(parsed_json["info"]["eb_id"], "eb-t0001-20241022-00002")
        self.assertEqual(parsed_json["source"], "ODA")
        self.assertIsInstance(parsed_json["comments"], list)
