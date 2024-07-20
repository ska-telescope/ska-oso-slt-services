from datetime import datetime, timezone

from pydantic import AwareDatetime, BaseModel, Field

from ska_oso_slt_services.backend.models.metadata import Metadata


class SLTObject(BaseModel):
    """Shared Base Class for all SLT Entities."""

    id: int = Field(default=None)
    comments: str = None
    shift_start: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    shift_end: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    annotation: str = None
    metadata: Metadata = None
