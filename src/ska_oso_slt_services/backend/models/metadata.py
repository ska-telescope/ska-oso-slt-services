from datetime import datetime, timezone
from typing import Optional

from pydantic import AwareDatetime, Field


class Metadata:
    """Represents metadata about other entities."""

    created_by: Optional[str] = None
    created_on: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_modified_by: Optional[str] = None
    last_modified_on: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
