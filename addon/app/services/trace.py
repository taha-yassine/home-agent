from __future__ import annotations

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from ..db import Span as SpanModel
from ..db import Trace as TraceModel
from ..models import Span, ConversationNeighbors, TraceWithSpans


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
    async def get_traces_with_spans_by_group_id(
        db: AsyncSession, group_id: str
    ) -> list[TraceWithSpans]:
        """Get all traces with their spans for a given group_id, ordered by trace start time."""
        # First, get all trace ids in the group ordered by their first span time
        first_span_subq = (
            select(
                SpanModel.trace_id.label("trace_id"),
                func.min(SpanModel.started_at).label("started_at"),
                func.max(SpanModel.ended_at).label("ended_at"),
            )
            .join(TraceModel, TraceModel.id == SpanModel.trace_id)
            .where(TraceModel.group_id == group_id)
            .group_by(SpanModel.trace_id)
            .subquery()
        )

        # Fetch trace ordering first
        ordered_traces = (
            await db.execute(select(first_span_subq).order_by(first_span_subq.c.started_at.asc()))
        ).all()

        trace_with_spans: list[TraceWithSpans] = []
        for row in ordered_traces:
            trace_id = row.trace_id
            started_at = row.started_at
            ended_at = row.ended_at

            spans_result = await db.execute(
                select(SpanModel)
                .where(SpanModel.trace_id == trace_id)
                .order_by(SpanModel.started_at.asc())
            )
            spans_models = spans_result.scalars().all()
            spans = [Span.model_validate(s) for s in spans_models]

            trace_with_spans.append(
                TraceWithSpans(
                    trace_id=trace_id,
                    started_at=started_at,
                    ended_at=ended_at,
                    spans=spans,
                )
            )

        return trace_with_spans

    @staticmethod
    async def get_group_neighbors(db: AsyncSession, group_id: str) -> ConversationNeighbors:
        """Get previous and next group_ids by ordering groups via latest generation span time."""
        # Rank each trace by latest generation span, then get a timestamp per group (max over traces)
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

        group_latest_stmt = (
            select(
                TraceModel.group_id.label("group_id"),
                func.max(latest_generation_span.started_at).label("latest_time"),
            )
            .join(latest_generation_span, latest_generation_span.trace_id == TraceModel.id)
            .where(ranked_spans_subq.c.row_num == 1)
            .group_by(TraceModel.group_id)
        ).subquery()

        # get current group's time
        current_time_stmt = select(group_latest_stmt.c.latest_time).where(
            group_latest_stmt.c.group_id == group_id
        )
        current_time = (await db.execute(current_time_stmt)).scalar_one_or_none()
        if not current_time:
            return ConversationNeighbors(previous=None, next=None)

        prev_stmt = (
            select(group_latest_stmt.c.group_id)
            .where(group_latest_stmt.c.latest_time < current_time)
            .order_by(desc(group_latest_stmt.c.latest_time))
            .limit(1)
        )
        next_stmt = (
            select(group_latest_stmt.c.group_id)
            .where(group_latest_stmt.c.latest_time > current_time)
            .order_by(asc(group_latest_stmt.c.latest_time))
            .limit(1)
        )

        prev_gid = (await db.execute(prev_stmt)).scalar_one_or_none()
        next_gid = (await db.execute(next_stmt)).scalar_one_or_none()

        return ConversationNeighbors(previous=prev_gid, next=next_gid)