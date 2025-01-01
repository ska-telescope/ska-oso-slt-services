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

    def test_mapping_factory__given_shift__then_correct_mapping_type(self):
        # when
        mapping = TableMappingFactory.create_mapping(ShiftBaseClass)
        # then
        assert mapping.table_details.table_name == "tab_oda_slt"

    # write same pattern type tet case for ShiftAnnotations
    def test_mapping_factory__given_shift_annotation__then_correct_mapping_type(self):
        # when
        mapping = TableMappingFactory.create_mapping(ShiftAnnotation)
        # then
        assert mapping.table_details.table_name == "tab_oda_slt_shift_annotations"

    def test_mapping_factory__given_shift_comment__then_correct_mapping_type(self):
        # when
        mapping = TableMappingFactory.create_mapping(ShiftComment)
        # then
        assert mapping.table_details.table_name == "tab_oda_slt_shift_comments"

    def test_mapping_factory__given_shift_log_comment__then_correct_mapping_type(self):
        # when
        mapping = TableMappingFactory.create_mapping(ShiftLogComment)
        # then
        assert mapping.table_details.table_name == "tab_oda_slt_shift_log_comments"
