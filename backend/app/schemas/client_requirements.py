"""Pydantic schemas for Client Requirements Management."""
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.infrastructure.database.client_requirements_models import (
    ComplianceStatus,
    RequirementPriority,
    RequirementCategory,
    ActionStatus,
    ActionType,
    EvidenceType,
)


# =============================================================================
# CLIENT SCHEMAS
# =============================================================================

class ClientBase(BaseModel):
    """Base schema for client."""
    name: str = Field(..., max_length=200)
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=30)
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    contract_reference: Optional[str] = Field(None, max_length=100)
    industry_sector: Optional[str] = Field(None, max_length=100)
    criticality: str = Field(default="medium", max_length=20)
    extra_data: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class ClientCreate(ClientBase):
    """Schema for creating a client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=30)
    contract_start: Optional[datetime] = None
    contract_end: Optional[datetime] = None
    contract_reference: Optional[str] = Field(None, max_length=100)
    industry_sector: Optional[str] = Field(None, max_length=100)
    criticality: Optional[str] = Field(None, max_length=20)
    extra_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    """Schema for client response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    requirements_count: int = 0
    compliance_score: Optional[float] = None


class ClientListResponse(BaseModel):
    """Schema for client list response."""
    items: List[ClientResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# REQUIREMENT SCHEMAS
# =============================================================================

class RequirementBase(BaseModel):
    """Base schema for requirement."""
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    category: RequirementCategory = RequirementCategory.SECURITY
    priority: RequirementPriority = RequirementPriority.MEDIUM
    source: Optional[str] = Field(None, max_length=200)
    source_reference: Optional[str] = Field(None, max_length=100)
    framework_mappings: List[Dict[str, Any]] = Field(default_factory=list)
    acceptance_criteria: Optional[str] = None
    evidence_required: List[str] = Field(default_factory=list)
    sla_target: Optional[str] = Field(None, max_length=100)
    review_frequency: Optional[str] = Field(None, max_length=50)
    is_mandatory: bool = True
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class RequirementCreate(RequirementBase):
    """Schema for creating a requirement."""
    client_id: uuid.UUID


class RequirementUpdate(BaseModel):
    """Schema for updating a requirement."""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    category: Optional[RequirementCategory] = None
    priority: Optional[RequirementPriority] = None
    source: Optional[str] = Field(None, max_length=200)
    source_reference: Optional[str] = Field(None, max_length=100)
    framework_mappings: Optional[List[Dict[str, Any]]] = None
    acceptance_criteria: Optional[str] = None
    evidence_required: Optional[List[str]] = None
    sla_target: Optional[str] = Field(None, max_length=100)
    review_frequency: Optional[str] = Field(None, max_length=50)
    is_mandatory: Optional[bool] = None
    is_active: Optional[bool] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class RequirementResponse(RequirementBase):
    """Schema for requirement response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    current_compliance_status: Optional[ComplianceStatus] = None


class RequirementListResponse(BaseModel):
    """Schema for requirement list response."""
    items: List[RequirementResponse]
    total: int
    page: int
    page_size: int


class RequirementImport(BaseModel):
    """Schema for importing requirements from file."""
    requirements: List[RequirementBase]


# =============================================================================
# ASSESSMENT SCHEMAS
# =============================================================================

class AssessmentBase(BaseModel):
    """Base schema for compliance assessment."""
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    scope: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AssessmentCreate(AssessmentBase):
    """Schema for creating an assessment."""
    client_id: uuid.UUID
    requirement_ids: Optional[List[uuid.UUID]] = None  # If None, all active requirements


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    scope: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    status: Optional[str] = None


class AssessmentResponse(AssessmentBase):
    """Schema for assessment response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: uuid.UUID
    assessed_by_id: uuid.UUID
    assessment_date: datetime
    total_requirements: int
    compliant_count: int
    partially_compliant_count: int
    non_compliant_count: int
    not_applicable_count: int
    not_assessed_count: int
    compliance_score: Optional[float] = None
    maturity_level: Optional[str] = None
    status: str
    is_final: bool
    created_at: datetime
    finalized_at: Optional[datetime] = None


class AssessmentSummary(BaseModel):
    """Schema for assessment summary."""
    total_requirements: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_applicable: int
    not_assessed: int
    compliance_score: float
    by_category: Dict[str, Dict[str, int]]
    by_priority: Dict[str, Dict[str, int]]


# =============================================================================
# COMPLIANCE RECORD SCHEMAS
# =============================================================================

class ComplianceRecordBase(BaseModel):
    """Base schema for compliance record."""
    status: ComplianceStatus = ComplianceStatus.NOT_ASSESSED
    compliance_level: Optional[int] = Field(None, ge=0, le=100)
    gap_description: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    evidence_provided: List[Dict[str, Any]] = Field(default_factory=list)


class ComplianceRecordUpdate(BaseModel):
    """Schema for updating compliance record."""
    status: Optional[ComplianceStatus] = None
    compliance_level: Optional[int] = Field(None, ge=0, le=100)
    gap_description: Optional[str] = None
    findings: Optional[str] = None
    recommendations: Optional[str] = None
    evidence_provided: Optional[List[Dict[str, Any]]] = None
    evidence_files: Optional[List[str]] = None


class ComplianceRecordResponse(ComplianceRecordBase):
    """Schema for compliance record response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    requirement_id: uuid.UUID
    assessed_by_id: Optional[uuid.UUID] = None
    previous_status: Optional[str] = None
    evidence_files: List[str] = []
    ai_assessment: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_recommendations: Optional[str] = None
    assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    requirement: Optional[RequirementResponse] = None
    remediation_actions_count: int = 0


class ComplianceRecordWithRequirement(ComplianceRecordResponse):
    """Schema for compliance record with requirement details."""
    requirement: RequirementResponse
    evidence_count: int = 0


# =============================================================================
# REMEDIATION ACTION SCHEMAS
# =============================================================================

class RemediationActionBase(BaseModel):
    """Base schema for remediation action."""
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    action_type: ActionType = ActionType.TECHNICAL
    priority: RequirementPriority = RequirementPriority.MEDIUM
    estimated_effort: Optional[str] = Field(None, max_length=50)
    estimated_cost: Optional[float] = None
    due_date: Optional[datetime] = None
    implementation_steps: List[Dict[str, Any]] = Field(default_factory=list)
    deliverables: List[str] = Field(default_factory=list)


class RemediationActionCreate(RemediationActionBase):
    """Schema for creating remediation action."""
    compliance_record_id: uuid.UUID
    assigned_to_id: Optional[uuid.UUID] = None


class RemediationActionUpdate(BaseModel):
    """Schema for updating remediation action."""
    title: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    action_type: Optional[ActionType] = None
    priority: Optional[RequirementPriority] = None
    status: Optional[ActionStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    estimated_effort: Optional[str] = Field(None, max_length=50)
    estimated_cost: Optional[float] = None
    actual_effort: Optional[str] = Field(None, max_length=50)
    actual_cost: Optional[float] = None
    due_date: Optional[datetime] = None
    implementation_steps: Optional[List[Dict[str, Any]]] = None
    deliverables: Optional[List[str]] = None
    blockers: Optional[str] = None
    notes: Optional[str] = None
    assigned_to_id: Optional[uuid.UUID] = None


class RemediationActionResponse(RemediationActionBase):
    """Schema for remediation action response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    compliance_record_id: uuid.UUID
    created_by_id: uuid.UUID
    assigned_to_id: Optional[uuid.UUID] = None
    status: ActionStatus
    progress_percentage: int
    actual_effort: Optional[str] = None
    actual_cost: Optional[float] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    blockers: Optional[str] = None
    ai_generated: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class RemediationPlanGenerate(BaseModel):
    """Schema for generating AI remediation plan."""
    compliance_record_id: uuid.UUID


class RemediationPlanResponse(BaseModel):
    """Schema for generated remediation plan."""
    compliance_record_id: uuid.UUID
    requirement_code: str
    requirement_title: str
    gap_description: Optional[str] = None
    actions: List[RemediationActionResponse]
    generated_at: datetime


# =============================================================================
# AI ASSESSMENT SCHEMAS
# =============================================================================

class AIAssessmentRequest(BaseModel):
    """Schema for AI-assisted compliance assessment."""
    requirement_id: uuid.UUID
    evidence: Dict[str, Any] = Field(default_factory=dict)


class AIAssessmentResponse(BaseModel):
    """Schema for AI assessment response."""
    status: ComplianceStatus
    compliance_level: Optional[int] = None
    gap_analysis: Optional[str] = None
    recommendations: Optional[str] = None
    confidence: float
    success: bool
    error: Optional[str] = None


# =============================================================================
# DASHBOARD/STATS SCHEMAS
# =============================================================================

class ClientComplianceStats(BaseModel):
    """Schema for client compliance statistics."""
    client_id: uuid.UUID
    client_name: str
    total_requirements: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_assessed: int
    compliance_score: float
    open_actions: int
    overdue_actions: int


class ComplianceTrend(BaseModel):
    """Schema for compliance trend over time."""
    date: datetime
    compliance_score: float
    compliant_count: int
    non_compliant_count: int


class RemediationStats(BaseModel):
    """Schema for remediation statistics."""
    total_actions: int
    planned: int
    in_progress: int
    completed: int
    blocked: int
    cancelled: int
    overdue: int
    completion_rate: float


# =============================================================================
# EVIDENCE SCHEMAS
# =============================================================================

class EvidenceBase(BaseModel):
    """Base schema for evidence."""
    name: str = Field(..., max_length=300)
    description: Optional[str] = None
    evidence_type: EvidenceType = EvidenceType.DOCUMENT
    external_url: Optional[str] = Field(None, max_length=1000)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class EvidenceCreate(EvidenceBase):
    """Schema for creating evidence."""
    compliance_record_id: uuid.UUID


class EvidenceUpdate(BaseModel):
    """Schema for updating evidence."""
    name: Optional[str] = Field(None, max_length=300)
    description: Optional[str] = None
    evidence_type: Optional[EvidenceType] = None
    external_url: Optional[str] = Field(None, max_length=1000)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    tags: Optional[List[str]] = None
    extra_data: Optional[Dict[str, Any]] = None


class EvidenceResponse(EvidenceBase):
    """Schema for evidence response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    compliance_record_id: uuid.UUID
    uploaded_by_id: uuid.UUID
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    is_expired: bool
    is_verified: bool
    verified_by_id: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class EvidenceVerify(BaseModel):
    """Schema for verifying evidence."""
    is_verified: bool
    verification_notes: Optional[str] = None


# =============================================================================
# CLIENT DASHBOARD SCHEMAS
# =============================================================================

class AssessmentTrendPoint(BaseModel):
    """Single point in assessment trend."""
    assessment_id: uuid.UUID
    assessment_name: str
    date: datetime
    compliance_score: float
    compliant_count: int
    partially_compliant_count: int
    non_compliant_count: int
    total_requirements: int


class CategoryScore(BaseModel):
    """Compliance score by category."""
    category: str
    category_label: str
    total: int
    compliant: int
    partially_compliant: int
    non_compliant: int
    not_assessed: int
    score: float


class PriorityScore(BaseModel):
    """Compliance score by priority."""
    priority: str
    priority_label: str
    total: int
    compliant: int
    non_compliant: int
    score: float


class EvidenceStats(BaseModel):
    """Evidence statistics."""
    total_evidence: int
    verified_evidence: int
    pending_verification: int
    expired_evidence: int
    by_type: Dict[str, int]


class ClientDashboard(BaseModel):
    """Complete client dashboard data."""
    client_id: uuid.UUID
    client_name: str
    client_code: str

    # Current stats
    total_requirements: int
    current_compliance_score: float
    previous_compliance_score: Optional[float] = None
    score_change: Optional[float] = None

    # Status counts
    compliant_count: int
    partially_compliant_count: int
    non_compliant_count: int
    not_assessed_count: int
    not_applicable_count: int

    # Actions
    total_actions: int
    open_actions: int
    overdue_actions: int
    completed_actions: int
    action_completion_rate: float

    # Evidence
    evidence_stats: EvidenceStats

    # Trends (historical data)
    assessment_trend: List[AssessmentTrendPoint]

    # Breakdown
    by_category: List[CategoryScore]
    by_priority: List[PriorityScore]

    # Recent activity
    last_assessment_date: Optional[datetime] = None
    next_review_date: Optional[datetime] = None

    # Key metrics
    critical_non_compliant: int
    high_priority_actions: int
    days_since_last_assessment: Optional[int] = None
