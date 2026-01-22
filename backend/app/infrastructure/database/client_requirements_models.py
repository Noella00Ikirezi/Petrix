"""SQLAlchemy models for Client Requirements Management."""
import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Boolean,
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


# =============================================================================
# ENUMS
# =============================================================================

class ComplianceStatus(str, PyEnum):
    """Compliance status for requirements."""
    NOT_ASSESSED = "not_assessed"
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    NOT_APPLICABLE = "not_applicable"


class RequirementPriority(str, PyEnum):
    """Priority levels for requirements."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RequirementCategory(str, PyEnum):
    """Categories of client requirements."""
    SECURITY = "security"
    PRIVACY = "privacy"
    AVAILABILITY = "availability"
    INTEGRITY = "integrity"
    AUDIT = "audit"
    REPORTING = "reporting"
    SLA = "sla"
    CONTRACTUAL = "contractual"
    REGULATORY = "regulatory"
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"


class ActionStatus(str, PyEnum):
    """Status of remediation actions."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ActionType(str, PyEnum):
    """Types of remediation actions."""
    TECHNICAL = "technical"
    ORGANIZATIONAL = "organizational"
    DOCUMENTATION = "documentation"
    TRAINING = "training"
    PROCESS = "process"
    TOOL = "tool"
    AUDIT = "audit"


# =============================================================================
# MODELS - CLIENT
# =============================================================================

class Client(Base):
    """Client/Customer entity."""
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Contact info
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Contract info
    contract_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    contract_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    contract_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Classification
    industry_sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    criticality: Mapped[str] = mapped_column(String(20), default="medium")

    # Custom fields
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    requirements: Mapped[List["ClientRequirement"]] = relationship(
        "ClientRequirement", back_populates="client", cascade="all, delete-orphan"
    )
    assessments: Mapped[List["ComplianceAssessment"]] = relationship(
        "ComplianceAssessment", back_populates="client", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_clients_code", "code"),
        Index("idx_clients_active", "is_active"),
    )


# =============================================================================
# MODELS - REQUIREMENTS
# =============================================================================

class ClientRequirement(Base):
    """Client-specific security/compliance requirement."""
    __tablename__ = "client_requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE")
    )

    # Identification
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Classification
    category: Mapped[RequirementCategory] = mapped_column(
        Enum(RequirementCategory), default=RequirementCategory.SECURITY
    )
    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(RequirementPriority), default=RequirementPriority.MEDIUM
    )

    # Source
    source: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Mapping to frameworks
    framework_mappings: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Acceptance criteria
    acceptance_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_required: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # SLA
    sla_target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    review_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="requirements")
    compliance_records: Mapped[List["RequirementCompliance"]] = relationship(
        "RequirementCompliance", back_populates="requirement", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_requirements_client", "client_id"),
        Index("idx_requirements_category", "category"),
        Index("idx_requirements_priority", "priority"),
    )


# =============================================================================
# MODELS - COMPLIANCE ASSESSMENT
# =============================================================================

class ComplianceAssessment(Base):
    """Compliance assessment campaign for a client."""
    __tablename__ = "compliance_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE")
    )
    assessed_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # Identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assessment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Scope
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Results summary
    total_requirements: Mapped[int] = mapped_column(Integer, default=0)
    compliant_count: Mapped[int] = mapped_column(Integer, default=0)
    partially_compliant_count: Mapped[int] = mapped_column(Integer, default=0)
    non_compliant_count: Mapped[int] = mapped_column(Integer, default=0)
    not_applicable_count: Mapped[int] = mapped_column(Integer, default=0)
    not_assessed_count: Mapped[int] = mapped_column(Integer, default=0)

    # Score
    compliance_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maturity_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finalized_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="assessments")
    assessed_by: Mapped["User"] = relationship("User")
    compliance_records: Mapped[List["RequirementCompliance"]] = relationship(
        "RequirementCompliance", back_populates="assessment", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_assessments_client", "client_id"),
        Index("idx_assessments_date", "assessment_date"),
    )


