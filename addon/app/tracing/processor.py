import json
from agents.tracing.processor_interface import TracingExporter
from agents import Span, Trace
from typing import Any
from datetime import datetime
from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker

from ..db.models import Span as SpanModel
from ..db.models import Trace as TraceModel


class HASpanExporter(TracingExporter):
    def __init__(self, db_sync_engine: Engine):
        self.db_sync_engine = db_sync_engine

    def export(self, items: list[Trace | Span[Any]]) -> None:
        if not items:
            return
        
        session = sessionmaker(bind=self.db_sync_engine)
        
        data = [item.export() for item in items if item.export()]

        with session() as session:

            for item in data:
                if not isinstance(item, dict):
                    continue

                if item.get("object") == "trace":
                    trace = TraceModel(
                        id=item.get("id"),
                        workflow_name=item.get("workflow_name"),
                        group_id=item.get("group_id"),
                    )
                    session.add(trace)
                
                elif item.get("object") == "trace.span":
                    trace_id = item.get("trace_id")
                    if not trace_id:
                        continue

                    trace = session.query(TraceModel).filter_by(id=trace_id).first()
                    if not trace:
                        continue

                    span = SpanModel(
                        id=item.get("id"),
                        trace_id=trace_id,
                        parent_id=item.get("parent_id"),
                        started_at=datetime.fromisoformat(item.get("started_at", "0")),
                        ended_at=datetime.fromisoformat(item.get("ended_at", "0")),
                        span_type=item.get("span_data").get("type"), # type: ignore
                        span_data=item.get("span_data"),
                        error=item.get("error"),
                    )
                    session.add(span)

            session.commit()

        
