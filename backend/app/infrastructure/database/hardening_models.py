"""SQLAlchemy models for the HCO Hardening module."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class HardeningSessionStatus(str, PyEnum):
    PENDING = "pending"
    CONNECTING = "connecting"
    AUDITING = "auditing"
    COMPLETED = "completed"
    FAILED = "failed"


class HardeningTarget(Base):
    __tablename__ = "hardening_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22)
    username: Mapped[str] = mapped_column(String(100), default="root")
    os_type: Mapped[str] = mapped_column(String(30), default="linux")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credentials: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    sessions = relationship(
        "HardeningSession", back_populates="target", cascade="all, delete-orphan"
    )


class HardeningSession(Base):
    __tablename__ = "hardening_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hardening_targets.id"), nullable=False
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(String(30), default=HardeningSessionStatus.PENDING)
    current_module: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    modules_requested: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    modules_completed: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    findings_summary: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    total_findings: Mapped[int] = mapped_column(Integer, default=0)
    total_checks: Mapped[int] = mapped_column(Integer, default=0)
    passed_checks: Mapped[int] = mapped_column(Integer, default=0)

    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    target = relationship("HardeningTarget", back_populates="sessions")
    findings = relationship(
        "HardeningFinding", back_populates="session", cascade="all, delete-orphan"
    )


class HardeningFinding(Base):
    __tablename__ = "hardening_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("hardening_sessions.id"), nullable=False
    )

    check_id: Mapped[str] = mapped_column(String(20), nullable=False)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False)
    found: Mapped[str] = mapped_column(Text, nullable=False)
    expected: Mapped[str] = mapped_column(Text, nullable=False)
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(10), default="FAIL")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session = relationship("HardeningSession", back_populates="findings")
