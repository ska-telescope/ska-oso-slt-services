from datetime import datetime, timezone
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field

from ska_oso_slt_services.models.metadata import Metadata


class SLT(BaseModel):
    """Shared Base Class for all SLT Entities."""

    id: str = Field(default=None)
    comments: str = None
    shift_start: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    shift_end: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    annotation: str = None
    metadata: Optional[Metadata] = None
