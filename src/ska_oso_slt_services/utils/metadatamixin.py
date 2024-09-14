import logging
from abc import abstractmethod
from copy import deepcopy
from datetime import datetime, timezone
from typing import Dict, Generic, List, Optional, TypeVar

from ska_oso_slt_services.models.shiftmodels import Metadata

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def update_metadata(shift: T, last_modified_by: Optional[str] = None) -> T:
    """Updates the metadata of a copy of the entity

    If a version of the entity already exists in the SLT, the previous version will be incremented and the last modified fields updated.

    If a version does not already exist, a new metadata block will be created.

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param last_modified_by: The user performing the operation
    :type last_modified_by: str
    :param is_entity_update: True if called from any put API sbd, sbi or eb else False
    :return: A copy of the entity with the updated metadata to be persisted
    :rtype: An SLT entity which contains Metadata
    """
    # This is a temporary measure to indicate that the last_modified_by field will be stored in the database,
    # but currently it is uncertain which layer of the architecture this will come from, and
    # eg whether is will be set in the entity json or extracted from HTTP headers

    if last_modified_by is None:
        last_modified_by = "DefaultUser"
    updated_entity = deepcopy(shift)
    updated_entity.metadata.last_modified_on = datetime.now(tz=timezone.utc)
    updated_entity.metadata.last_modified_by = last_modified_by
    return updated_entity


def set_new_metadata(shift: T, created_by: Optional[str] = None) -> T:
    """
    Set the metadata for a new entity, with version 1, created_on and last_modified_on set to the current time
    and created_on and last_modified_by both set to the same value

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param created_by: The user performing the operation
    :type created_by: str
    :return: A copy of the entity with the new metadata to be persisted
    """
    # This is a temporary measure to indicate that the last_modified_by field will be stored in the database,
    # but currently it is uncertain which layer of the architecture this will come from, and
    # eg whether is will be set in the entity json or extracted from HTTP headers
    if created_by is None:
        created_by = "DefaultUser"

    now = datetime.now(timezone.utc)
    # TODO this is while we still are working out the generated code issues, and the new entites
    #  use the generated Metadata while the SBDefinition is the old SLT version
    metadata_cls = Metadata
    shift.metadata = metadata_cls(
        created_on=now,
        created_by=created_by,
        last_modified_on=now,
        last_modified_by=created_by,
    )
    return shift
