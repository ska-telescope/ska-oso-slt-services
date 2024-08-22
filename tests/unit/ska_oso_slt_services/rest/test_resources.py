import copy
import io
from datetime import datetime, timezone
from http import HTTPStatus
from unittest.mock import patch

from flask import json

from ska_oso_slt_services.models.data_models import Shift
from tests.unit.ska_oso_slt_services.util import assert_json_is_equal


class TestShiftCRUD:
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift")
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    @patch("ska_oso_slt_services.rest.api.resources.ShiftLogUpdater.update_shift_id")
    def test_create_shift_valid(
        self,
        mock_update_shift_id,
        mock_get_shift,
        mock_create_shift,
        client,
        valid_shift_data,
    ):
        """Verify that a valid shift can be created."""
        valid_shift_data_with_shift_start = copy.deepcopy(valid_shift_data)
        valid_shift_data_with_shift_start["shift_start"] = (
            "2024-07-28T08:00:00Z"  # datetime.utcnow()
        )
        valid_shift_data_with_id = copy.deepcopy(valid_shift_data_with_shift_start)
        valid_shift_data_with_id["sid"] = 1

        valid_shift_data_with_id_and_shift_id = copy.deepcopy(valid_shift_data_with_id)
        valid_shift_data_with_id_and_shift_id["shift_id"] = "shift-20240808-1"
        mock_shift = Shift(**valid_shift_data_with_id)
        mock_create_shift.return_value = mock_shift

        mock_get_shift_response = Shift(**valid_shift_data_with_id_and_shift_id)
        mock_get_shift.return_value = mock_get_shift_response
        response = client.post(
            "/ska-oso-slt-services/slt/api/v0/shifts",
            data=json.dumps(valid_shift_data_with_shift_start),
            content_type="application/json",
        )
        mock_update_shift_id.response = None
        assert response.status_code == HTTPStatus.CREATED
        assert_json_is_equal(
            response.data,
            mock_get_shift_response.model_dump_json(exclude_unset=True),
            exclude_paths=["root['shift_start']"],
        )

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.create_shift")
    def test_create_shift_invalid(
        self,
        mock_create_shift,
        client,
        invalid_shift_data,
        invalid_create_shift_response,
    ):
        """Verify that an invalid shift cannot be created."""
        response = client.post(
            "/ska-oso-slt-services/slt/api/v0/shifts",
            data=json.dumps(invalid_shift_data),
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert_json_is_equal(response.data, json.dumps(invalid_create_shift_response))
        mock_create_shift.assert_not_called()

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.update_shift")
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    def test_update_shift_valid(
        self, mock_get_shift, mock_update_shift, client, valid_update_shift_data
    ):
        """Verify that a valid shift can be updated."""
        shift_id = 1
        mock_shift_before_update = Shift(
            sid=shift_id, comments="Initial comments", annotations="Initial annotations"
        )
        mock_shift_after_update = Shift(sid=shift_id, **valid_update_shift_data)

        mock_get_shift.return_value = mock_shift_before_update
        mock_update_shift.return_value = mock_shift_after_update

        response = client.put(
            f"/ska-oso-slt-services/slt/api/v0/shifts/{shift_id}",
            data=json.dumps(valid_update_shift_data),
            content_type="application/json",
        )

        assert response.status_code == HTTPStatus.CREATED
        assert_json_is_equal(
            response.data, mock_shift_after_update.model_dump_json(exclude_unset=True)
        )

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    def test_get_shift_valid(self, mock_get_shift, client):
        """Verify that a valid shift can be retrieved."""
        shift_id = 1
        mock_shift = Shift(
            sid=shift_id,
            shift_operator={"name": "John Doe"},
            annotations="Routine maintenance shift.",
            comments="All systems operational.",
        )
        mock_get_shift.return_value = mock_shift

        response = client.get(f"/ska-oso-slt-services/slt/api/v0/shifts/{shift_id}")

        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data, mock_shift.model_dump_json(exclude_unset=True)
        )
        mock_get_shift.assert_called_once_with(sid=shift_id)

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    def test_get_shift_not_found(self, mock_get_shift, client):
        """Verify that a non-existent shift cannot be retrieved."""
        shift_id = 999
        mock_get_shift.return_value = None

        response = client.get(f"/ska-oso-slt-services/slt/api/v0/shifts/{shift_id}")

        assert response.status_code == HTTPStatus.NOT_FOUND
        assert_json_is_equal(response.data, json.dumps({"error": "Shift not found"}))
        mock_get_shift.assert_called_once_with(sid=shift_id)

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.getShifts")
    def test_get_shifts_valid(self, mock_get_shifts, client):
        """Verify that all shifts can be retrieved."""
        mock_shifts = [
            Shift(
                sid=1,
                shift_operator={"name": "John Doe"},
                annotations="Routine maintenance shift.",
                comments="All systems operational.",
            ),
            Shift(
                sid=2,
                shift_operator={"name": "Jane Doe"},
                annotations="System upgrade shift.",
                comments="Upgrade completed.",
            ),
        ]
        mock_get_shifts.return_value = mock_shifts

        response = client.get("/ska-oso-slt-services/slt/api/v0/shifts")

        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data,
            json.dumps([shift.model_dump(exclude_unset=True) for shift in mock_shifts]),
        )

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.getShifts")
    def test_get_shifts_with_filters(self, mock_get_shifts, client):
        """Verify that shifts can be retrieved with filters."""
        shift_start = "2024-07-01T00:00:00"
        shift_end = "2024-07-03T00:00:00"
        mock_shifts = [
            Shift(
                sid=1,
                shift_start=datetime(2024, 7, 1, 8, 0, 0, tzinfo=timezone.utc),
                shift_end=datetime(2024, 7, 1, 16, 0, 0, tzinfo=timezone.utc),
                shift_operator={"name": "John Doe"},
                annotations="Routine maintenance shift.",
                comments="All systems operational.",
                created_by=None,
                created_time=None,
                last_modified_by=None,
                last_modified_time=None,
                media=None,
                shift_logs=None,
            )
        ]
        mock_get_shifts.return_value = mock_shifts
        response = client.get(
            "/ska-oso-slt-services/slt/api/v0/shifts?shift_start="
            f"{shift_start}&shift_end={shift_end}"
        )

        expected_response = [
            shift.model_dump(exclude_unset=True, exclude_none=True)
            for shift in mock_shifts
        ]

        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data,
            json.dumps(expected_response),
            exclude_paths=["root[0]['shift_start']", "root[0]['shift_end']"],
        )

    @patch("ska_oso_slt_services.rest.api.resources.shift_repository.get_oda_data")
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_shift")
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.update_shift")
    def test_update_shift_log_info(
        self,
        mock_update_shift,
        mock_get_shift,
        mock_shift_repository_get_oda_data,
        client,
        shift_data_with_logs,
        updated_shift_data_with_logs,
    ):
        """Verify that shift log info can be updated."""
        shift_id = 1
        mock_get_shift.return_value = shift_data_with_logs
        mock_shift_repository_get_oda_data.return_value = {
            "eb-t0001-20240801-00004": {
                "eb_id": "eb-t0001-20240801-00004",
                "sbd_ref": "sbd-t0001-20240801-00002",
                "sbi_ref": "sbd-t0001-20240801-00003",
                "metadata": {
                    "version": 1,
                    "created_by": "DefaultUser",
                    "created_on": "2024-08-01T17:24:38.004027Z",
                    "last_modified_by": "DefaultUser",
                    "last_modified_on": "2024-08-01T17:24:38.004027Z",
                },
                "interface": "https://schema.skao.int/ska-oso-pdm-eb/0.1",
                "telescope": "ska_mid",
                "sbi_status": "updated",
                "sbd_version": 1,
                "request_responses": [],
            }
        }
        mock_update_shift.return_value = updated_shift_data_with_logs

        response = client.put(
            f"/ska-oso-slt-services/slt/api/v0/shifts/{shift_id}/logs_update"
        )

        assert response.status_code == HTTPStatus.CREATED
        exclude_paths = [
            "root['created_by']",
            "root['created_time']",
            "root['last_modified_by']",
            "root['last_modified_time']",
            "root['media']",
            "root['shift_end']",
            "root['shift_logs'][0]['log_time']",
            "root['shift_start']",
        ]
        assert_json_is_equal(
            response.data,
            updated_shift_data_with_logs.model_dump_json(exclude_unset=True),
            exclude_paths,
        )

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.add_media")
    @patch("ska_oso_slt_services.rest.api.resources.upload_image_to_folder")
    def test_add_add_media(self, mock_save_file, mock_add_media, client):
        """Verify that valid image should be upload."""
        shift_id = 1

        mock_save_file.return_value = "test", "test/1_mccs.png"
        mock_add_media.return_value = True
        data = {}
        data["files"] = (io.BytesIO(b"abcdef"), "1_mccs.png")

        response = client.post(
            f"/ska-oso-slt-services/slt/api/v0/shifts/images/{shift_id}",
            headers={"Content-Type": "multipart/form-data"},
            data=data,
        )

        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data,
            json.dumps({"message": "Image uploaded successfully"}),
        )

    # taking above reference write test case for get media
    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_media")
    @patch("ska_oso_slt_services.rest.api.resources.read_image_from_folder")
    def test_get_media(self, mock_read_image, mock_get_media, client):
        """Verify that valid image should be upload."""
        shift_id = 1
        mock_get_media.return_value = [{"type": "test", "path": "test"}]
        mock_read_image.return_value = "test"
        response = client.get(
            f"/ska-oso-slt-services/slt/api/v0/shifts/images/{shift_id}"
        )

        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data.decode("utf-8"),
            '[\n  "test"\n]\n',
        )

    @patch("ska_oso_slt_services.services.shift_service.ShiftService.get_current_shift")
    def test_get_current_shifts_valid(self, mock_get_shifts, client):
        """Verify that all shifts can be retrieved."""
        mock_shift = Shift(
            sid=1,
            shift_operator={"name": "John Doe"},
            annotations="Routine maintenance shift.",
            comments="All systems operational.",
        )

        mock_get_shifts.return_value = mock_shift

        response = client.get("/ska-oso-slt-services/slt/api/v0/current_shifts")
        assert response.status_code == HTTPStatus.OK
        assert_json_is_equal(
            response.data,
            mock_shift.model_dump_json(exclude_unset=True),
        )
