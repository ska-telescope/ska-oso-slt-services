import json
import random
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from psycopg import DatabaseError
from ska_db_oda.unit_of_work.postgresunitofwork import create_connection_pool

from ska_oso_slt_services.models.metadata import _set_new_metadata, update_metadata
from ska_oso_slt_services.models.slt import SLT

skuid_entity_type = "slt"

conn_pool = create_connection_pool()



class QueryType(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


def convert_value(value):
    """
    Convert values to appropriate types for database insertion.
    """
    if isinstance(value, dict):
        return json.dumps(value)
    return value


class Postgresql:
    def __init__(self, table_name: str = None):
        """
        Initializes the Postgresql Base Class with a table name.

        :param table_name: The name of the database table.
        """
        self.pool = conn_pool
        self.table_name = table_name

    def _execute_query_or_update(
        self, query: str, query_type: QueryType, params: tuple = None
    ):
        """
        Executes a query or update operation on the database.

        :param query: The SQL query to be executed.
        :param query_type: The type of query (GET, POST, PUT, DELETE).
        :param params: Parameters to be used in the SQL query.
        :return: The result of the query if query_type is GET; otherwise, None.
        """
        try:
            with self.pool.connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    if query_type == QueryType.GET:
                        return cursor.fetchall()
                    elif query_type in {
                        QueryType.POST,
                        QueryType.PUT,
                        QueryType.DELETE,
                    }:
                        returned_id = None
                        if query_type == QueryType.POST:
                            returned_id = cursor.fetchone()
                        conn.commit()
                        return returned_id  # if returned_id else None
                    else:
                        raise ValueError(f"Unsupported query type: {query_type}")
        except (Exception, DatabaseError) as error:
            raise DatabaseError(
                f"Error executing {query_type.value} query: {query} with params:"
                f" {params}. Error: {str(error)}"
            )

    def get_records_by_id_or_by_slt_ref(
        self, record_id: Optional[int] = None, slt_ref: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves records from the table. If record_id is provided, fetches
        the specific record.

        :param record_id: Optional; ID of the record to fetch.
        :param slt_ref: Optional; slt_ref ID of the record to fetch.
        :return: List of records as dictionaries.
        """
        base_query = f"SELECT * FROM {self.table_name}"
        if record_id:
            query = base_query + (" WHERE id = %s" if record_id is not None else "")
            params = (record_id,) if record_id is not None else None
        else:
            query = base_query + (" WHERE slt_ref = %s" if slt_ref is not None else "")
            params = (slt_ref,) if slt_ref is not None else None

        return (
            self._execute_query_or_update(
                query=query, query_type=QueryType.GET, params=params
            )
            or []
        )

    def insert(self, slt_entity: Dict[str, Any]):
        """
        Inserts a new slt_entity into the table.

        :param slt_entity: Dictionary containing the slt_entity data to be inserted.
        """

        slt_entity = _set_new_metadata(slt_entity)

        if isinstance(slt_entity, SLT):

            slt_entity.shift_start = datetime.now(tz=timezone.utc)
            metadata_dict = json.loads(slt_entity.metadata.model_dump_json())

            slt_entity = json.loads(slt_entity.model_dump_json())
            slt_entity_without_metadata = {**slt_entity, **metadata_dict}
            slt_entity_without_metadata.pop("metadata")
            time_now = datetime.now().strftime("%m%d%Y")
            slt_entity_without_metadata["id"] = (
                f"{skuid_entity_type}-mvp01-{time_now}-{str(random.randint(0, 10000))}"
            )

        else:

            slt_entity_without_metadata["id"] = datetime.now(tz=timezone.utc)

        try:

            # Convert all values in the slt_entity to the appropriate types
            converted_slt_entity = {
                k: convert_value(v) for k, v in slt_entity_without_metadata.items()
            }

            columns = ", ".join(converted_slt_entity.keys())
            placeholders = ", ".join(["%s"] * len(converted_slt_entity))
            query = (
                f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders} )"
                " RETURNING id"
            )

            return self._execute_query_or_update(
                query=query,
                query_type=QueryType.POST,
                params=tuple(converted_slt_entity.values()),
            )

        except (Exception, DatabaseError) as error:
            raise DatabaseError(
                f"Error inserting slt entity into table: {self.table_name}. Error:"
                f" {str(error)}"
            )

    def update(self, slt_entity, slt_ref=None, slt_entity_id=None):

        slt_entity = update_metadata(slt_entity)

        try:

            slt_entity = {**slt_entity, **slt_entity["metadata"]}
            slt_entity.pop("metadata")

            set_clause = ", ".join([f"{col} = %s" for col in slt_entity.keys()])
            base_query = f"UPDATE {self.table_name} SET {set_clause}"

            if slt_ref:
                query = base_query + f" WHERE slt_ref = {slt_ref}"
            else:  # slt_entity
                query = base_query + " WHERE id = %s"

            converted_slt_entity = {k: convert_value(v) for k, v in slt_entity.items()}
            params = list(
                converted_slt_entity[col] for col in converted_slt_entity.keys()
            )
            params.append(slt_entity_id)

            self._execute_query_or_update(
                query=query, query_type=QueryType.PUT, params=params
            )
        except (Exception, DatabaseError) as error:
            raise DatabaseError(
                f"Error updating slt entity in table: {self.table_name}. Error:"
                f" {str(error)}"
            )

    def delete_by_id(self, record_id: int):
        """
        Deletes a record from the table by id.

        :param record_id: ID of the record to delete.
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = %s"
            params = (record_id,)

            self._execute_query_or_update(
                query=query, query_type=QueryType.DELETE, params=params
            )
        except (Exception, DatabaseError) as error:
            raise DatabaseError(
                f"Error deleting slt entity from table: {self.table_name}. Error:"
                f" {str(error)}"
            )
