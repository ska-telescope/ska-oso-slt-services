from datetime import datetime
from typing import Optional, List, Dict, Any
from psycopg import DatabaseError
from repository_classes.base_repository_mappings import BaseRepository, QueryType

class ODASLTRepository(BaseRepository):
    def __init__(self):
        super().__init__(table_name='tab_oda_slt')

    def _get_base_query(self) -> str:
        """
        Returns the base SQL query with LEFT JOINs for ODASLT, ODASLTLogs, and ODASLTImages.

        :return: The base SQL query string.
        """
        return """
            SELECT 
                odaslt.*,
                odasltlogs.info AS log_info,
                odasltlogs.source AS log_source,
                odasltimages.image_path AS image_path
            FROM
                tab_oda_slt odaslt
            LEFT JOIN
                tab_oda_slt_logs odasltlogs ON odaslt.id = odasltlogs.slt_ref
            LEFT JOIN
                tab_oda_slt_images odasltimages ON odaslt.id = odasltimages.slt_ref
        """

    def get_records_by_shift_time(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Retrieves records from ODASLT where shift_start is within the specified time range.

        :param start_time: Start of the time range.
        :param end_time: End of the time range.
        :return: List of records as dictionaries.
        """
        import pdb
        pdb.set_trace()
        query = f"SELECT * FROM {self.table_name}" + " WHERE shift_start BETWEEN %s AND %s"
        print(f"{query=}")
        params = (start_time, end_time)

        return self._execute_query_or_update(query=query, query_type=QueryType.GET, params=params) or []

    def get_records_with_logs_and_image(self, record_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves records from ODASLT with associated logs and images. Optionally filters by record_id.

        :param record_id: Optional; ID of the record to fetch.
        :return: List of records with logs and images as dictionaries.
        """
        base_query = self._get_base_query()
        # If record_id is provided, filter by it; otherwise, return all records
        query = base_query + (f" WHERE odaslt.id = %s" if record_id is not None else "")
        params = (record_id,) if record_id is not None else None

        return self._execute_query_or_update(query=query, query_type=QueryType.GET, params=params) or []

    def get_records_by_shift_time_with_logs_and_image(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Retrieves records from ODASLT with associated logs and images where shift_start is within the specified time range.

        :param start_time: Optional; Start of the time range.
        :param end_time: Optional; End of the time range.
        :return: List of records with logs and images as dictionaries.
        """
        base_query = self._get_base_query()
        query = base_query + " WHERE odaslt.shift_start BETWEEN %s AND %s"
        params = (start_time, end_time)

        return self._execute_query_or_update(query=query, query_type=QueryType.GET, params=params) or []




class ODASLTLogsRepository(BaseRepository):
    def __init__(self):
        super().__init__(table_name='tab_oda_slt_logs')

class ODASLTImagesRepository(BaseRepository):
    def __init__(self):
        super().__init__(table_name='tab_oda_slt_images')
