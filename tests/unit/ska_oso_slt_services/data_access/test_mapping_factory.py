import pytest

from ska_oso_slt_services.data_access.postgres.mapping_factory import (
    TableMappingFactory,
)
from ska_oso_slt_services.domain.shift_models import (
    ShiftAnnotation,
    ShiftBaseClass,
    ShiftComment,
    ShiftLogComment,
)


class TestMappingFactory:

    @pytest.mark.parametrize(
        "input_class,expected_table_name",
        [
            (ShiftBaseClass, "tab_oda_slt"),
            (ShiftAnnotation, "tab_oda_slt_shift_annotations"),
            (ShiftComment, "tab_oda_slt_shift_comments"),
            (ShiftLogComment, "tab_oda_slt_shift_log_comments"),
        ],
    )
    def test_mapping_factory_creates_correct_mapping_type(
        self, input_class, expected_table_name
    ):
        # when
        mapping = TableMappingFactory.create_mapping(input_class)
        # then
        assert mapping.table_details.table_name == expected_table_name
