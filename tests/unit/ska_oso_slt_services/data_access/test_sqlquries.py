import unittest
from datetime import datetime

from psycopg import sql

from ska_oso_slt_services.data_access.postgres.mapping import ShiftLogMapping
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    insert_query,
    select_latest_query,
    update_query,
)
from ska_oso_slt_services.domain.shift_models import Shift


class TestShiftQueries(unittest.TestCase):

    def setUp(self):
        # Create a mock TableDetails object
        self.table_details = ShiftLogMapping()

        # Create a mock Shift object
        self.shift = Shift(
            shift_id="123",
            shift_start=datetime(2023, 1, 1, 9, 0),
            shift_end=datetime(2023, 1, 1, 17, 0),
            shift_type="Day",
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
        query, params = update_query(self.table_details, self.shift)

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

    def test_select_latest_query(self):
        query, params = select_latest_query(self.table_details, self.shift.shift_id)

        # Check if the query is of the correct type
        self.assertIsInstance(query, sql.Composed)

        # Check if the query contains the correct table name
        self.assertIn("tab_oda_slt", query.as_string())

        # Check if the query is a SELECT query
        self.assertIn("SELECT", query.as_string())

        # Check if the query includes ORDER BY clause
        self.assertIn("ORDER BY id", query.as_string())

        # Check if the parameters are correct
        self.assertEqual(params, (self.shift.shift_id,))
