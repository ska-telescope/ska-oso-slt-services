import json
from datetime import datetime
from typing import List, Optional

from ska_oso_slt_services.data_access.postgres_data_acess import (
    PostgresDataAccess,
    QueryType,
)
from ska_oso_slt_services.models.data_models import Media, Operator, Shift, ShiftLogs
from ska_oso_slt_services.repositories.abstract_base import CRUDShiftRepository


class PostgresShiftRepository(CRUDShiftRepository):
    """
    Implementation of CRUDShiftRepository for PostgreSQL.

    This class provides concrete implementations of the CRUD operations defined in the
    CRUDShiftRepository abstract base class, specifically for interacting with a
    PostgreSQL database.
    """

    def __init__(self):
        self.postgresDataAccess = PostgresDataAccess()

    def get_shifts(
        self,
        shift_start: Optional[datetime] = None,
        shift_end: Optional[datetime] = None,
    ) -> List[Shift]:
        """
        Retrieve a list of shifts within the specified start and end times.

        :param shift_start Optional[datetime]: The start time to filter shifts. If
        None, no start time filter is applied.
        :param shift_end Optional[datetime]: The end time to filter shifts. If None,
         no end time filter is applied.

        :returns: A list of Shift objects that fall within the specified time range.
        :raises: NotImplementedError if the method is not implemented by a subclass.
        """

        query = """
        SELECT id,shift_id, shift_start, shift_end, shift_operator, shift_logs, media, 
        annotations, comments, created_by, created_time, last_modified_by,
         last_modified_time FROM tab_oda_slt
        """  # noqa: W291
        params = []
        if shift_start and shift_end:
            query += " WHERE shift_start >= %s AND shift_end <= %s"
            params.extend([shift_start, shift_end])
        query += " ORDER BY shift_start ASC"

        rows = self.postgresDataAccess.execute_query_or_update(
            query=query, params=tuple(params), query_type=QueryType.GET
        )

        shifts = []
        for row in rows:

            operator_data = (
                row["shift_operator"] if row["shift_operator"] is not None else {}
            )
            logs_data = row["shift_logs"] if row["shift_logs"] is not None else []
            media_data = row["media"] if row["media"] is not None else []

            operator = Operator(**operator_data) if operator_data else None
            shift_logs = [ShiftLogs(**log) for log in logs_data] if logs_data else None
            media = [Media(**item) for item in media_data] if media_data else None

            shift = Shift(
                id=row["id"],
                shift_id=row["shift_id"],
                shift_start=row["shift_start"],
                shift_end=row["shift_end"],
                shift_operator=operator,
                shift_logs=shift_logs,
                media=media,
                annotations=row["annotations"],
                comments=row["comments"],
                created_by=row["created_by"],
                created_time=row["created_time"],
                last_modified_by=row["last_modified_by"],
                last_modified_time=row["last_modified_time"],
            )
            shifts.append(shift)

        return shifts

    def get_shift(self, shift_id: int) -> Optional[Shift]:
        """
        Retrieve a single shift by its unique identifier.

        :param shift_id int: The unique identifier of the shift.

        :returns: The Shift object with the specified identifier, or None if not found.
        :raises: NotImplementedError if the method is not implemented by a subclass.
        """

        query = """
        SELECT id, shift_id, shift_start, shift_end, shift_operator, shift_logs, media,
         annotations,
               comments, created_by, created_time, last_modified_by, last_modified_time
        FROM tab_oda_slt
        WHERE id = %s
        """  # noqa: W291

        # import pdb
        # pdb.set_trace()

        params = (shift_id,)
        rows = self.postgresDataAccess.execute_query_or_update(query=query, params=params, query_type=QueryType.GET)

        if not rows:
            return None

        row = rows[0]

        operator_data = (
            row["shift_operator"] if row["shift_operator"] is not None else {}
        )
        logs_data = row["shift_logs"] if row["shift_logs"] is not None else []
        media_data = row["media"] if row["media"] is not None else []

        operator = Operator(**operator_data) if operator_data else None
        shift_logs = [ShiftLogs(**log) for log in logs_data] if logs_data else None
        media = [Media(**item) for item in media_data] if media_data else None

        shift = Shift(
            id=row["id"],
            shift_id=row["shift_id"],
            shift_start=row["shift_start"],
            shift_end=row["shift_end"],
            shift_operator=operator,
            shift_logs=shift_logs,
            media=media,
            annotations=row["annotations"],
            comments=row["comments"],
            created_by=row["created_by"],
            created_time=row["created_time"],
            last_modified_by=row["last_modified_by"],
            last_modified_time=row["last_modified_time"],
        )

        return shift

    def create_shift(self, shift: Shift) -> Shift:
        """
        Create a new shift.

        :param shift Shift: The Shift object to be created.

        :returns: The created Shift object with the assigned identifier.
        :raises: NotImplementedError if the method is not implemented by a subclass.
        """

        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        shift_data = shift.model_dump(exclude_unset=True, mode="python")

        columns = []
        values = []
        params = []

        for field, value in shift_data.items():
            columns.append(field)
            values.append("%s")

            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, list) and field in ["shift_logs", "media"]:

                serialized_items = []
                for item in value:
                    if isinstance(item, dict):
                        serialized_items.append(item)
                    else:
                        serialized_items.append(
                            item.model_dump(exclude_unset=True, mode="python")
                        )
                value = json.dumps(serialized_items, default=serialize_datetime)
            elif isinstance(value, dict) and field == "shift_operator":
                value = json.dumps(value, default=serialize_datetime)

            params.append(value)

        if "created_time" not in shift_data:
            columns.append("created_time")
            values.append("%s")
            params.append(datetime.now().isoformat())

        if "shift_start" not in shift_data:
            columns.append("shift_start")
            values.append("%s")
            params.append(datetime.now().isoformat())

        columns_clause = ", ".join(columns)
        values_clause = ", ".join(values)
        returning_clause = ", ".join(["id"] + columns)
        query = f"""
        INSERT INTO tab_oda_slt ({columns_clause})
        VALUES ({values_clause})
        RETURNING {returning_clause}
        """

        row = self.postgresDataAccess.execute_query_or_update(
            query=query, params=tuple(params), query_type=QueryType.POST
        )

        if row:
            created_shift = Shift(**row)

        return created_shift

    def update_shift(self, shift: Shift) -> Shift:
        """
        Update an existing shift.

        :param shift Shift: The Shift object with updated information.

        :returns: The updated Shift object.
        :raises: ValueError if the shift ID is not provided.
        :raises: NotImplementedError if the method is not implemented by a subclass.
        """
        if not shift.id:
            raise ValueError("Shift ID is required for update operation")

        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError("Type not serializable")

        shift_data = shift.model_dump(exclude_unset=True, mode="python")

        shift_id = shift_data.pop("id", None)

        set_clauses = []
        params = []

        for field, value in shift_data.items():
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, list) and field in ["shift_logs", "media"]:

                serialized_items = []
                for item in value:
                    if isinstance(item, dict):
                        serialized_items.append(item)
                    else:
                        serialized_items.append(
                            item.model_dump(exclude_unset=True, mode="python")
                        )
                value = json.dumps(serialized_items, default=serialize_datetime)
            elif isinstance(value, dict) and field == "shift_operator":
                value = json.dumps(value, default=serialize_datetime)

            set_clauses.append(f"{field} = %s")
            params.append(value)

        params.append(shift_id)

        set_clause = ", ".join(set_clauses)
        returning_clause = ", ".join(["id"] + [field for field in shift_data.keys()])
        query = f"""
        UPDATE tab_oda_slt
        SET {set_clause}
        WHERE id = %s
        RETURNING {returning_clause}
        """

        row = self.postgresDataAccess.execute_query_or_update(
            query=query, params=tuple(params), query_type=QueryType.PUT
        )

        if row:
            shift.id = row["id"]
            shift.last_modified_time = row["last_modified_time"]

        return shift

    def delete_shift(self, id: str) -> bool:
        pass




    def get_oda_data(self,filter_date):
        #query for EB
        #        ebs = uow.ebs.query(maybe_qry_params)
        eb_query = f"""SELECT eb_id, info,sbd_id,sbi_id,sbd_version,version,created_on,created_by,last_modified_on,last_modified_by
                    FROM tab_oda_eb
                    WHERE last_modified_on >= %s
        """
        eb_params = [filter_date]
        eb_rows = self.postgresDataAccess.execute_query_or_update(
            query=eb_query, params=tuple(eb_params), query_type=QueryType.GET
        )
        print(f"\n\n\n\n========================== Printing Data =============================\n{eb_rows} {type(eb_rows[0])}")

        info = {}
        for eb in eb_rows:
            # sbi_status_query = """
            #     SELECT sbi_ref, previous_status, current_status, version, created_on, created_by, last_modified_on, last_modified_by
            #     FROM tab_oda_sbi_status_history
            #     WHERE sbi_ref = sbi-t0001-20240810-00003
            #     ORDER BY version DESC, id DESC
            #     LIMIT 1
            # """

            sbi_status_query = """
                            SELECT current_status
                            FROM tab_oda_sbi_status_history
                            WHERE sbi_ref = %s
                            ORDER BY version DESC, id DESC 
                            LIMIT 1
                        """
            sbi_status_params = [eb["sbi_id"]]
            sbi_current_status = self.postgresDataAccess.execute_query_or_update(
                query=sbi_status_query, params=tuple(sbi_status_params), query_type=QueryType.GET
            )
            info[eb["eb_id"]] = eb["info"]
            info[eb["eb_id"]]["sbi_status"] = sbi_current_status[0]["current_status"]
            print(f"\n\n\n\n========================== Printing sbi_current_status Data =============================\n{sbi_current_status} {type(sbi_current_status[0])}")

            #sbi_current_status =

        # #query for SB
        # query = """"""
        return info

def update_shift_log():
    pass

#
# class POStgresODARepositiry
#     pass

