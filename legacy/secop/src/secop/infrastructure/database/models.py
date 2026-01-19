"""SQLAlchemy ORM models for SecOp."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Float,
    ForeignKey,
    Enum,
    Table,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column

Base = declarative_base()


# ============================================================================
# Enums
# ============================================================================


class UserRole(PyEnum):
    """User roles for RBAC."""

    VIEWER = "viewer"
    ANALYST = "analyst"
    AUDITOR = "auditor"
    ADMIN = "admin"


class AssetType(PyEnum):
    """Types of assets."""

    SERVER = "server"
    WORKSTATION = "workstation"
    LAPTOP = "laptop"
    NETWORK = "network"
    PRINTER = "printer"
    IOT = "iot"
    MOBILE = "mobile"
    VIRTUAL = "virtual"
    CLOUD = "cloud"
    OTHER = "other"


class AssetStatus(PyEnum):
    """Asset status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"
    UNKNOWN = "unknown"


class Criticality(PyEnum):
    """Asset/vulnerability criticality levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ScanStatus(PyEnum):
    """Scan execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScannerType(PyEnum):
    """Types of scanners."""

    NMAP = "nmap"
    OPENVAS = "openvas"
    NUCLEI = "nuclei"
    CUSTOM = "custom"


class VulnerabilityStatus(PyEnum):
    """Vulnerability remediation status."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"
    FALSE_POSITIVE = "false_positive"


class AuditType(PyEnum):
    """Types of audits."""

    AD = "active_directory"
    GWS = "google_workspace"
    NETWORK = "network"
    SERVER = "server"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class AuditStatus(PyEnum):
    """Audit execution status."""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Association Tables
# ============================================================================

asset_tags = Table(
    "asset_tags",
    Base.metadata,
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


# ============================================================================
# Models
# ============================================================================


class User(Base):
    """User model for authentication and RBAC."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
    scans: Mapped[List["Scan"]] = relationship("Scan", back_populates="created_by_user")
    audits: Mapped[List["Audit"]] = relationship("Audit", back_populates="created_by_user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role={self.role.value})>"


class UserSession(Base):
    """User session for authentication."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id})>"


class AuditLog(Base):
    """Audit trail for all actions."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="audit_logs")

    __table_args__ = (Index("ix_audit_logs_timestamp_action", "timestamp", "action"),)

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', resource={self.resource_type})>"


class Tag(Base):
    """Tags for categorizing assets."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6c757d")

    # Relationships
    assets: Mapped[List["Asset"]] = relationship(
        "Asset", secondary=asset_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name='{self.name}')>"


class Asset(Base):
    """IT asset model."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType), default=AssetType.OTHER)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True, index=True)
    mac_address: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    hostname: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    fqdn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    os: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    os_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    manufacturer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    owner: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    criticality: Mapped[Criticality] = mapped_column(Enum(Criticality), default=Criticality.MEDIUM)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    tags: Mapped[List["Tag"]] = relationship("Tag", secondary=asset_tags, back_populates="assets")
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="asset", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_assets_type_status", "asset_type", "status"),)

    def __repr__(self) -> str:
        return f"<Asset(id={self.id}, name='{self.name}', type={self.asset_type.value})>"


class Scan(Base):
    """Vulnerability scan model."""

    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scanner_type: Mapped[ScannerType] = mapped_column(Enum(ScannerType), nullable=False)
    targets: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ScanStatus] = mapped_column(Enum(ScanStatus), default=ScanStatus.PENDING)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    created_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="scans")
    vulnerabilities: Mapped[List["Vulnerability"]] = relationship(
        "Vulnerability", back_populates="scan", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_scans_status_created", "status", "created_at"),)

    def __repr__(self) -> str:
        return f"<Scan(id={self.id}, name='{self.name}', status={self.status.value})>"


class Vulnerability(Base):
    """Vulnerability finding model."""

    __tablename__ = "vulnerabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("assets.id", ondelete="CASCADE"), nullable=True
    )
    scan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("scans.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Criticality] = mapped_column(Enum(Criticality), default=Criticality.MEDIUM)
    cvss_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cve_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    cwe_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    affected_component: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    solution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[VulnerabilityStatus] = mapped_column(
        Enum(VulnerabilityStatus), default=VulnerabilityStatus.OPEN
    )
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    asset: Mapped[Optional["Asset"]] = relationship("Asset", back_populates="vulnerabilities")
    scan: Mapped[Optional["Scan"]] = relationship("Scan", back_populates="vulnerabilities")

    __table_args__ = (
        Index("ix_vulns_severity_status", "severity", "status"),
        Index("ix_vulns_asset_severity", "asset_id", "severity"),
    )

    def __repr__(self) -> str:
        return f"<Vulnerability(id={self.id}, name='{self.name}', severity={self.severity.value})>"


class Audit(Base):
    """Audit session model."""

    __tablename__ = "audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    audit_type: Mapped[AuditType] = mapped_column(Enum(AuditType), nullable=False)
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AuditStatus] = mapped_column(Enum(AuditStatus), default=AuditStatus.SCHEDULED)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    created_by_user: Mapped[Optional["User"]] = relationship("User", back_populates="audits")
    findings: Mapped[List["AuditFinding"]] = relationship(
        "AuditFinding", back_populates="audit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Audit(id={self.id}, name='{self.name}', type={self.audit_type.value})>"


class AuditFinding(Base):
    """Audit finding model."""

    __tablename__ = "audit_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    audit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("audits.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[Criticality] = mapped_column(Enum(Criticality), default=Criticality.MEDIUM)
    affected_item: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    audit: Mapped["Audit"] = relationship("Audit", back_populates="findings")

    def __repr__(self) -> str:
        return f"<AuditFinding(id={self.id}, title='{self.title}')>"


# ============================================================================
# Configuration for LDAP/Google Workspace
# ============================================================================


class DirectoryConfig(Base):
    """Directory service configuration storage."""

    __tablename__ = "directory_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    config_type: Mapped[str] = mapped_column(String(20), nullable=False)
    config_data: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<DirectoryConfig(id={self.id}, name='{self.name}', type={self.config_type})>"
