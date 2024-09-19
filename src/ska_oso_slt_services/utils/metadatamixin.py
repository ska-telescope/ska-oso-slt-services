import logging
from datetime import datetime, timezone
from typing import Optional, TypeVar

from ska_oso_slt_services.models.shiftmodels import Metadata

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def update_metadata(
    shift: T, metadata: Metadata, last_modified_by: Optional[str] = None
) -> T:
    """Updates the metadata of a copy of the entity

    If a version of the entity already exists in the SLT, the previous
    version will be incremented and the last modified fields updated.

    If a version does not already exist, a new metadata block will be created.

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param last_modified_by: The user performing the operation
    :type last_modified_by: str
    :param is_entity_update: True if called from any put API sbd, sbi or eb else False
    :return: A copy of the entity with the updated metadata to be persisted
    :rtype: An SLT entity which contains Metadata
    """

    if metadata.created_on and metadata.created_by:
        metadata_cls = Metadata
        shift.metadata = metadata_cls(
            created_on=metadata.created_on,
            created_by=metadata.created_by,
            last_modified_on=datetime.now(timezone.utc),
            last_modified_by=last_modified_by,
        )
    return shift


def set_new_metadata(shift: T, created_by: Optional[str] = None) -> T:
    """
    Set the metadata for a new entity, with version 1,
    created_on and last_modified_on set to the current time
    and created_on and last_modified_by both set to the same value

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param created_by: The user performing the operation
    :type created_by: str
    :return: A copy of the entity with the new metadata to be persisted
    """
    if created_by is None:
        created_by = "DefaultUser"

    now = datetime.now(timezone.utc)

    metadata_cls = Metadata
    shift.metadata = metadata_cls(
        created_on=now,
        created_by=created_by,
        last_modified_on=now,
        last_modified_by=created_by,
    )
    return shift
