from __future__ import annotations

from datetime import datetime
from typing import List

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Backend(Base):
    __tablename__ = "backends"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    url: Mapped[str] = mapped_column(String)
    api_key: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[str] = mapped_column(String)


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


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    folder_name: Mapped[str] = mapped_column(String, unique=True)
    original_filename: Mapped[str] = mapped_column(String)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    mime_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class ModelConfig(Base):
    __tablename__ = "model_configs"

    role: Mapped[str] = mapped_column(String, primary_key=True)
    backend_id: Mapped[int] = mapped_column(ForeignKey("backends.id"), nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False) 
