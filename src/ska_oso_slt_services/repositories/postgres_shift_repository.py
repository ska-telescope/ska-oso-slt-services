import json
from datetime import datetime
from typing import List, Optional

from ska_oso_slt_services.data_access.postgres_data_acess import PostgresDataAccess, QueryType
from ska_oso_slt_services.models.data_models import Shift, Operator, ShiftLogs, Media
from ska_oso_slt_services.repositories.abstract_base import CRUDShiftRepository


class PostgresShiftRepository(CRUDShiftRepository):
    def __init__(self):
        self.postgresDataAccess = PostgresDataAccess()

    def get_shifts(self, shift_start: Optional[datetime] = None, shift_end: Optional[datetime] = None) -> List[Shift]:
        query = """
        SELECT id, shift_start, shift_end, shift_operator, shift_logs, media, annotations,
               comments, created_by, created_time, last_modified_by, last_modified_time
        FROM shifts
        """
        params = []
        if shift_start and shift_end:
            query += " WHERE shift_start >= %s AND shift_end <= %s"
            params.extend([shift_start, shift_end])
        query += " ORDER BY shift_start ASC"

        rows = self.postgresDataAccess.execute_query_or_update(query=query, params=tuple(params), query_type=QueryType.GET)

        shifts = []
        for row in rows:

            operator_data = row['shift_operator'] if row['shift_operator'] is not None else {}
            logs_data = row['shift_logs'] if row['shift_logs'] is not None else []
            media_data = row['media'] if row['media'] is not None else []
            # import pdb
            # pdb.set_trace()

            operator = Operator(**operator_data) if operator_data else None
            shift_logs = [ShiftLogs(**log) for log in logs_data] if logs_data else None
            media = [Media(**item) for item in media_data] if media_data else None

            shift = Shift(
                id=row['id'],
                shift_start=row['shift_start'],
                shift_end=row['shift_end'],
                shift_operator=operator,
                shift_logs=shift_logs,
                media=media,
                annotations=row['annotations'],
                comments=row['comments'],
                created_by=row['created_by'],
                created_time=row['created_time'],
                last_modified_by=row['last_modified_by'],
                last_modified_time=row['last_modified_time']
            )
            shifts.append(shift)

        return shifts

    def get_shift(self, shift_id: int) -> Optional[Shift]:
        query = """
        SELECT id, shift_start, shift_end, shift_operator, shift_logs, media, annotations,
               comments, created_by, created_time, last_modified_by, last_modified_time
        FROM shifts
        WHERE id = %s
        """
        params = (shift_id,)
        rows = self.postgresDataAccess.execute_query_or_update(query=query, params=params, query_type=QueryType.GET)

        if not rows:
            return None

        row = rows[0]


        operator_data = row['shift_operator'] if row['shift_operator'] is not None else {}
        logs_data = row['shift_logs'] if row['shift_logs'] is not None else []
        media_data = row['media'] if row['media'] is not None else []

        # import pdb
        # pdb.set_trace()

        operator = Operator(**operator_data) if operator_data else None
        shift_logs = [ShiftLogs(**log) for log in logs_data] if logs_data else None
        media = [Media(**item) for item in media_data] if media_data else None

        shift = Shift(
            id=row['id'],
            shift_start=row['shift_start'],
            shift_end=row['shift_end'],
            shift_operator=operator,
            shift_logs=shift_logs,
            media=media,
            annotations=row['annotations'],
            comments=row['comments'],
            created_by=row['created_by'],
            created_time=row['created_time'],
            last_modified_by=row['last_modified_by'],
            last_modified_time=row['last_modified_time']
        )

        return shift

    # def create_shift(self, shift: Shift) -> Shift:
    #     pass

    def create_shift(self, shift: Shift) -> Shift:
        query = """
        INSERT INTO shifts (shift_start, shift_end, shift_operator, shift_logs, media, annotations,
                            comments, created_by, created_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_time
        """


        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        params = (
            shift.shift_start.isoformat() if shift.shift_start else None,
            shift.shift_end.isoformat() if shift.shift_end else None,
            json.dumps(shift.shift_operator.model_dump(mode="python", exclude_unset=True), default=serialize_datetime) if shift.shift_operator else None,
            json.dumps([log.model_dump(mode="python", exclude_unset=True) for log in shift.shift_logs], default=serialize_datetime) if shift.shift_logs else None,
            json.dumps([media.model_dump(mode="python", exclude_unset=True) for media in shift.media], default=serialize_datetime) if shift.media else None,
            shift.annotations,
            shift.comments,
            shift.created_by,
            shift.created_time.isoformat() if shift.created_time else datetime.now().isoformat(),
        )

        row = self.postgresDataAccess.execute_query_or_update(query=query, params=params, query_type=QueryType.POST)

        if row:
            shift.id = row['id']
            shift.created_time = row['created_time']

        return shift

    # def update_shift(self, shift: Shift) -> Shift:
    #     pass
    def update_shift(self, shift: Shift) -> Shift:
        if not shift.id:
            raise ValueError("Shift ID is required for update operation")
        query = """
        UPDATE shifts
        SET shift_start = %s,
            shift_end = %s,
            shift_operator = %s,
            shift_logs = %s,
            media = %s,
            annotations = %s,
            comments = %s,
            last_modified_by = %s,
            last_modified_time = %s
        WHERE id = %s
        RETURNING id, last_modified_time
        """

        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        params = (
            shift.shift_start.isoformat() if shift.shift_start else None,
            shift.shift_end.isoformat() if shift.shift_end else None,
            json.dumps(shift.shift_operator.model_dump(mode="python", exclude_unset=True), default=serialize_datetime) if shift.shift_operator else None,
            json.dumps([log.model_dump(mode="python", exclude_unset=True) for log in shift.shift_logs], default=serialize_datetime) if shift.shift_logs else None,
            json.dumps([media.model_dump(mode="python", exclude_unset=True) for media in shift.media], default=serialize_datetime) if shift.media else None,
            shift.annotations,
            shift.comments,
            shift.last_modified_by,
            shift.last_modified_time.isoformat() if shift.last_modified_time else datetime.now().isoformat(),
            shift.id
        )

        row = self.postgresDataAccess.execute_query_or_update(query=query, params=params, query_type=QueryType.PUT)

        if row:
            shift.id = row['id']
            shift.last_modified_time = row['last_modified_time']

        return shift
    def delete_shift(self, id: str) -> bool:
        pass
