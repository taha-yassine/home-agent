from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

class Span(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    trace_id: str
    parent_id: Optional[str]
    started_at: datetime
    ended_at: datetime
    span_type: str
    span_data: dict
    error: Optional[dict]
