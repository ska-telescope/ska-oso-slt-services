"""Database operations for handling database interactions."""

import logging
from typing import Any, Tuple, Optional, Dict, List, Union

from psycopg2 import sql

from ska_oso_slt_services.data_access.postgres.sqlqueries import (
    insert_query,
    select_by_date_query,
    select_by_shift_params,
    select_latest_query,
    select_logs_by_status,
    select_metadata_query,
    update_query,
)

from .mapping_factory import TableMappingFactory, MappingType
from .execute_query import PostgresDataAccess

from ska_oso_slt_services.domain.shift_models import (
    EntityFilter,
    MatchType,
    Media,
    Metadata,
    SbiEntityStatus,
    Shift,
    ShiftAnnotation,
    ShiftComment,
    ShiftLogComment,
    ShiftLogs,
    ShiftBaseClass
)

logger = logging.getLogger(__name__)

class DBCrud:
    """Class for handling database operations."""

    def __init__(self):
        """Initialize DatabaseOperations."""
        self.data_access = PostgresDataAccess()

    def update_entity(self, entity_id: int, entity: Any, db:Any) -> None:
        """Update an entity in the database.
        
        Args:
            entity_id: The ID of the entity to update
            entity: The entity object containing updated data
        """
        table_details = self._get_table_details(entity)
        query, params = update_query(
            entity_id=entity_id, table_details=table_details, entity=entity
        )

        db.update(query, params)

    def insert_entity(self, entity: Any, db:Any) -> None:
        """Insert an entity into the database.
        
        Args:
            entity: The entity object to insert
        """
        table_details = self._get_table_details(entity)

        query, params = insert_query(table_details=table_details, entity=entity)
        id_created = db.insert(query, params)
        return id_created

    def get_entity(self, entity: Any, db,  metadata=False, filters=None) -> Any:
        """Get an entity from the database.
        
        Args:
            entity_type: Type of entity to retrieve
            **filters: Filter conditions for the query
        
        Returns:
            The retrieved entity
        """
        
        table_details = self._get_table_details(entity)
        
        if metadata is True:
            query, params = select_metadata_query(
            table_details=table_details,
            filters=filters,
        )
        else:
            query, params = select_latest_query(table_details=table_details, filters=filters)
        results = db.get_one(query=query, params=params)
        
        return results
    
    def get_entities(self, entity: Any, db, oda_entities=None, entity_status=None,  match_type=None, filters=None) -> List[Any]:
        """Get entities from the database.

        Args:
            entity_type: Type of entity to retrieve
            **filters: Filter conditions for the query

        Returns:
            The retrieved entities
        """
        table_details = self._get_table_details(entity)
        if hasattr(entity, 'shift_start') and entity.shift_start and hasattr(entity, 'shift_end') and entity.shift_end:
            query, params = select_by_date_query(table_details, entity)

        elif entity_status and entity_status.sbi_status:
            query, params = select_logs_by_status(
                table_details, entity_status, "sbi_status"
            )
        elif oda_entities and (oda_entities.sbi_id or oda_entities.eb_id):
            query, params = select_logs_by_status(
                table_details, entity_filter=oda_entities, match_type=match_type
            )
        elif (hasattr(entity, 'shift_id') and entity.shift_id) or (hasattr(entity, 'shift_operator') and entity.shift_operator) and match_type.dict()[
            "match_type"
        ]:
            query, params = select_by_shift_params(
                table_details, entity, match_type
            )
        else:
            query, params = select_latest_query(table_details, filters)
        results = db.get(query=query, params=params)
        return results

    def _get_mapping_type(self, entity: Any) -> MappingType:
        """Get the mapping type for an entity.
        
        Args:
            entity: The entity to get mapping type for
        
        Returns:
            The corresponding MappingType
        """
        if isinstance(entity, Shift):
            return MappingType.SHIFT
        if isinstance(entity, ShiftBaseClass):
            return MappingType.SHIFT_BASE_CLASS
        elif isinstance(entity, ShiftLogComment):
            return MappingType.SHIFT_LOG_COMMENT
        elif isinstance(entity, ShiftComment):
            return MappingType.SHIFT_COMMENT
        elif isinstance(entity, ShiftAnnotation):
            return MappingType.SHIFT_ANNOTATION
        else:
            raise ValueError(f"Unknown entity type: {type(entity)}")
        
    def _get_table_details(self, entity):
        mapping_type = self._get_mapping_type(entity)
        TableMappingFactory.create_mapping(mapping_type)
        mapping = TableMappingFactory.get_mapping_class(mapping_type)
        return mapping()