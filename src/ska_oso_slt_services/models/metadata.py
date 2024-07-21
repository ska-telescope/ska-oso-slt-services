from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional, TypeVar

from pydantic import AwareDatetime, BaseModel, Field

T = TypeVar("T")


class Metadata(BaseModel):
    """Represents metadata about SLT entities."""

    created_by: Optional[str] = None
    created_on: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_modified_by: Optional[str] = None
    last_modified_on: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


def update_metadata(
    entity: T,
    last_modified_by: Optional[str] = None,
) -> T:
    """Updates the metadata of a copy of the entity

    If a version of the entity already exists in the SLT, the previous version will be
    incremented and the last modified fields updated.

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param last_modified_by: The user performing the operation
    :type last_modified_by: str
    :param is_entity_update: True if called from any put API sbd, sbi or eb else False
    :return: A copy of the entity with the updated metadata to be persisted
    :rtype: An SLT entity which contains Metadata
    """

    if last_modified_by is None:
        last_modified_by = "DefaultUser"

    updated_entity = deepcopy(entity)

    updated_entity.metadata.version = entity.metadata.version

    updated_entity.metadata.last_modified_on = datetime.now(tz=timezone.utc)
    updated_entity.metadata.last_modified_by = last_modified_by

    return updated_entity


def _set_new_metadata(entity: T, created_by: Optional[str] = None) -> T:
    """
    Set the metadata for a new SLT entity, created_on and last_modified_on set to
    the current time and created_on and last_modified_by both set to the same value

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param created_by: The user performing the operation
    :type created_by: str
    :return: A copy of the entity with the new metadata to be persisted
    """

    if created_by is None:
        created_by = "DefaultUser"

    entity = deepcopy(entity)
    now = datetime.now(tz=timezone.utc)

    entity.metadata = Metadata(
        created_on=now,
        created_by=created_by,
        last_modified_on=now,
        last_modified_by=created_by,
    )

    return entity
