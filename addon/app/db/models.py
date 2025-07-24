from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import JSON, DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    backend: Mapped[str] = mapped_column(String)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class Trace(Base):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(
        String, primary_key=True
    )
    workflow_name: Mapped[str | None] = mapped_column(String, nullable=True)
    group_id: Mapped[str | None] = mapped_column(String, nullable=True)
    spans: Mapped[List[Span]] = relationship("Span", back_populates="trace")


class Span(Base):
    __tablename__ = "spans"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    trace_id: Mapped[str] = mapped_column(ForeignKey("traces.id"), index=True)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("spans.id"), index=True, nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ended_at: Mapped[datetime] = mapped_column(DateTime)

    span_type: Mapped[str] = mapped_column(String)
    span_data: Mapped[dict] = mapped_column(JSON)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trace: Mapped[Trace] = relationship("Trace", back_populates="spans")
    parent: Mapped[Span | None] = relationship(
        "Span", remote_side=[id], back_populates="children"
    )
    children: Mapped[List[Span]] = relationship("Span", back_populates="parent") 