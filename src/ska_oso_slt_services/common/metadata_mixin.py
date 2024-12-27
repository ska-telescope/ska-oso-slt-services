import logging
from typing import Optional, TypeVar

from ska_oso_slt_services.common.utils import get_datetime_for_timezone
from ska_oso_slt_services.domain.shift_models import Metadata

LOGGER = logging.getLogger(__name__)

T = TypeVar("T")
U = TypeVar("U")


def update_metadata(
    entity: T, metadata: Metadata, last_modified_by: Optional[str] = None
) -> T:
    """Updates the metadata of a copy of the entity
    :param entity: Old entity object with metadata if user not provided
                  metadata.
    :type entity: entity object
    :param metadata: old metadata stored in db
    :type metadata: str
    :param last_modified_by: The user performing the operation
    :type last_modified_by: str
    :return: A copy of the entity with the updated metadata to be persisted
    """

    if last_modified_by is None:
        last_modified_by = metadata.last_modified_by

    if metadata.created_on and metadata.created_by:
        metadata_cls = Metadata
        entity.metadata = metadata_cls(
            created_on=metadata.created_on,
            created_by=metadata.created_by,
            last_modified_on=get_datetime_for_timezone("UTC"),
            last_modified_by=last_modified_by,
        )
    return entity


def set_new_metadata(entity: T, created_by: Optional[str] = None) -> T:
    """
    Set the metadata for a new shift, with
    created_on and last_modified_on set to the current time
    and created_on and last_modified_by both set to the same value

    :param entity: An SLT entity submitted to be persisted
    :type entity: An SLT entity which contains Metadata
    :param created_by: The user performing the operation
    :type created_by: str
    :return: A copy of the shift with the new metadata to be persisted
    """
    if created_by is None:
        created_by = "DefaultUser"

    now = get_datetime_for_timezone("UTC")

    metadata_cls = Metadata
    entity.metadata = metadata_cls(
        created_on=now,
        created_by=created_by,
        last_modified_on=now,
        last_modified_by=created_by,
    )
    return entity
