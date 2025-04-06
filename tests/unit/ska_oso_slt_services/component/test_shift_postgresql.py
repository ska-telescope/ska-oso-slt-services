"""Component test for shift operations using pytest-postgresql."""

from datetime import datetime, timezone

import pytest
from pytest_postgresql import factories

from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.domain.shift_models import Metadata, Shift, ShiftComment
from ska_oso_slt_services.repository.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService

postgresql_my_proc = factories.postgresql_proc(port=None, unixsocketdir="/tmp")
postgresql_my = factories.postgresql("postgresql_my_proc")


@pytest.fixture
def shift_comment_data():
    """Fixture to create test shift comment data."""
    return {
        "comment": "Test comment",
        "shift_id": "test_shift",
        "operator_name": "test1",
        "image": [],
        "metadata": {
            "created_by": "test_user",
            "created_on": datetime.now(timezone.utc).isoformat(),
            "last_modified_by": "test_user",
            "last_modified_on": datetime.now(timezone.utc).isoformat(),
        },
    }


@pytest.fixture
def shift_data():
    return {
        "id": 1,
        "shift_id": "test_shift",
        "shift_operator": "test",
        "created_by": "test",
        "shift_start": datetime.now(timezone.utc),
        "last_modified_by": "test",
        "last_modified_on": datetime.now(timezone.utc),
        "created_on": datetime.now(timezone.utc),
    }


# @pytest.fixture
# def db_crud():
#     return PostgresDataAccess(postgres_connection=postgresql_my)


def test_shift_e2e(postgresql_my, shift_data, init_database, shift_comment_data):
    """Test inserting a shift into the database."""
    # Create shift instance
    shift = Shift(**shift_data)

    # Define repository class that uses test database

    class TestPostgresShiftRepository(PostgresShiftRepository):
        """Repository class for testing with pytest-postgresql database."""

        def __init__(self, postgres_data_access=None):
            # Create a test data access if none provided
            if postgres_data_access is None:
                test_data_access = PostgresDataAccess()
                test_data_access.postgres_connection = postgresql_my
                postgres_data_access = test_data_access
            super().__init__(postgres_data_access)

    shift_service = ShiftService([TestPostgresShiftRepository])

    metadata = {
        "created_by": "test",
        "created_on": datetime.now(timezone.utc),
        "last_modified_by": "test",
        "last_modified_on": datetime.now(timezone.utc),
    }
    shift.metadata = Metadata(**metadata)
    # Insert shift into database
    result = shift_service.create_shift(shift)
    assert result.id == 1
    # # Verify shift was inserted
    # assert shift_id == 1

    # Retrieve shift and verify data
    retrieved_shift = shift_service.get_shift("test_shift")
    assert retrieved_shift.id == shift_data["id"]
    assert retrieved_shift.shift_operator == shift_data["shift_operator"]

    shift.shift_operator = "test1"
    updated_shift = shift_service.update_shift(shift_id="test_shift", shift_data=shift)
    assert updated_shift.shift_operator == "test1"

    # Create shift comment
    shift_comment = ShiftComment(**shift_comment_data)
    created_comment = shift_service.create_shift_comment(shift_comment)
    assert created_comment.comment == shift_comment_data["comment"]
    assert created_comment.shift_id == shift_comment_data["shift_id"]
