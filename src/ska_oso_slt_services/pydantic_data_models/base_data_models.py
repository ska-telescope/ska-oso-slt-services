from typing import Optional

from pydantic import BaseModel, field_validator
from datetime import datetime


class BaseModelWithTimestamp(BaseModel):
    created_on: Optional[datetime] = None
    created_by: Optional[str] = None
    last_modified_on: Optional[datetime] = None
    last_modified_by: Optional[str] = None
    id: Optional[int] = None

    @field_validator('id', mode='before')
    def set_id(cls, v):
        return v or int(datetime.now().timestamp())

