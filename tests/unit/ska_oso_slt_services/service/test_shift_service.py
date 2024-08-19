from copy import deepcopy
from unittest.mock import patch

import pytest

from ska_oso_slt_services.domain.models import Shift
from ska_oso_slt_services.repositories.postgres_shift_repository import (
    PostgresShiftRepository,
)
from ska_oso_slt_services.services.shift_service import ShiftService


@pytest.fixture()
def valid_shift_data():
    """Valid Create Shift Request Fixture"""
    return {
        "shift_operator": {"name": "John Doe"},
        "annotations": "Routine maintenance shift.",
        "comments": "All systems operational.",
    }


class TestShiftService:

    #  @patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift")
    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository."
        "PostgresShiftRepository.get_shifts"
    )
    # @patch("ska_oso_slt_services.data_access.postgres_data_access.")
    # #patch db connection get connection
    def test_get_shifts(self, mock_postgres_shift_repository, valid_shift_data):
        mock_get_shifts = Shift(**valid_shift_data)
        mock_postgres_shift_repository.return_value = mock_get_shifts

        shift_repository = PostgresShiftRepository()
        shift_service = ShiftService(
            crud_shift_repository=shift_repository, shift_repositories=None
        )

        response = shift_service.getShifts()
        # import pdb
        # pdb.set_trace()
        assert valid_shift_data == response.model_dump(mode="JSON", exclude_none=True)

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository"
        ".PostgresShiftRepository.get_shift"
    )
    def test_get_shift(
        self, mock_postgres_shift_repository_get_shifts, valid_shift_data
    ):
        valid_shift_data_with_id = deepcopy(valid_shift_data)
        valid_shift_data_with_id["id"] = 1
        mock_get_shifts = Shift(**valid_shift_data_with_id)
        mock_postgres_shift_repository_get_shifts.return_value = mock_get_shifts

        shift_repository = PostgresShiftRepository()
        shift_service = ShiftService(
            crud_shift_repository=shift_repository, shift_repositories=None
        )

        response = shift_service.get_shift(1)

        assert valid_shift_data_with_id == response.model_dump(
            mode="JSON", exclude_none=True
        )

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository"
        ".PostgresShiftRepository.create_shift"
    )
    # @patch("ska_oso_slt_services.data_access.postgres_data_access.")
    # #patch db connection get connection
    def test_create_shift(
        self, mock_postgres_shift_repository_create_shift, valid_shift_data
    ):
        mock_create_shifts = Shift(**valid_shift_data)
        mock_postgres_shift_repository_create_shift.return_value = mock_create_shifts

        shift_repository = PostgresShiftRepository()
        shift_service = ShiftService(
            crud_shift_repository=shift_repository, shift_repositories=None
        )

        response = shift_service.create_shift(mock_create_shifts)
        # import pdb
        # pdb.set_trace()
        assert valid_shift_data == response.model_dump(mode="JSON", exclude_none=True)

    @patch(
        "ska_oso_slt_services.repositories.postgres_shift_repository"
        ".PostgresShiftRepository.update_shift"
    )
    # @patch("ska_oso_slt_services.data_access.postgres_data_access.")
    # #patch db connection get connection
    def test_update_shift(
        self, mock_postgres_shift_repository_create_shift, valid_shift_data
    ):
        valid_shift_data_with_annotation = deepcopy(valid_shift_data)
        valid_shift_data_with_annotation["annotations"] = "updated_annotation"
        valid_shift_data_with_annotation["id"] = 1

        mock_update_shifts = Shift(**valid_shift_data_with_annotation)
        # import pdb
        # pdb.set_trace()
        mock_postgres_shift_repository_create_shift.return_value = mock_update_shifts

        shift_repository = PostgresShiftRepository()
        shift_service = ShiftService(
            crud_shift_repository=shift_repository, shift_repositories=None
        )

        response = shift_service.update_shift(mock_update_shifts)

        assert valid_shift_data_with_annotation == response.model_dump(
            mode="JSON", exclude_none=True
        )
