"""SQLAlchemy models for SMSI Generator module."""
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


# =============================================================================
# ENUMS
# =============================================================================

class ComplianceFramework(str, PyEnum):
    """Supported compliance frameworks."""
    ISO_27001 = "iso_27001"
    ISO_27002 = "iso_27002"
    DORA = "dora"
    NIS2 = "nis2"
    RGPD = "rgpd"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    NIST_CSF = "nist_csf"
    CIS_CONTROLS = "cis_controls"
    EU_AI_ACT = "eu_ai_act"
    ENISA = "enisa"
    ANSSI_HDS = "anssi_hds"
    SECNUMCLOUD = "secnumcloud"


class DocumentType(str, PyEnum):
    """Types of SMSI documents."""
    POLICY = "policy"
    PROCEDURE = "procedure"
    REGISTER = "register"
    ANNEX = "annex"
    SCHEMA = "schema"
    TEMPLATE = "template"
    CHECKLIST = "checklist"
    REPORT = "report"
    MATRIX = "matrix"


class DocumentStatus(str, PyEnum):
    """Document generation status."""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class QuestionType(str, PyEnum):
    """QCM question types."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    YES_NO = "yes_no"
    SCALE = "scale"
    MATRIX = "matrix"


class ProjectStatus(str, PyEnum):
    """SMSI project status."""
    CREATED = "created"
    ASSESSMENT = "assessment"
    GENERATION = "generation"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SecurityLevel(str, PyEnum):
    """Security classification levels."""
    N1_STANDARD = "n1_standard"
    N2_REINFORCED = "n2_reinforced"
    N3_CRITICAL = "n3_critical"


# =============================================================================
# MODELS - COMPLIANCE FRAMEWORKS
# =============================================================================

class Framework(Base):
    """Compliance framework definition."""
    __tablename__ = "smsi_frameworks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Framework metadata
    category: Mapped[str] = mapped_column(String(50), default="general")
    region: Mapped[str] = mapped_column(String(50), default="eu")
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    effective_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Structure
    total_controls: Mapped[int] = mapped_column(Integer, default=0)
    total_requirements: Mapped[int] = mapped_column(Integer, default=0)

    # Icon and color for UI
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    controls: Mapped[List["FrameworkControl"]] = relationship(
        "FrameworkControl", back_populates="framework", cascade="all, delete-orphan"
    )
    documents: Mapped[List["DocumentTemplate"]] = relationship(
        "DocumentTemplate", back_populates="framework"
    )


class FrameworkControl(Base):
    """Individual control/requirement within a framework."""
    __tablename__ = "smsi_framework_controls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_frameworks.id", ondelete="CASCADE")
    )

    # Control identification
    control_id: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Hierarchy
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_framework_controls.id"), nullable=True
    )
    domain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subdomain: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    # Attributes
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    security_level: Mapped[Optional[SecurityLevel]] = mapped_column(
        Enum(SecurityLevel), nullable=True
    )

    # Implementation guidance
    implementation_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_required: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Mapping to other frameworks
    mappings: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    framework: Mapped["Framework"] = relationship("Framework", back_populates="controls")
    parent: Mapped[Optional["FrameworkControl"]] = relationship(
        "FrameworkControl", remote_side=[id], backref="children"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="control"
    )

    __table_args__ = (
        Index("idx_controls_framework", "framework_id"),
        Index("idx_controls_control_id", "control_id"),
    )


# =============================================================================
# MODELS - DOCUMENT TEMPLATES
# =============================================================================

class DocumentTemplate(Base):
    """Template for SMSI document generation."""
    __tablename__ = "smsi_document_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    framework_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_frameworks.id"), nullable=True
    )

    # Document identification
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template structure
    sections: Mapped[List[dict]] = mapped_column(JSONB, default=list)
    variables: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # AI generation config
    ai_prompt_template: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_context: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Supported output formats
    output_formats: Mapped[List[str]] = mapped_column(
        JSONB, default=["docx", "pdf", "md", "html"]
    )

    # Security level requirements
    min_security_level: Mapped[SecurityLevel] = mapped_column(
        Enum(SecurityLevel), default=SecurityLevel.N1_STANDARD
    )

    # Metadata
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    framework: Mapped[Optional["Framework"]] = relationship(
        "Framework", back_populates="documents"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question", back_populates="template", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_templates_type", "document_type"),
        Index("idx_templates_framework", "framework_id"),
    )


# =============================================================================
# MODELS - QCM / QUESTIONNAIRE
# =============================================================================

class Question(Base):
    """Question for document generation QCM."""
    __tablename__ = "smsi_questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_document_templates.id", ondelete="CASCADE")
    )
    control_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_framework_controls.id"), nullable=True
    )

    # Question content
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), nullable=False)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    placeholder: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # For choice questions
    options: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # Validation
    is_required: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    min_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_value: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Conditional logic
    depends_on: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_questions.id"), nullable=True
    )
    condition: Mapped[dict] = mapped_column(JSONB, default=dict)

    # AI generation mapping
    variable_name: Mapped[str] = mapped_column(String(100), nullable=False)
    section_target: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Display
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    group_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    template: Mapped["DocumentTemplate"] = relationship(
        "DocumentTemplate", back_populates="questions"
    )
    control: Mapped[Optional["FrameworkControl"]] = relationship(
        "FrameworkControl", back_populates="questions"
    )

    __table_args__ = (
        Index("idx_questions_template", "template_id"),
        Index("idx_questions_order", "template_id", "order_index"),
    )


# =============================================================================
# MODELS - SMSI PROJECT
# =============================================================================

class SMSIProject(Base):
    """SMSI generation project for an organization."""
    __tablename__ = "smsi_projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Project identification
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus), default=ProjectStatus.CREATED
    )

    # Organization context
    organization_name: Mapped[str] = mapped_column(String(200), nullable=False)
    organization_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organization_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    industry_sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Scope
    selected_frameworks: Mapped[List[str]] = mapped_column(JSONB, default=list)
    security_level: Mapped[SecurityLevel] = mapped_column(
        Enum(SecurityLevel), default=SecurityLevel.N1_STANDARD
    )

    # Context data (from QCM)
    context_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Progress tracking
    completion_percentage: Mapped[int] = mapped_column(Integer, default=0)
    documents_generated: Mapped[int] = mapped_column(Integer, default=0)
    documents_total: Mapped[int] = mapped_column(Integer, default=0)

    # AI generation stats
    ai_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    ai_generation_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Storage
    storage_bucket: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    created_by: Mapped["User"] = relationship("User")
    responses: Mapped[List["QuestionResponse"]] = relationship(
        "QuestionResponse", back_populates="project", cascade="all, delete-orphan"
    )
    documents: Mapped[List["GeneratedDocument"]] = relationship(
        "GeneratedDocument", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_projects_status", "status"),
        Index("idx_projects_created_by", "created_by_id"),
    )


class QuestionResponse(Base):
    """User response to a question in a project."""
    __tablename__ = "smsi_question_responses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_projects.id", ondelete="CASCADE")
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_questions.id", ondelete="CASCADE")
    )

    # Response data
    response_value: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Validation
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_errors: Mapped[List[str]] = mapped_column(JSONB, default=list)

    # AI-assisted input
    ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    project: Mapped["SMSIProject"] = relationship(
        "SMSIProject", back_populates="responses"
    )
    question: Mapped["Question"] = relationship("Question")

    __table_args__ = (
        Index("idx_responses_project", "project_id"),
        Index("idx_responses_question", "question_id"),
    )


# =============================================================================
# MODELS - GENERATED DOCUMENTS
# =============================================================================

class GeneratedDocument(Base):
    """Generated SMSI document."""
    __tablename__ = "smsi_generated_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_projects.id", ondelete="CASCADE")
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_document_templates.id")
    )

    # Document identification
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Status
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus), default=DocumentStatus.DRAFT
    )

    # Content
    content_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Generated files (stored in MinIO)
    files: Mapped[List[dict]] = mapped_column(JSONB, default=list)

    # AI generation metadata
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ai_prompt_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_tokens_input: Mapped[int] = mapped_column(Integer, default=0)
    ai_tokens_output: Mapped[int] = mapped_column(Integer, default=0)
    ai_generation_time: Mapped[float] = mapped_column(Float, default=0.0)

    # Review
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Current owner/editor
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Lock for concurrent editing
    locked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Last validated versions (for quick rollback)
    last_validated_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    second_last_validated_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Current version number
    current_version_number: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    project: Mapped["SMSIProject"] = relationship(
        "SMSIProject", back_populates="documents"
    )
    template: Mapped[Optional["DocumentTemplate"]] = relationship("DocumentTemplate")
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
    owner: Mapped[Optional["User"]] = relationship("User", foreign_keys=[owner_id])
    locked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[locked_by_id])
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document", cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()"
    )
    comments: Mapped[List["DocumentComment"]] = relationship(
        "DocumentComment", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_documents_project", "project_id"),
        Index("idx_documents_status", "status"),
    )


# =============================================================================
# MODELS - DOCUMENT VERSIONS (AUDIT TRAIL)
# =============================================================================

class DocumentVersion(Base):
    """Version history for document changes - enables rollback and audit trail."""
    __tablename__ = "smsi_document_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_generated_documents.id", ondelete="CASCADE")
    )

    # Version info
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_label: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "1.0", "1.1"

    # Content snapshot
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    content_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Change metadata
    change_summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    change_type: Mapped[str] = mapped_column(String(50), default="edit")  # edit, review, approval, rollback

    # Who made the change
    modified_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Validation status
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    validated_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    document: Mapped["GeneratedDocument"] = relationship(
        "GeneratedDocument", back_populates="versions"
    )
    modified_by: Mapped["User"] = relationship("User", foreign_keys=[modified_by_id])
    validated_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[validated_by_id])

    __table_args__ = (
        Index("idx_versions_document", "document_id"),
        Index("idx_versions_number", "document_id", "version_number"),
    )


class DocumentComment(Base):
    """Comments and annotations on documents."""
    __tablename__ = "smsi_document_comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_generated_documents.id", ondelete="CASCADE")
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("smsi_document_versions.id"), nullable=True
    )

    # Comment content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    comment_type: Mapped[str] = mapped_column(String(50), default="general")  # general, review, suggestion, issue

    # Position in document (for inline comments)
    section_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    line_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Author
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Resolution status
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, onupdate=datetime.utcnow, nullable=True
    )

    # Relationships
    document: Mapped["GeneratedDocument"] = relationship(
        "GeneratedDocument", back_populates="comments"
    )
    author: Mapped["User"] = relationship("User", foreign_keys=[author_id])
    resolved_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[resolved_by_id])

    __table_args__ = (
        Index("idx_comments_document", "document_id"),
    )


# Import User for relationships
from app.infrastructure.database.models import User
