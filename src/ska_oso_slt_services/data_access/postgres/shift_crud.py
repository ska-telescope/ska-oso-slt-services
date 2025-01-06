"""Database operations for handling shift-related database interactions.

This module provides a DBCrud class that handles various database operations
for shift-related entities including creation, retrieval, and updates.
"""

import logging
from typing import Any, List, Optional, TypeVar, Union

from ska_oso_slt_services.common.error_handling import NotFoundError
from ska_oso_slt_services.data_access.postgres.base_mapping import BaseMapping
from ska_oso_slt_services.data_access.postgres.execute_query import PostgresDataAccess
from ska_oso_slt_services.data_access.postgres.mapping_factory import (
    TableMappingFactory,
)
from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    insert_query,
    select_by_date_query,
    select_by_shift_params,
    select_latest_query,
    select_latest_shift_query,
    select_logs_by_status,
    select_metadata_query,
    update_query,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DBCrud:
    """Class for handling database CRUD operations.

    This class provides methods for Create, Read, Update operations
    on database entities related to shifts and their associated data."""

    def __init__(self) -> None:
        """Initialize DatabaseOperations with a PostgreSQL data access instance."""
        self.data_access = PostgresDataAccess()

    def update_entity(self, entity_id: Union[int, str], entity: T, db: Any) -> None:
        """Update an entity in the database.

        Args:
            entity_id: The ID of the entity to update
            entity: The entity object containing updated data
            db: Database connection instance

        Raises:
            Exception: If database update operation fails
        """
        table_details = self._get_table_details(entity)
        query, params = update_query(
            entity_id=entity_id, table_details=table_details, entity=entity
        )
        db.update(query, params)

    def insert_entity(self, entity: T, db: Any) -> int:
        """Insert an entity into the database.

        Args:
            entity: The entity object to insert
            db: Database connection instance

        Returns:
            int: ID of the newly created entity

        Raises:
            Exception: If database insert operation fails
        """
        table_details = self._get_table_details(entity)
        query, params = insert_query(table_details=table_details, entity=entity)
        return db.insert(query, params)

    def get_entity(
        self, entity: T, db: Any, metadata: bool = False, filters: Optional[dict] = None
    ) -> Optional[T]:
        """Get an entity from the database.

        Args:
            entity: Type of entity to retrieve
            db: Database connection instance
            metadata: Flag to indicate if metadata should be retrieved
            filters: Optional filter conditions for the query

        Returns:
            Optional[T]: The retrieved entity or None if not found

        Raises:
            Exception: If database query fails
        """
        table_details = self._get_table_details(entity)
        if metadata:
            query, params = select_metadata_query(
                table_details=table_details, entity_id=filters["entity_id"]
            )
        else:
            query, params = select_latest_query(
                table_details=table_details, filters=filters
            )

        return db.get_one(query=query, params=params)

    def get_latest_entity(self, entity: T, db: Any) -> Optional[T]:
        """Get the latest entity from the database.

        Args:
            entity: Type of entity to retrieve
            db: Database connection instance
            filters: Optional filter conditions for the query

        Returns:
            Optional[T]: The latest entity or None if not found

        Raises:
            Exception: If database query fails
        """
        table_details = self._get_table_details(entity)
        query, params = select_latest_shift_query(table_details=table_details)
        return db.get_one(query=query, params=params)

    def get_entities(
        self,
        entity: T,
        db: Any,
        oda_entities: Optional[Any] = None,
        entity_status: Optional[Any] = None,
        match_type: Optional[Any] = None,
        filters: Optional[dict] = None,
    ) -> List[T]:
        """Get multiple entities from the database based on various criteria.

        Args:
            entity: Type of entity to retrieve
            db: Database connection instance
            oda_entities: Optional ODA entities for filtering
            entity_status: Optional status filter
            match_type: Optional match type for filtering
            filters: Optional additional filter conditions

        Returns:
            List[T]: List of retrieved entities matching the criteria

        Raises:
            NotFoundError: If required match_type is missing
            Exception: If database query fails
        """
        try:
            query, params = self._build_entities_query(
                entity, oda_entities, entity_status, match_type, filters
            )
            return db.get(query=query, params=params)
        except Exception as e:
            logger.error(  # pylint: disable=W1203
                f"Error retrieving entities: {str(e)}"
            )  # pylint: disable=I0021
            raise NotFoundError("Select match_type for required selection types") from e

    def _build_entities_query(
        self,
        entity: T,
        oda_entities: Optional[Any],
        entity_status: Optional[Any],
        match_type: Optional[Any],
        filters: Optional[dict],
    ) -> tuple[str, list]:
        """Build the appropriate query for retrieving
            entities based on provided criteria.

        Args:
            entity: The entity type to query for
            oda_entities: Optional ODA entities for filtering
            entity_status: Optional status filter
            match_type: Optional match type for filtering
            filters: Optional additional filter conditions

        Returns:
            tuple[str, list]: Query string and parameters
        """
        table_details = self._get_table_details(entity)

        if (
            hasattr(entity, "shift_start")
            and entity.shift_start
            and hasattr(entity, "shift_end")
            and entity.shift_end
        ):
            return select_by_date_query(table_details, entity)

        if entity_status and entity_status.sbi_status:
            return select_logs_by_status(table_details, entity_status, "sbi_status")

        if oda_entities and (oda_entities.sbi_id or oda_entities.eb_id):
            return select_logs_by_status(
                table_details, entity_filter=oda_entities, match_type=match_type
            )

        if (
            (hasattr(entity, "shift_id") and entity.shift_id)
            or (hasattr(entity, "shift_operator") and entity.shift_operator)
            and match_type
            and match_type.dict()["match_type"]
        ):
            return select_by_shift_params(table_details, entity, match_type)

        return select_latest_query(table_details, filters)

    def _get_table_details(self, entity: T) -> BaseMapping:
        """Get table mapping details for the given entity.

        Args:
            entity: The entity to get mapping details for

        Returns:
            BaseMapping: The mapping class for the entity's table
        """
        return TableMappingFactory.create_mapping(entity)
