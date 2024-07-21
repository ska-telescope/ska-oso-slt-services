from typing import Optional

from pydantic import BaseModel, Field

from ska_oso_slt_services.models.metadata import Metadata


class SLTImage(BaseModel):
    """Shared Base Class for all SLT-Image Entities."""

    id: Optional[int] = Field(default=None)
    slt_ref: str = None
    image_path: str = None
    metadata: Optional[Metadata] = None
