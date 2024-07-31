from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Operator(BaseModel):
    name: Optional[str] = None

class Media(BaseModel):
    type: Optional[str] = None
    path: Optional[str] = None

class ShiftLogs(BaseModel):
    info: Optional[dict] = None
    source: Optional[str] = None
    log_time: Optional[datetime] = None

class Shift(BaseModel):
    id: Optional[int] = None
    shift_start: Optional[datetime] = None
    shift_end: Optional[datetime] = None
    shift_operator: Optional[Operator] = None
    shift_logs: Optional[List[ShiftLogs]] = None
    media: Optional[List[Media]] = None
    annotations: Optional[str] = None
    comments: Optional[str] = None
    created_by: Optional[str] = None
    created_time: Optional[datetime] = None
    last_modified_by: Optional[str] = None
    last_modified_time: Optional[datetime] = None

