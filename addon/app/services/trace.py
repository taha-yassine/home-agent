from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Span as SpanModel
from ..models import Span, TraceNeighbors


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

    @staticmethod
    async def get_trace_neighbors(db: AsyncSession, trace_id: str) -> TraceNeighbors:
        """Get the previous and next traces for a given trace."""
        ranked_spans_subq = (
            select(
                SpanModel,
                func.row_number()
                .over(
                    partition_by=SpanModel.trace_id,
                    order_by=desc(SpanModel.started_at),
                )
                .label("row_num"),
            )
            .where(SpanModel.span_type == "generation")
            .subquery("ranked_spans")
        )

        latest_generation_span = aliased(SpanModel, ranked_spans_subq)

        current_trace_time_stmt = (
            select(latest_generation_span.started_at)
            .where(latest_generation_span.trace_id == trace_id)
            .where(ranked_spans_subq.c.row_num == 1)
        )
        current_trace_time_result = await db.execute(current_trace_time_stmt)
        current_trace_time = current_trace_time_result.scalar_one_or_none()

        if not current_trace_time:
            return TraceNeighbors(previous=None, next=None)

        previous_trace_stmt = (
            select(latest_generation_span.trace_id)
            .where(ranked_spans_subq.c.row_num == 1)
            .where(latest_generation_span.started_at < current_trace_time)
            .order_by(desc(latest_generation_span.started_at))
            .limit(1)
        )
        previous_trace_id = (await db.execute(previous_trace_stmt)).scalar_one_or_none()

        next_trace_stmt = (
            select(latest_generation_span.trace_id)
            .where(ranked_spans_subq.c.row_num == 1)
            .where(latest_generation_span.started_at > current_trace_time)
            .order_by(asc(latest_generation_span.started_at))
            .limit(1)
        )
        next_trace_id = (await db.execute(next_trace_stmt)).scalar_one_or_none()

        return TraceNeighbors(previous=previous_trace_id, next=next_trace_id) 