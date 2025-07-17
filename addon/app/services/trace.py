from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Span as SpanModel
from ..models import Span


class TraceService:
    @staticmethod
    async def get_spans_by_trace_id(db: AsyncSession, trace_id: str) -> list[Span]:
        """Get all spans for a given trace."""
        result = await db.execute(
            select(SpanModel)
            .filter(SpanModel.trace_id == trace_id)
            .order_by(SpanModel.started_at.asc())
        )
        spans = result.scalars().all()
        return [Span.model_validate(span) for span in spans] 