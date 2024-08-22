from unittest.mock import patch

import pytest
from psycopg import DatabaseError

from ska_oso_slt_services.models.data_models import Shift
from ska_oso_slt_services.repositories.postgres_shift_repository import (
    PostgresShiftRepository,
)

# class TestShiftService:
#     #  @patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift")
#     @patch("ska_oso_slt_services.repositories.postgres_shift_repository
#     .PostgresShiftRepository.get_shifts")
#     #@patch("ska_oso_slt_services.data_access.postgres_data_access.")
#     #patch db connection get connection
#     def test_get_shifts(self,mock_postgres_shift_repository,valid_shift_data):
#         mock_get_shifts = Shift(**valid_shift_data)
#         mock_postgres_shift_repository.return_value = mock_get_shifts
#
#         shift_repository = PostgresShiftRepository()
#         # shift_service = ShiftService(
#         #     crud_shift_repository=shift_repository, shift_repositories=None
#         # )
#
#         response = shift_repository.get_shifts()
#         # import pdb
#         # pdb.set_trace()
#         assert valid_shift_data == response.model_dump(mode="JSON",exclude_none=True)


class TestPostgresShiftRepository:
    # @patch("ska_oso_slt_services.data_access.postgres_data_acess.PostgresDataAccess
    # .execute_query_or_update")
    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_get_shifts(self, mock_execute_or_update_query):
        # mock_get_shifts = Shift(**valid_shift_data)

        shift_data = [{
            "sid": 1,
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
            "annotations": "Routine maintenance shift.",
            "comments": "All systems operational.",
            "created_by": "admin",
            "created_time": "2024-07-27T07:00:00Z",
            "last_modified_by": "admin",
            "last_modified_time": "2024-07-27T07:30:00Z",
        }]

        mock_execute_or_update_query.return_value = shift_data
        # valid_shift_data["sid"] = 1
        # mock_execute_or_update_query.return_value = [valid_shift_data]

        # print("*********\n",mock_get_shifts)
        # mock_execute_or_update_query.return_value = mock_get_shifts
        # import pdb
        # pdb.set_trace()
        # print(1)
        shift_repository = PostgresShiftRepository()
        # import pdb
        # pdb.set_trace()
        response = shift_repository.get_shifts()
        # import pdb
        # pdb.set_trace()
        assert shift_data == [
            x.model_dump(mode="json", exclude_none=True, exclude_unset=True)
            for x in response
        ]
        # assert shift_data == response.model_dump(mode="json",
        # exclude_none=True,exclude_unset=True)

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository."
        "PostgresDataAccess.execute_query_or_update"
    )
    def test_get_shift(self, mock_execute_or_update_query):
        shift_data = [{
            "sid": 1,
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
            "annotations": "Routine maintenance shift.",
            "comments": "All systems operational.",
            "created_by": "admin",
            "created_time": "2024-07-27T07:00:00Z",
            "last_modified_by": "admin",
            "last_modified_time": "2024-07-27T07:30:00Z",
        }]

        mock_execute_or_update_query.return_value = shift_data
        shift_repository = PostgresShiftRepository()
        response = shift_repository.get_shift(1)
        # assert shift_data == [x.model_dump(mode="json", exclude_none=True
        # ,exclude_unset=True) for x in response]
        assert shift_data[0] == response.model_dump(
            mode="json", exclude_none=True, exclude_unset=True
        )

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository."
        "PostgresDataAccess.execute_query_or_update"
    )
    def test_create_shift(self, mock_execute_or_update_query):
        shift_data = {
            "sid": 1,
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
            "annotations": "Routine maintenance shift.",
            "comments": "All systems operational.",
            "created_by": "admin",
            "created_time": "2024-07-27T07:00:00Z",
            "last_modified_by": "admin",
            "last_modified_time": "2024-07-27T07:30:00Z",
        }
        mock_execute_or_update_query.return_value = shift_data

        shift = Shift(**shift_data)
        shift_repository = PostgresShiftRepository()
        response = shift_repository.create_shift(shift)

        assert shift_data == response.model_dump(
            mode="json", exclude_none=True, exclude_unset=True
        )

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_update_shift(self, mock_execute_or_update_query):
        shift_data = {
            "sid": 1,
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
            "annotations": "Routine maintenance shift.",
            "comments": "All systems operational.",
            "created_by": "admin",
            "created_time": "2024-07-27T07:00:00Z",
            "last_modified_by": "admin",
            "last_modified_time": "2024-07-27T07:30:00Z",
        }
        mock_execute_or_update_query.return_value = shift_data

        shift = Shift(**shift_data)
        shift_repository = PostgresShiftRepository()
        response = shift_repository.update_shift(shift)

        assert shift_data == response.model_dump(
            mode="json", exclude_none=True, exclude_unset=True
        )

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_get_shifts_invalid(self, mock_execute_or_update_query):
        mock_execute_or_update_query.side_effect = DatabaseError(
            "Database connection error"
        )

        shift_repository = PostgresShiftRepository()

        with pytest.raises(DatabaseError, match="Database connection error"):
            shift_repository.get_shifts()

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_get_shift_invalid(self, mock_execute_or_update_query):
        mock_execute_or_update_query.return_value = []

        shift_repository = PostgresShiftRepository()

        response = shift_repository.get_shift(999)  # Non-existing ID
        assert response is None

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_create_shift_invalid(self, mock_execute_or_update_query):
        mock_execute_or_update_query.side_effect = DatabaseError(
            "Failed to insert shift"
        )

        shift_data = {
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
        }

        shift = Shift(**shift_data)
        shift_repository = PostgresShiftRepository()

        with pytest.raises(DatabaseError, match="Failed to insert shift"):
            shift_repository.create_shift(shift)

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_update_shift_invalid(self, mock_execute_or_update_query):
        shift_data = {
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
        }

        shift = Shift(**shift_data)
        shift_repository = PostgresShiftRepository()

        with pytest.raises(
            ValueError, match="Shift SID is required for update operation"
        ):
            shift_repository.update_shift(shift)

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository.PostgresDataAccess"
        ".execute_query_or_update"
    )
    def test_update_shift_db_error(self, mock_execute_or_update_query):

        shift_data = {
            "sid": 1,
            "shift_id": "shift-001",
            "shift_start": "2024-07-28T08:00:00Z",
            "shift_end": "2024-07-28T16:00:00Z",
            "shift_operator": {"name": "John Doe"},
        }

        mock_execute_or_update_query.side_effect = DatabaseError(
            "Failed to update shift"
        )

        shift = Shift(**shift_data)
        shift_repository = PostgresShiftRepository()

        with pytest.raises(DatabaseError, match="Failed to update shift"):
            shift_repository.update_shift(shift)
