"""SQLAlchemy models for GRC Platform (unified from SecOP + GRC-Agent)."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base
from app.core.permissions import UserRole


# =============================================================================
# ENUMS
# =============================================================================

class AssetType(str, PyEnum):
    SERVER = "server"
    WORKSTATION = "workstation"
    NETWORK = "network"
    CLOUD_INSTANCE = "cloud_instance"
    CONTAINER = "container"
    DATABASE = "database"
    APPLICATION = "application"
    IOT = "iot"
    OTHER = "other"


class AssetStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class Severity(str, PyEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class ScanStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(str, PyEnum):
    DISCOVERY = "discovery"
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"
    FULL = "full"


# =============================================================================
# MODELS
# =============================================================================

class User(Base):
    """User model with authentication and RBAC."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Security
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="created_by")

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email


class Asset(Base):
    """Asset inventory model (servers, workstations, network devices, etc.)."""
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False)
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus), default=AssetStatus.ACTIVE
    )
    criticality: Mapped[Severity] = mapped_column(
        Enum(Severity), default=Severity.MEDIUM
    )

    # Network info (from GRC-Agent HostInfo)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), index=True, nullable=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fqdn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # System info
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Organization
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Flexible data
    services: Mapped[dict] = mapped_column(JSONB, default=list)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_assets_type_status", "asset_type", "status"),
    )


class Vulnerability(Base):
    """Vulnerability/Finding model (unified from SecOP + GRC-Agent)."""
    __tablename__ = "vulnerabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    scan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scans.id", ondelete="SET NULL"), nullable=True
    )

    # Identification
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="general")
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    status: Mapped[VulnStatus] = mapped_column(
        Enum(VulnStatus), default=VulnStatus.OPEN
    )

    # CVSS (from GRC-Agent)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cvss_vector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cve_ids: Mapped[List[str]] = mapped_column(JSONB, default=list)
    cwe_ids: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Context
    affected_component: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    port: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    service: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    protocol: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Remediation
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_effort: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    references: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Assignment
    assignee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # AI enrichment
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    discovered_by: Mapped[str] = mapped_column(String(50), default="manual")
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="vulnerabilities")
    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="vulnerabilities")
    assignee: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_vulns_severity_status", "severity", "status"),
        Index("idx_vulns_asset_id", "asset_id"),
    )


class Scan(Base):
    """Scan/Audit campaign model (from GRC-Agent)."""
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # General
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scan_type: Mapped[ScanType] = mapped_column(Enum(ScanType), nullable=False)
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), default=ScanStatus.PENDING
    )
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # Targets
    targets: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Configuration
    config: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Results (from GRC-Agent AuditScore)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    risk_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    findings_summary: Mapped[dict] = mapped_column(
        JSONB,
        default={"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    )

    # Phases
    current_phase: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    phases_completed: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Timing
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Errors
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    errors: Mapped[List[str]] = mapped_column(JSONB, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    created_by: Mapped["User"] = relationship("User", back_populates="scans")
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="scan"
    )

    __table_args__ = (
        Index("idx_scans_status_created", "status", "created_at"),
    )


class AuditLog(Base):
    """Audit trail for all actions."""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index("idx_audit_logs_timestamp", "timestamp"),
    )
