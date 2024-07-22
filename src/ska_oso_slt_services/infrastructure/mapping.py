from datetime import datetime
from typing import Any, Dict, List, Optional

from ska_oso_slt_services.database.config import SLTConfig
from ska_oso_slt_services.infrastructure.postgresql import Postgresql, QueryType

slt_config = SLTConfig()


class SLTRepository(Postgresql):
    def __init__(self):
        super().__init__(table_name=slt_config.SLT_TABLE_NAME)

    def _get_base_query(self) -> str:
        """
        Returns the base SQL query with LEFT JOINs for SLT, SLTLog, and SLTImage.

        :return: The base SQL query string.
        """
        return """
            SELECT
                odaslt.*,
                odasltlog.info AS log_info,
                odasltlog.source AS log_source,
                odasltimage.image_path AS image_path
            FROM
                tab_oda_slt odaslt
            LEFT JOIN
                tab_oda_slt_log odasltlog ON odaslt.id = odasltlog.slt_ref
            LEFT JOIN
                tab_oda_slt_image odasltimage ON odaslt.id = odasltimage.slt_ref"""

    def get_records_by_shift_time(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from SLT where shift_start is within the specified time
        range.

        :param start_time: Start of the time range.
        :param end_time: End of the time range.
        :return: List of records as dictionaries.
        """
        query = (
            f"SELECT * FROM {self.table_name}" + " WHERE shift_start BETWEEN %s AND %s"
        )
        params = (start_time, end_time)

        return (
            self._execute_query_or_update(
                query=query, query_type=QueryType.GET, params=params
            )
            or "No Record Found"
        )

    def get_records_with_logs_and_image(
        self, record_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from SLT with associated logs and images. Optionally filters
        by record_id.

        :param record_id: Optional; ID of the record to fetch.
        :return: List of records with logs and images as dictionaries.
        """
        base_query = self._get_base_query()
        # If record_id is provided, filter by it; otherwise, return all records
        query = base_query + (" WHERE odaslt.id = %s" if record_id is not None else "")
        params = (record_id,) if record_id is not None else None

        return (
            self._execute_query_or_update(
                query=query, query_type=QueryType.GET, params=params
            )
            or "No Record Found"
        )

    def get_records_by_shift_time_with_logs_and_image(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from SLT with associated logs and images where shift_start
        is within the specified time range.

        :param start_time: Optional; Start of the time range.
        :param end_time: Optional; End of the time range.
        :return: List of records with logs and images as dictionaries.
        """
        base_query = self._get_base_query()
        query = base_query + " WHERE odaslt.shift_start BETWEEN %s AND %s"
        params = (start_time, end_time)

        return (
            self._execute_query_or_update(
                query=query, query_type=QueryType.GET, params=params
            )
            or "No Record Found"
        )


class SLTLogRepository(Postgresql):
    def __init__(self):
        super().__init__(table_name=slt_config.SLT_LOG_TABLE_NAME)


class SLTImageRepository(Postgresql):
    def __init__(self):
        super().__init__(table_name=slt_config.SLT_IMAGE_TABLE_NAME)
