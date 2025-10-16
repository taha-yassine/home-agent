from __future__ import annotations

from datetime import datetime
from typing import Optional, List

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


class ConversationNeighbors(BaseModel):
    model_config = {"extra": "forbid"}

    previous: str | None = None
    next: str | None = None


class TraceWithSpans(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trace_id: str
    started_at: datetime
    ended_at: datetime
    spans: List[Span]


class ConversationTracesResponse(BaseModel):
    model_config = {"extra": "forbid"}

    group_id: str
    traces: List[TraceWithSpans]