class RequirementCompliance(Base):
    """Compliance status for a specific requirement in an assessment."""
    __tablename__ = "requirement_compliance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("compliance_assessments.id", ondelete="CASCADE")
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_requirements.id", ondelete="CASCADE")
    )
    assessed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Status
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus), default=ComplianceStatus.NOT_ASSESSED
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # Assessment details
    compliance_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0-100
    gap_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    findings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Evidence
    evidence_provided: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    evidence_files: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # AI-assisted assessment
    ai_assessment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    assessment: Mapped["ComplianceAssessment"] = relationship(
        "ComplianceAssessment", back_populates="compliance_records"
    )
    requirement: Mapped["ClientRequirement"] = relationship(
        "ClientRequirement", back_populates="compliance_records"
    )
    assessed_by: Mapped[Optional["User"]] = relationship("User")
    remediation_actions: Mapped[List["RemediationAction"]] = relationship(
        "RemediationAction", back_populates="compliance_record", cascade="all, delete-orphan"
    )
    evidence: Mapped[List["Evidence"]] = relationship(
        "Evidence", back_populates="compliance_record", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_compliance_assessment", "assessment_id"),
        Index("idx_compliance_requirement", "requirement_id"),
        Index("idx_compliance_status", "status"),
    )


# =============================================================================
# MODELS - REMEDIATION ACTIONS
# =============================================================================

class RemediationAction(Base):
    """Remediation action for non-compliant requirements."""
    __tablename__ = "remediation_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    compliance_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirement_compliance.id", ondelete="CASCADE")
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Action details
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_type: Mapped[ActionType] = mapped_column(
        Enum(ActionType), default=ActionType.TECHNICAL
    )
    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(RequirementPriority), default=RequirementPriority.MEDIUM
    )

    # Status tracking
    status: Mapped[ActionStatus] = mapped_column(
        Enum(ActionStatus), default=ActionStatus.PLANNED
    )
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)

    # Effort estimation
    estimated_effort: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_effort: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dates
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Implementation details
    implementation_steps: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    deliverables: Mapped[List[str]] = mapped_column(JSONB, default=list)
    blockers: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI-generated
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    compliance_record: Mapped["RequirementCompliance"] = relationship(
        "RequirementCompliance", back_populates="remediation_actions"
    )
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    assigned_to: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_to_id])

    __table_args__ = (
        Index("idx_actions_compliance", "compliance_record_id"),
        Index("idx_actions_status", "status"),
        Index("idx_actions_due_date", "due_date"),
    )


# =============================================================================
# MODELS - EVIDENCE
# =============================================================================

class EvidenceType(str, PyEnum):
    """Types of evidence."""
    DOCUMENT = "document"
    SCREENSHOT = "screenshot"
    LOG = "log"
    CONFIG = "config"
    REPORT = "report"
    CERTIFICATE = "certificate"
    POLICY = "policy"
    PROCEDURE = "procedure"
    ATTESTATION = "attestation"
    OTHER = "other"


class Evidence(Base):
    """Evidence/Proof for compliance records."""
    __tablename__ = "compliance_evidence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    compliance_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("requirement_compliance.id", ondelete="CASCADE")
    )
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )

    # Evidence details
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType), default=EvidenceType.DOCUMENT
    )

    # File info
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    minio_bucket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    minio_object_key: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # External link (alternative to file)
    external_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    # Validity
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    compliance_record: Mapped["RequirementCompliance"] = relationship(
        "RequirementCompliance", back_populates="evidence"
    )
    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[uploaded_by_id])
    verified_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[verified_by_id])

    __table_args__ = (
        Index("idx_evidence_compliance", "compliance_record_id"),
        Index("idx_evidence_type", "evidence_type"),
        Index("idx_evidence_verified", "is_verified"),
    )


# Import User for relationships
from app.infrastructure.database.models import User
