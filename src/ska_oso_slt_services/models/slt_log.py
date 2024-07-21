from typing import Dict, Optional

from pydantic import BaseModel, Field

from ska_oso_slt_services.models.metadata import Metadata


class SLTLog(BaseModel):
    """Shared Base Class for all SLT-Image Entities."""

    id: int = Field(default=None)
    slt_ref: str = None
    info: Optional[Dict[str, str]] = Field(default_factory=dict)
    source: str = None
    metadata: Optional[Metadata] = None
