from unittest.mock import patch

from ska_oso_slt_services.common.utils import set_telescope_type
from ska_oso_slt_services.repository.postgres_shift_repository import create_shift_id


def test_set_telescope_type_mid():

    telescope_type = set_telescope_type("SKA-Mid")

    assert telescope_type == "mid"


@patch("ska_oso_slt_services.common.utils.getenv", return_value="SKA-Low")
def test_set_telescope_type_low(mock_getenv):

    telescope_type = set_telescope_type("SKA-Low")

    assert telescope_type == "low"


@patch(
    "ska_oso_slt_services.repository.postgres_shift_repository.skuid.fetch_skuid",
    return_value="sl-m0001-20241204-00004",
)
@patch(
    "ska_oso_slt_services.repository.postgres_shift_repository.set_telescope_type",
    return_value="mid",
)
def test_create_shift_id(mock_skuid, mock_telescope_type):

    shift_id = create_shift_id()

    assert shift_id == "sl-m0001-20241204-00004"
