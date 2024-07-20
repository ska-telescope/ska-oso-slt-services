import json

from pydantic import BaseModel, Field

from ska_oso_slt_services.backend.models.metadata import Metadata


class SLTLog(BaseModel):
    """Shared Base Class for all SLT-Image Entities."""

    id: int = Field(default=None)
    slt_ref: str = None
    info: json = None
    source: str = None
    metadata: Metadata = None
